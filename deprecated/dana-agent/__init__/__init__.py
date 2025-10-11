"""
Dana Agent - Domain-Aware Neurosymbolic Agents

This package provides the core agent framework for building and managing
specialized AI agents with domain-specific knowledge and capabilities.
"""

# Import and run initialization (loads .env files)
from dotenv import find_dotenv, load_dotenv


def _load_env():
    """Load environment variables from .env file."""
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()


# Load .env automatically when package is imported
_load_env()

# Import main components
from dana_agent.common import LLM, LLMMessage, LLMResponse

from dana_agent.core import STARAgent


__version__ = "0.6.0.1rc3"
__author__ = "Christopher Nguyen"
__email__ = "ctn@aitomatic.com"

__all__ = ["LLM", "LLMMessage", "LLMResponse", "STARAgent", "__version__"]
