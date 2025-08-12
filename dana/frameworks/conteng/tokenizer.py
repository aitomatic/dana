"""
Basic Tokenizer Integration

Provides token counting utilities for context engineering.
Uses simple heuristics but can be extended to use proper tokenizers.
"""

import re
from typing import Any


class SimpleTokenizer:
    """Simple tokenizer using word-based heuristics"""

    # Common token-to-word ratios for different content types
    TOKEN_RATIOS = {
        "english": 1.3,  # English text averages ~1.3 tokens per word
        "code": 1.5,  # Code tends to have more tokens per word
        "json": 1.2,  # JSON is relatively token-efficient
        "technical": 1.4,  # Technical content has more complex terms
        "financial": 1.35,  # Financial content with numbers and terms
    }

    def __init__(self, content_type: str = "english"):
        self.ratio = self.TOKEN_RATIOS.get(content_type, 1.3)

    def count_tokens(self, text: str) -> int:
        """Count approximate tokens in text"""
        if not text:
            return 0

        # Count words (simplified)
        words = len(re.findall(r"\b\w+\b", text))

        # Count numbers separately (tend to be tokenized differently)
        numbers = len(re.findall(r"\b\d+\b", text))

        # Count punctuation that becomes tokens
        special_chars = len(re.findall(r"[^\w\s]", text))

        # Apply ratio and add special handling
        estimated_tokens = int((words * self.ratio) + (numbers * 0.8) + (special_chars * 0.3))

        return max(1, estimated_tokens)  # At least 1 token for non-empty text

    def count_tokens_batch(self, texts: list[str]) -> list[int]:
        """Count tokens for multiple texts"""
        return [self.count_tokens(text) for text in texts]

    def estimate_tokens_for_object(self, obj: Any) -> int:
        """Estimate tokens for complex objects"""
        if isinstance(obj, str):
            return self.count_tokens(obj)
        elif isinstance(obj, list | tuple):
            return sum(self.estimate_tokens_for_object(item) for item in obj)
        elif isinstance(obj, dict):
            total = 0
            for key, value in obj.items():
                total += self.count_tokens(str(key))  # Keys become tokens
                total += self.estimate_tokens_for_object(value)
            return total
        else:
            return self.count_tokens(str(obj))


class FinancialTokenizer(SimpleTokenizer):
    """Tokenizer optimized for financial content"""

    def __init__(self):
        super().__init__("financial")

        # Financial terms that tend to be single tokens
        self.financial_terms = {
            "var",
            "volatility",
            "portfolio",
            "derivative",
            "equity",
            "bond",
            "yield",
            "duration",
            "convexity",
            "delta",
            "gamma",
            "theta",
            "vega",
            "rho",
            "basel",
            "tier1",
            "cet1",
            "lcr",
            "nsfr",
            "cvar",
            "es",
            "sharpe",
            "treynor",
            "alpha",
            "beta",
            "correlation",
            "covariance",
            "regression",
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens with financial term optimization"""
        base_count = super().count_tokens(text)

        # Adjust for financial terms (tend to be tokenized as single units)
        text_lower = text.lower()
        financial_term_count = sum(1 for term in self.financial_terms if term in text_lower)

        # Financial terms are typically more token-efficient
        adjustment = financial_term_count * -0.2  # Slight reduction

        return max(1, int(base_count + adjustment))


# Global tokenizer instances for different use cases
_tokenizers: dict[str, SimpleTokenizer] = {
    "default": SimpleTokenizer(),
    "financial": FinancialTokenizer(),
    "technical": SimpleTokenizer("technical"),
    "code": SimpleTokenizer("code"),
    "json": SimpleTokenizer("json"),
}


def get_tokenizer(tokenizer_type: str = "default") -> SimpleTokenizer:
    """Get tokenizer instance by type"""
    return _tokenizers.get(tokenizer_type, _tokenizers["default"])


def count_tokens(text: str, tokenizer_type: str = "default") -> int:
    """Convenience function to count tokens"""
    return get_tokenizer(tokenizer_type).count_tokens(text)


def count_tokens_financial(text: str) -> int:
    """Convenience function for financial content"""
    return count_tokens(text, "financial")


# Integration helpers for updating existing code
def update_token_counts_in_architect():
    """Helper to update token counting in architect.py"""
    # This would be called to update the architect to use proper tokenizer
    # instead of the simple word_count * 1.3 heuristic
    pass


def update_token_counts_in_templates():
    """Helper to update token counting in templates.py"""
    # This would update TokenBudget and other classes to use proper tokenizer
    pass
