"""
自建的轻量级 tracing / 可观测系统。

设计沿用分布式追踪的 span 树模型（见书 6.x「Agent 的可观测性」）：
    - 一次 agent 任务 = 一条 Trace
    - 每次 LLM 调用 / 工具调用 = 一个 Span
    - Span 记录：所属步骤、类型、token 用量（prompt/completion/cached）、时延、成本

用法：
    tracer = Tracer(client)
    resp = tracer.chat(step="turn-1", tool="query_order",
                       model=..., messages=..., temperature=0)
    tracer.print_breakdown()   # 打印按步骤/工具聚合的成本拆解
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional

from config import cost_usd


@dataclass
class Span:
    """一次被追踪的调用（这里主要是 LLM 调用）。"""
    step: str                 # 逻辑步骤名，如 "turn-2"
    tool: str                 # 该步骤关联的工具/动作名，用于归因“哪一步最贵”
    kind: str = "llm"         # span 类型：llm / tool
    prompt_tokens: int = 0
    cached_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class Tracer:
    """包裹 OpenAI client，自动记录每次 LLM 调用的 usage / 时延 / 成本。"""

    def __init__(self, client, name: str = "trace"):
        self.client = client
        self.name = name
        self.spans: List[Span] = []

    def chat(self, step: str, tool: str, **kwargs):
        """发起一次被追踪的 chat.completions 调用。

        kwargs 原样透传给 openai client（model / messages / temperature 等）。
        返回原始的 OpenAI response 对象，方便上层取 content。
        """
        t0 = time.time()
        resp = self.client.chat.completions.create(**kwargs)
        latency = time.time() - t0

        usage = resp.usage
        # cached_tokens 藏在 prompt_tokens_details 里，注意做防御式读取
        cached = 0
        details = getattr(usage, "prompt_tokens_details", None)
        if details is not None:
            cached = getattr(details, "cached_tokens", 0) or 0

        span = Span(
            step=step,
            tool=tool,
            kind="llm",
            prompt_tokens=usage.prompt_tokens,
            cached_tokens=cached,
            completion_tokens=usage.completion_tokens,
            latency_s=latency,
            cost_usd=cost_usd(usage.prompt_tokens, cached, usage.completion_tokens),
        )
        self.spans.append(span)
        return resp

    # ---------- 聚合 ----------
    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.spans)

    def total_prompt_tokens(self) -> int:
        return sum(s.prompt_tokens for s in self.spans)

    def total_cached_tokens(self) -> int:
        return sum(s.cached_tokens for s in self.spans)

    def total_completion_tokens(self) -> int:
        return sum(s.completion_tokens for s in self.spans)

    def total_latency(self) -> float:
        return sum(s.latency_s for s in self.spans)

    # ---------- 打印 ----------
    def print_breakdown(self, title: Optional[str] = None):
        """打印一次 agent 任务的按步骤成本拆解表，并指出最贵的一步。"""
        print()
        print(f"===== 成本拆解: {title or self.name} =====")
        header = (
            f"{'步骤':<8} {'工具/动作':<20} {'输入tok':>8} {'缓存tok':>8} "
            f"{'输出tok':>8} {'时延(s)':>8} {'成本($)':>12}"
        )
        print(header)
        print("-" * len(header))
        for s in self.spans:
            print(
                f"{s.step:<8} {s.tool:<20} {s.prompt_tokens:>8} {s.cached_tokens:>8} "
                f"{s.completion_tokens:>8} {s.latency_s:>8.2f} {s.cost_usd:>12.6f}"
            )
        print("-" * len(header))
        print(
            f"{'合计':<8} {'':<20} {self.total_prompt_tokens():>8} "
            f"{self.total_cached_tokens():>8} {self.total_completion_tokens():>8} "
            f"{self.total_latency():>8.2f} {self.total_cost():>12.6f}"
        )
        # 归因：哪一步最贵
        if self.spans:
            worst = max(self.spans, key=lambda s: s.cost_usd)
            share = worst.cost_usd / self.total_cost() * 100 if self.total_cost() else 0
            print(
                f"\n最贵的一步 → {worst.step} / {worst.tool}: "
                f"${worst.cost_usd:.6f}（占总成本 {share:.1f}%）"
            )
