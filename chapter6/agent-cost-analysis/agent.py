"""
一个多轮「客服退款 Agent」任务，用于成本分析（对应书 6.x 表6-4 的客服退款示例）。

为了让实验可复现、不依赖模型工具调用的随机性，这里用「受控工具环境」：
每一轮我们把上一步工具的返回结果喂给模型，由模型（真实 LLM 调用）决定下一步怎么做。
工具返回内容是预设好的（真实 API 里会是订单系统/物流系统的返回），
但每一次 LLM 调用、每一份 token 用量、每一分成本都是真实的。

本文件提供两种上下文构造策略，用于 A/B：
  (a) run_naive     —— 朴素做法：前缀不稳定 + 不压缩历史（KV-cache 命中不了，上下文疯长）
  (b) run_optimized —— KV-cache 友好 + 上下文压缩：稳定长前缀（复用 cached_tokens）+ 旧轮次摘要
"""

import uuid

from config import MODEL
from tracer import Tracer

# 限制每轮输出长度：本实验聚焦「输入侧」的 KV-cache 与压缩两个杠杆，
# 把输出 token 控制在相近水平，可避免模型生成长度的随机波动干扰 A/B 成本对比。
MAX_OUTPUT_TOKENS = 160

# ---------------------------------------------------------------------------
# 一个「足够长且稳定」的系统提示 + 工具定义（> 1024 token），
# 这是 KV-cache 命中的关键：稳定的长前缀才会被 OpenAI 自动缓存。
# 内容是一个真实感的客服退款 Agent 的系统规范与工具手册。
# ---------------------------------------------------------------------------
STABLE_SYSTEM_PROMPT = """你是「云购商城」的高级客服 Agent，专门处理售后与退款事务。你必须严格遵循以下工作规范。

# 角色与目标
你的目标是在保障平台规则的前提下，高效、礼貌地帮助用户完成退款、退货、换货、物流查询等售后诉求。
你要主动澄清诉求、核对订单状态、判断是否符合退款政策，并在权限范围内执行操作。

# 可用工具手册（tool manual）
1. query_order(order_id): 查询订单详情。返回字段包括：order_id, status, item_name, sku, price,
   quantity, pay_time, pay_channel, buyer_note, seller_note, is_prepaid, warehouse, promotion_tags。
2. query_logistics(order_id): 查询物流轨迹。返回字段：carrier, tracking_no, current_status,
   last_scan_time, last_scan_location, estimated_delivery, full_trace(数组，含每个扫描节点)。
3. check_refund_policy(sku, reason): 查询该 SKU 在给定退款原因下的退款政策。返回字段：
   refundable, need_return, restocking_fee_rate, refund_window_days, special_notes, approval_required。
4. query_user_history(user_id): 查询用户历史行为，用于风控。返回：total_orders, refund_count_90d,
   dispute_count, risk_level, vip_tier, register_days。
5. issue_refund(order_id, amount, reason): 发起退款。返回：refund_id, status, expected_arrival,
   channel, operator。仅当政策允许且金额不超过订单实付金额时才可调用。
6. send_notification(user_id, channel, template, params): 给用户发通知（sms/app/email）。

# 决策规范
- 先核对订单是否存在、状态是否允许退款（已发货未签收、已签收 7 天内、未发货均有不同处理路径）。
- 未发货：可直接全额退款，无需退货。
- 已发货未签收：需拦截物流或等待退回，退款在退货签收后发起。
- 已签收 7 天内且商品无质量问题：适用 7 天无理由，可能收取一定比例的手续费（restocking_fee_rate）。
- 商品质量问题：全额退款且不收手续费，需用户提供凭证。
- 涉及大额退款（> 500 元）或高风险用户（risk_level=high）需要人工审批（approval_required=true）。
- 每一步都要给出简短的中文推理，说明你「基于什么信息、决定下一步调用哪个工具或给出什么结论」。

# 输出要求
- 保持专业、简洁、有同理心。
- 每轮只推进一步，不要臆造工具尚未返回的数据。
- 最终解决时，明确告知用户退款金额、到账时间与后续动作。

# 合规与风控
- 不得泄露其它用户信息；不得承诺超出政策的赔付；金额与政策以工具返回为准。
- 对疑似欺诈（短期高频退款、异常物流轨迹）要保持谨慎并触发人工审批。
请始终遵守以上全部规范。"""


# ---------------------------------------------------------------------------
# 预设的多轮剧本：用户诉求 + 每一步工具返回（真实 API 里来自后端系统）。
# 工具返回故意写得比较「啰嗦」（大 JSON），以体现工具结果注入上下文的 token 成本。
# ---------------------------------------------------------------------------
USER_REQUEST = (
    "你好，我上周买的蓝牙耳机（订单号 ORD20240517001）到货后一直连不上，"
    "试了各种办法都没用，我想退货退款，怎么处理？"
)

# 每一轮：(逻辑步骤名, 关联工具, 该工具的"啰嗦"返回文本)
# 工具返回都写得比较大（真实的订单/物流/知识库返回往往几百到上千 token），
# 以体现「工具结果注入上下文后在后续每一轮被反复计费」这一放大因素。
_LOGISTICS_TRACE = ",".join(
    '{"time":"2024-05-%02dT%02d:%02d","loc":"%s","desc":"%s","operator":"SF%04d","scan_type":"auto"}'
    % (17 + i // 6, 6 + i, (i * 7) % 60, loc, desc, 1000 + i)
    for i, (loc, desc) in enumerate([
        ("华东1仓", "包裹已揽收，称重0.42kg"), ("华东1仓分拣中心", "已分拣，发往上海转运"),
        ("上海转运中心", "到达转运中心"), ("上海转运中心", "已发出，运输中"),
        ("苏州中转场", "途经中转"), ("上海浦东集散点", "到达派送网点"),
        ("上海浦东集散点", "安排派送"), ("浦东xx营业点", "派送中，联系收件人"),
        ("浦东xx营业点", "首次派送未接通"), ("浦东xx营业点", "二次派送"),
        ("浦东xx营业点", "已签收，签收人：本人"),
    ])
)

TOOL_RESULTS = [
    ("turn-1", "query_order",
     '{"order_id":"ORD20240517001","status":"SIGNED","item_name":"Acme 主动降噪蓝牙耳机 Pro",'
     '"sku":"SKU-BT-9981","price":499.00,"quantity":1,"pay_time":"2024-05-17T10:22:31",'
     '"pay_channel":"wechat_pay","buyer_note":"希望尽快发货，送人用","seller_note":"已核对库存",'
     '"is_prepaid":true,"warehouse":"华东1仓","promotion_tags":["满300减30","会员日","新客礼"],'
     '"actual_paid":469.00,"coupon_used":"CPN-30","points_earned":469,"invoice_requested":false,'
     '"sign_time":"2024-05-19T14:03:11","after_sale_window_end":"2024-05-26T23:59:59",'
     '"sub_items":[{"sku":"SKU-BT-9981","name":"耳机主体","qty":1},{"sku":"SKU-BT-9981-CASE","name":"充电盒","qty":1},{"sku":"SKU-BT-9981-TIP","name":"耳塞套装","qty":1}],'
     '"address_hash":"a1b2c3d4","channel":"app","device":"iOS","order_source":"首页推荐位"}'),
    ("turn-2", "query_logistics",
     '{"carrier":"顺丰速运","tracking_no":"SF1234567890123","current_status":"已签收",'
     '"last_scan_time":"2024-05-19T14:03:11","last_scan_location":"上海市浦东新区xx营业点",'
     '"estimated_delivery":"2024-05-19","weight_kg":0.42,"volume":"20x15x8cm","insured":true,'
     '"full_trace":[' + _LOGISTICS_TRACE + ']}'),
    ("turn-3", "check_refund_policy",
     '{"sku":"SKU-BT-9981","reason":"quality_issue_cannot_connect","refundable":true,'
     '"need_return":true,"restocking_fee_rate":0.0,"refund_window_days":7,'
     '"special_notes":"质量问题类退款免手续费；需用户回寄并由质检确认是否为质量问题；'
     '若质检判定非质量问题（如人为损坏、私自拆修），将按原路退回商品且不予退款；'
     '回寄运费由平台承担，用户需在系统中申请电子面单；退款在质检通过后 1 个工作日内发起；'
     '3C 电子类目已激活/绑定账号的商品，需先解绑再回寄，否则质检不予通过。",'
     '"approval_required":false,"category":"3C-电子","quality_claim_supported":true,'
     '"return_label_provided":true,"qc_sla_days":2,"related_policy_ids":["P-3C-01","P-3C-07","P-QC-12"]}'),
    ("turn-4", "query_knowledge_base",
     '{"query":"蓝牙耳机无法连接 排查","hits":['
     '{"kb_id":"KB-1001","title":"蓝牙耳机无法连接的常见原因","content":"1.未进入配对模式；'
     '2.手机蓝牙缓存异常需忘记设备重连；3.固件版本过低；4.电量过低；5.多设备抢占连接。"},'
     '{"kb_id":"KB-1002","title":"Acme Pro 系列重置方法","content":"长按充电盒按键15秒至指示灯红白交替闪烁即完成重置，'
     '随后在手机端删除旧配对记录重新搜索。若重置后仍无法搜索到设备，多为硬件故障，建议走质量问题退换。"},'
     '{"kb_id":"KB-1003","title":"质量问题判定标准","content":"重置无效 + 换设备仍无法连接 + 无进液/外观损伤，'
     '通常判定为质量问题，支持免费退换。"}],"suggested_action":"引导用户重置；若无效则判定质量问题走退款流程"}'),
    ("turn-5", "query_user_history",
     '{"user_id":"U-88123","total_orders":37,"refund_count_90d":1,"dispute_count":0,'
     '"risk_level":"low","vip_tier":"gold","register_days":1180,"payment_disputes":0,'
     '"avg_order_value":312.5,"last_refund_reason":"尺码不合适","chargeback_count":0,'
     '"complaint_count":0,"account_status":"normal","fraud_flags":[],"lifetime_value":11562.5}'),
    ("turn-6", "issue_refund",
     '{"refund_id":"RF20240520777","status":"APPROVED","amount":469.00,'
     '"expected_arrival":"1-3 个工作日","channel":"原路退回-微信","operator":"agent-bot",'
     '"return_shipping":"平台承担","return_address":"华东1仓退货组","return_label":"SF-RET-998877",'
     '"qc_required":true,"qc_deadline":"2024-05-27","refund_flow":"pending_return->qc->refund"}'),
    ("turn-7", "send_notification",
     '{"user_id":"U-88123","channel":"app","template":"refund_approved",'
     '"delivered":true,"message_id":"MSG-556677","sent_time":"2024-05-20T15:20:03",'
     '"params":{"refund_id":"RF20240520777","amount":469.00,"return_label":"SF-RET-998877"},'
     '"read_receipt":false,"fallback_sms_scheduled":true}'),
    ("turn-8", "close_ticket",
     '{"ticket_id":"TK-20240520-3345","status":"resolved","resolution":"refund_after_return",'
     '"csat_survey_sent":true,"handle_time_s":184,"escalated":false,"agent":"agent-bot",'
     '"summary_logged":true,"tags":["退款","质量问题","3C","已闭环"]}'),
]

# 供「上下文压缩」策略使用的旧轮次一句话摘要（把啰嗦的工具返回压成要点）
TOOL_SUMMARIES = {
    "turn-1": "[摘要] 订单 ORD20240517001：Acme降噪耳机Pro，实付469元，已于5/19签收，售后窗口至5/26。",
    "turn-2": "[摘要] 物流：顺丰已签收（5/19 14:03，本人签收），11 个轨迹节点均正常无异常。",
    "turn-3": "[摘要] 退款政策：质量问题可退、免手续费，需回寄质检，回寄运费平台承担，无需人工审批。",
    "turn-4": "[摘要] 知识库：先引导重置耳机；重置无效即判定质量问题，支持免费退换。",
    "turn-5": "[摘要] 用户风控：37单/90天仅1次退款/low风险/gold会员，信誉良好，无欺诈标记。",
    "turn-6": "[摘要] 已发起退款 RF20240520777：469元原路退微信，需回寄质检，平台承担回寄运费。",
    "turn-7": "[摘要] 已通过 app 通知用户退款已批准，附回寄面单。",
}


def _next_user_msg(tool_name: str, tool_result: str) -> str:
    """把工具返回包装成喂给模型的下一条 user 消息。"""
    return (
        f"[工具 {tool_name} 返回结果]\n{tool_result}\n\n"
        f"请基于以上结果给出你的推理，并决定下一步动作。"
    )


def run_naive(client) -> Tracer:
    """(a) 朴素做法。

    两个「反模式」：
    1. 前缀不稳定：每次调用在 system 最前面塞一个随机 session 头（uuid/时间戳），
       破坏前缀一致性 → OpenAI prompt cache 完全命中不了（cached_tokens=0）。
    2. 不压缩：每轮都把全部历史工具返回原样带上，上下文线性膨胀。
    """
    tracer = Tracer(client, name="A-朴素(无缓存/无压缩)")
    # 历史消息（会随轮次不断增长）
    history = [{"role": "user", "content": USER_REQUEST}]

    for step, tool, result in TOOL_RESULTS:
        # 反模式1：每轮生成新的易变前缀，放在 system 最前面，破坏 KV-cache
        volatile_head = f"[会话追踪] session={uuid.uuid4()} 请求序号={uuid.uuid4()}\n\n"
        system = {"role": "system", "content": volatile_head + STABLE_SYSTEM_PROMPT}

        messages = [system] + history
        resp = tracer.chat(step=step, tool=tool, model=MODEL,
                           messages=messages, temperature=0,
                           max_tokens=MAX_OUTPUT_TOKENS)
        assistant_text = resp.choices[0].message.content or ""

        # 反模式2：历史里保留完整（啰嗦的）工具返回，不做压缩
        history.append({"role": "assistant", "content": assistant_text})
        history.append({"role": "user", "content": _next_user_msg(tool, result)})

    return tracer


def run_optimized(client) -> Tracer:
    """(b) KV-cache 友好 + 上下文压缩。

    两个优化：
    1. 稳定长前缀：system 永远是同一份 STABLE_SYSTEM_PROMPT（> 1024 token），
       且始终放在消息列表最前面、逐字节不变 → OpenAI 自动缓存该前缀，
       后续轮次 cached_tokens 会显著 > 0，这部分按缓存价（5 折）计费。
    2. 上下文压缩：只保留最近 2 轮的完整工具返回，更早轮次替换为一句话摘要，
       控制上下文增长速率（对应书里「压缩历史轨迹」）。
    """
    tracer = Tracer(client, name="B-优化(KV缓存+压缩)")
    # 稳定 system，全程复用同一个对象内容
    system = {"role": "system", "content": STABLE_SYSTEM_PROMPT}

    # 分别记录：每一轮的 (step, assistant_text, tool_name, full_result)
    turns = []

    KEEP_VERBOSE = 2  # 最近 2 轮保留完整工具返回，更早的压成摘要

    for idx, (step, tool, result) in enumerate(TOOL_RESULTS):
        # 基于已完成的历史轮次，构造压缩后的历史消息
        history = [{"role": "user", "content": USER_REQUEST}]
        for j, (p_step, p_assistant, p_tool, p_result) in enumerate(turns):
            history.append({"role": "assistant", "content": p_assistant})
            # 距当前较远的轮次 → 用摘要替换啰嗦的工具返回（上下文压缩）
            if idx - j > KEEP_VERBOSE:
                compact = TOOL_SUMMARIES.get(p_step, f"[摘要] {p_tool} 已完成。")
                history.append({"role": "user", "content": compact})
            else:
                history.append({"role": "user",
                                "content": _next_user_msg(p_tool, p_result)})

        messages = [system] + history + [
            {"role": "user", "content": _next_user_msg(tool, result)}
        ]
        resp = tracer.chat(step=step, tool=tool, model=MODEL,
                           messages=messages, temperature=0,
                           max_tokens=MAX_OUTPUT_TOKENS)
        assistant_text = resp.choices[0].message.content or ""
        turns.append((step, assistant_text, tool, result))

    return tracer
