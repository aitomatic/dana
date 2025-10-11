"""
Base WR (Workflow, Resource) class with common functionality.
"""

import inspect
import json
import xml.etree.ElementTree as ET
from typing import Any

from .base_war import BaseWAR
from .protocols import AgentProtocol
from .protocols.types import DictParams
from .protocols.war import IS_TOOL_USE


class BaseWR(BaseWAR):
    """Base class for WR (Workflow, Resource) objects with common functionality."""

    def __init__(self, agent: AgentProtocol | None = None, **kwargs):
        super().__init__(**kwargs)
        self._agent = agent

    @property
    def agent(self) -> AgentProtocol | None:
        """Get the agent of the workflow."""
        return self._agent

    @agent.setter
    def agent(self, value: AgentProtocol | None):
        """Set the agent of the workflow."""
        self._agent = value

    @property
    def public_description(self) -> str:
        return self._get_public_description()

    def query(self, **kwargs) -> DictParams:
        """Default query implementation.

        This method provides a default implementation for querying WAR objects.
        Subclasses can override this method to provide specific query functionality.

        Args:
            **kwargs: The arguments to the query method.

        Returns:
            A dictionary with the query results.
        """
        return {}
