from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.utils.misc import Misc
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def agent_function(context: SandboxContext, *args, _name: str | None = None, **kwargs) -> BaseResource:
    """Create an A2A agent resource.

    Args:
        context: The sandbox context
        *args: Positional arguments for agent creation
        _name: Optional name for the agent (auto-generated if None)
        **kwargs: Keyword arguments for agent creation
    """
    name: str = _name if _name is not None else Misc.generate_uuid(length=6)
    from opendxa.contrib.mcp_a2a.resource.a2a import A2AAgent
    resource = A2AAgent(name=name, *args, **kwargs)
    context.set_agent(name, resource)
    return resource


def agent_pool_function(context: SandboxContext, *args, _name: str | None = None, **kwargs) -> BaseResource:
    """Create an A2A agent pool resource.

    Args:
        context: The sandbox context
        *args: Positional arguments for agent pool creation
        _name: Optional name for the agent pool (auto-generated if None)
        **kwargs: Keyword arguments for agent pool creation
    """
    name: str = _name if _name is not None else Misc.generate_uuid(length=6)
    from opendxa.contrib.mcp_a2a.agent.pool.agent_pool import AgentPool
    resource = AgentPool(name=name, *args, **kwargs, context=context)
    context.set(name, resource)
    return resource