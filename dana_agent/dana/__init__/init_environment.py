"""
Dana Agent - Domain-Aware Neurosymbolic Agents

This package provides the core agent framework for building and managing
specialized AI agents with domain-specific knowledge and capabilities.
"""

# Import and run initialization (loads .env files)
from dotenv import find_dotenv, load_dotenv


def init_environment():
    """Load environment variables from .env file."""
    dotenv_path = find_dotenv()
    print(f"Loading environment variables from {dotenv_path}")
    if dotenv_path:
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
