"""
Dana Context Engineering Framework

Provides knowledge architecture engineering capabilities that start well before
the first prompt is written. Enables pre-structured domain knowledge, context
templates, and runtime optimization for Dana's agent-native programming model.

Core Components:
- ContextTemplate: Reusable context patterns for domains and tasks
- ContextArchitect: Builds optimal contexts from knowledge assets
- RuntimeOptimizer: Performance tuning and caching for contexts
- DomainRegistry: Versioned domain knowledge packs

Integration with Dana:
- Enhanced reason() calls with engineered contexts
- Agent-native context templates and inheritance
- Pipeline context optimization
- POET-enabled context learning
"""

from .templates import ContextTemplate, ContextInstance, ContextSpec
from .architect import ContextArchitect
from .optimization import RuntimeContextOptimizer
from .registry import DomainRegistry, KnowledgeAsset
from .integration import ConEngIntegration
from .tokenizer import SimpleTokenizer, FinancialTokenizer, get_tokenizer, count_tokens

__all__ = [
    "ContextTemplate",
    "ContextInstance",
    "ContextSpec",
    "ContextArchitect",
    "RuntimeContextOptimizer",
    "DomainRegistry",
    "KnowledgeAsset",
    "ConEngIntegration",
    "SimpleTokenizer",
    "FinancialTokenizer",
    "get_tokenizer",
    "count_tokens",
]

# Framework version for template compatibility
__version__ = "0.1.0"
