"""OpenDXA API Infrastructure

Generic API infrastructure for all OpenDXA services including POET, MagicFunctions, and others.
Provides unified server and client abstractions with environment-based configuration.
"""

from .server import OpenDXAServer
from .client import APIClient

__all__ = ["OpenDXAServer", "APIClient"]
