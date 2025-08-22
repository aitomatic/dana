"""
Agent blueprint for A2A_Agent as a first-class Dana AgentInstance.

Registers an AgentType named 'A2A_Agent' with fields for remote A2A connectivity
and implements a solve() method that delegates to the A2A client.
"""

from __future__ import annotations

from typing import Any

from dana.common.utils.misc import Misc
from dana.core.builtin_types.agent_system import AgentType
from dana.integrations.a2a.client.a2a_client import BaseA2AClient
from dana.registry import register_agent_type


def _get_or_create_client(instance: Any) -> BaseA2AClient:
    """Lazily create and cache the A2A client on the agent instance."""
    try:
        client = getattr(instance, "_a2a_client", None)
        if client is not None:
            return client
    except Exception:
        # Instance may not have attribute yet
        pass

    endpoint_url: str = instance.url
    headers: dict[str, str] = instance.headers or {}
    timeout: int = int(instance.timeout or 30 * 60)
    google_a2a_compatible: bool = bool(instance.google_a2a_compatible or False)

    client = BaseA2AClient(
        endpoint_url=endpoint_url,
        headers=headers,
        timeout=timeout,
        google_a2a_compatible=google_a2a_compatible,
    )
    # Cache on instance (allowed for private attrs)
    setattr(instance, "_a2a_client", client)
    return client


def _solve(instance: Any, sandbox_context: Any, message: str, context: dict | None = None) -> str:
    """Agent method: solve. Delegates to remote A2A."""
    client = _get_or_create_client(instance)
    metadata = context or {}
    # Ensure sync boundary without leaking event loop complexities
    return Misc.safe_asyncio_run(client.ask_with_metadata(message, metadata))


def _refresh_agent_card(instance: Any, sandbox_context: Any) -> None:
    client = _get_or_create_client(instance)
    client.refresh_agent_card()


def _get_agent_card(instance: Any, sandbox_context: Any) -> dict[str, Any]:
    client = _get_or_create_client(instance)
    return client.json_agent_card


# Define and register AgentType
_fields: dict[str, str] = {
    "name": "str",
    "url": "str",
    "headers": "dict",
    "timeout": "int",
    "google_a2a_compatible": "bool",
}

_field_order = ["name", "url", "headers", "timeout", "google_a2a_compatible"]
_field_comments: dict[str, str] = {
    "name": "Logical agent name",
    "url": "Remote A2A endpoint URL",
    "headers": "Optional HTTP headers",
    "timeout": "Timeout seconds for A2A requests",
    "google_a2a_compatible": "Enable Google A2A compatibility quirks",
}
_defaults: dict[str, Any] = {
    "headers": {},
    "timeout": 30 * 60,
    "google_a2a_compatible": False,
}

_a2a_agent_type = AgentType(
    name="A2A_Agent",
    fields=_fields,
    field_order=_field_order,
    field_comments=_field_comments,
    field_defaults=_defaults,
    docstring=(
        "A2A_Agent: First-class agent that delegates to a remote A2A server.\n"
        "Fields: name, url, headers, timeout, google_a2a_compatible.\n"
        "Methods: solve(message, context)."
    ),
)

# Attach/override agent methods
_a2a_agent_type.add_agent_method("solve", _solve)
_a2a_agent_type.add_agent_method("refresh_agent_card", _refresh_agent_card)
_a2a_agent_type.add_agent_method("agent_card", _get_agent_card)

# Register so it's available to StructTypeRegistry and Agent registry
register_agent_type(_a2a_agent_type)


def create_a2a_agent(*, name: str, url: str, headers: dict | None = None, timeout: int = 30 * 60, google_a2a_compatible: bool = False):
    """Convenience factory to create an A2A_Agent instance."""
    from dana.registry import TYPE_REGISTRY

    values = {
        "name": name,
        "url": url,
        "headers": headers or {},
        "timeout": timeout,
        "google_a2a_compatible": google_a2a_compatible,
    }
    return TYPE_REGISTRY.create_instance("A2A_Agent", values)
