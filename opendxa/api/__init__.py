"""OpenDXA API Infrastructure

Generic API infrastructure for all OpenDXA services including POET, MagicFunctions, and others.
Provides unified server and client abstractions with environment-based configuration.
"""

from .client import APIClient
from .server import OpenDXAServer

__all__ = ["OpenDXAServer", "APIClient"]
