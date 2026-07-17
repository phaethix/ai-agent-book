"""
全局配置：模型与价格。

价格换算成本时使用「每百万 token 单价（美元）」。
默认值取自 OpenAI gpt-4o-mini 的公开定价（2024-2025）：
    - 输入        : $0.15  / 1M tokens
    - 缓存命中输入 : $0.075 / 1M tokens   （命中 prompt cache 的输入按 5 折计费）
    - 输出        : $0.60  / 1M tokens

注意：
1. 只依赖 OpenAI（gpt-4o-mini），不要接入 OpenRouter / Anthropic / DeepSeek / SiliconFlow。
2. OpenAI 的 prompt caching 是「自动」的：当请求前缀 >= 1024 token 且与近期请求
   命中相同前缀时，usage.prompt_tokens_details.cached_tokens 会大于 0，
   这部分 token 按缓存价（更便宜）计费。本项目正是用它来真实体现 KV-cache 的节省。
"""

import os

# 使用的模型（务必是 OpenAI 有效模型）
MODEL = os.environ.get("COST_DEMO_MODEL", "gpt-4o-mini")

# 每百万 token 的美元单价
PRICE_INPUT_PER_M = 0.15      # 普通输入
PRICE_CACHED_PER_M = 0.075    # 命中缓存的输入（gpt-4o-mini 缓存读取为输入价的 50%）
PRICE_OUTPUT_PER_M = 0.60     # 输出


def cost_usd(prompt_tokens: int, cached_tokens: int, completion_tokens: int) -> float:
    """按 token 用量换算成本（美元）。

    prompt_tokens   : usage.prompt_tokens，包含了缓存命中的部分
    cached_tokens   : usage.prompt_tokens_details.cached_tokens，命中缓存的输入 token
    completion_tokens: usage.completion_tokens

    未命中缓存的输入 = prompt_tokens - cached_tokens，按普通输入价计费；
    命中缓存的输入按缓存价计费。
    """
    uncached_input = max(prompt_tokens - cached_tokens, 0)
    return (
        uncached_input / 1_000_000 * PRICE_INPUT_PER_M
        + cached_tokens / 1_000_000 * PRICE_CACHED_PER_M
        + completion_tokens / 1_000_000 * PRICE_OUTPUT_PER_M
    )
