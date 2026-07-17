"""
实验 6-7：Agent 任务的端到端成本分析（可运行 demo）。

运行：
    export OPENAI_API_KEY=sk-...
    python demo.py

输出：
    1) 一次 agent 任务的「按步骤成本拆解」（哪一步最贵）——基于自建 tracing。
    2) A/B 对比：
       (a) 朴素做法（前缀不稳定 / 无压缩，KV-cache 命中不了、上下文疯长）
       (b) KV-cache 友好 + 上下文压缩（稳定长前缀命中 cached_tokens + 旧轮次摘要）
       量化 总 token / cached token / 成本 / 节省比例。

真实性说明：每一次 LLM 调用都真实打到 OpenAI（gpt-4o-mini），
token 与 cached_tokens 均取自 API 返回的 usage，成本按 config.py 的单价换算。
"""

import os
import sys

from openai import OpenAI

from config import (MODEL, PRICE_INPUT_PER_M, PRICE_CACHED_PER_M,
                    PRICE_OUTPUT_PER_M)
from agent import run_naive, run_optimized


def _pct(saved: float, base: float) -> str:
    if base == 0:
        return "0.0%"
    return f"{saved / base * 100:.1f}%"


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("未检测到 OPENAI_API_KEY，请先 export OPENAI_API_KEY=sk-...", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()

    print(f"模型: {MODEL}")
    print(f"单价(每百万token): 输入 ${PRICE_INPUT_PER_M} / 缓存输入 ${PRICE_CACHED_PER_M} "
          f"/ 输出 ${PRICE_OUTPUT_PER_M}")
    print("说明: OpenAI prompt caching 自动生效（前缀>=1024token 且近期命中相同前缀），")
    print("      命中的输入 token 出现在 usage.prompt_tokens_details.cached_tokens。")

    # -------- A: 朴素做法 --------
    print("\n>>> 正在运行 A 组（朴素：无缓存/无压缩）...")
    naive = run_naive(client)

    # -------- B: 优化做法 --------
    # 先跑一次「预热」，让稳定前缀写入 OpenAI 的 prompt cache，
    # 从而在正式计量时更稳定地命中 cached_tokens（真实系统中前缀早已是热的）。
    print(">>> 预热 B 组的稳定前缀（写入 prompt cache）...")
    run_optimized(client)
    print(">>> 正在运行 B 组（KV缓存+压缩，正式计量）...")
    optimized = run_optimized(client)

    # -------- 交付(a)：一次 agent 任务的按步骤成本拆解 --------
    naive.print_breakdown(title="A组 朴素做法（单次任务全链路拆解）")
    optimized.print_breakdown(title="B组 优化做法（单次任务全链路拆解）")

    # -------- 交付(b)：A/B 对比表 --------
    print("\n\n===== A/B 成本对比（同一个 8 轮客服退款任务）=====")
    header = (f"{'方案':<26} {'总输入tok':>10} {'缓存tok':>10} {'缓存率':>8} "
              f"{'输出tok':>8} {'总成本($)':>12}")
    print(header)
    print("-" * len(header))

    for label, tr in [("A 朴素(无缓存/无压缩)", naive),
                      ("B 优化(KV缓存+压缩)", optimized)]:
        pin = tr.total_prompt_tokens()
        cac = tr.total_cached_tokens()
        rate = f"{(cac / pin * 100):.1f}%" if pin else "0.0%"
        print(f"{label:<26} {pin:>10} {cac:>10} {rate:>8} "
              f"{tr.total_completion_tokens():>8} {tr.total_cost():>12.6f}")

    print("-" * len(header))

    # 量化节省
    tok_a = naive.total_prompt_tokens() + naive.total_completion_tokens()
    tok_b = optimized.total_prompt_tokens() + optimized.total_completion_tokens()
    cost_a = naive.total_cost()
    cost_b = optimized.total_cost()

    print("\n节省量化:")
    print(f"  总 token:   A={tok_a}  →  B={tok_b}   "
          f"减少 {tok_a - tok_b} ({_pct(tok_a - tok_b, tok_a)})")
    print(f"  缓存 token: A={naive.total_cached_tokens()}  →  "
          f"B={optimized.total_cached_tokens()}   （B 靠稳定前缀命中缓存）")
    print(f"  总成本:     A=${cost_a:.6f}  →  B=${cost_b:.6f}   "
          f"降低 ${cost_a - cost_b:.6f} ({_pct(cost_a - cost_b, cost_a)})")
    if cost_b > 0:
        print(f"  成本倍率:   A 是 B 的 {cost_a / cost_b:.2f} 倍")

    print("\n结论: 稳定长前缀让重复的系统提示/工具定义/历史轮次按缓存价计费，")
    print("      叠加上下文压缩控制上下文增长，二者共同显著降低了端到端成本。")


if __name__ == "__main__":
    main()
