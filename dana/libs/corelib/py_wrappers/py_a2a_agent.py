from typing import Any

from dana.common import SandboxContext
from dana.integrations.a2a import A2AAgent

__all__ = ["py_a2a_agent"]


def _get_cache(context: SandboxContext) -> dict[str, A2AAgent]:
    cache = getattr(context, "_a2a_agent_cache", None)
    if cache is None:
        cache = {}
        setattr(context, "_a2a_agent_cache", cache)
    return cache


def _compute_key(name: str | None, url: str | None) -> str:
    if name and name.strip():
        return f"name:{name.strip()}"
    if url and url.strip():
        return f"url:{url.strip()}"
    # Fallback singleton when neither provided
    return "default"


def py_a2a_agent(
    context: SandboxContext,
    _self: Any = None,
    *,
    url: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30 * 60,
    google_a2a_compatible: bool = False,
    name: str | None = None,
) -> A2AAgent:
    """
    Create or retrieve a singleton A2AAgent by identity.

    Identity precedence: name > url > default.

    Args:
        context: Sandbox execution context (injected by runtime)
        _self: Unused placeholder for registry binding
        url: Remote A2A endpoint URL
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        google_a2a_compatible: Enable Google A2A compatibility quirks
        name: Optional logical name (overrides cache identity)

    Returns:
        A cached A2AAgent instance for the given identity
    """
    if url is None and (name is None or name.strip() == ""):
        raise ValueError("a2a_agent requires at least 'url' or 'name' to identify the agent")

    cache = _get_cache(context)
    key = _compute_key(name, url)

    if key in cache:
        return cache[key]

    # Derive a human-friendly name
    agent_name = name or (url or "A2A Agent")

    agent = A2AAgent(
        name=agent_name,
        description=None,
        config=None,
        url=url,
        headers=headers,
        timeout=timeout,
        google_a2a_compatible=google_a2a_compatible,
    )

    cache[key] = agent
    return agent
