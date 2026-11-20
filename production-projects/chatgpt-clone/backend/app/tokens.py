"""Token counting -- from the Deploy lesson's "Token Usage Tracking" step.

The lesson's original snippet also had an `estimate_cost()` helper with
hardcoded per-token dollar rates; that's removed here per the no-pricing-
content rule applied to this course. Token *counting* (not cost) is a
legitimate product feature and is kept.
"""
import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))
