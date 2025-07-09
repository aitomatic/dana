from dana.agent.abstract_dana_agent import AbstractDanaAgent
from dana.common.resource.base_resource import BaseResource
from dana.common.utils.misc import Misc
from dana.core.lang.sandbox_context import SandboxContext


def agent_function(context: SandboxContext, *args, _name: str | None = None, **kwargs) -> AbstractDanaAgent:
    """Create an agent resource (A2A or module-based).

    Args:
        context: The sandbox context
        *args: Positional arguments for agent creation
        _name: Optional name for the agent (auto-generated if None)
        **kwargs: Keyword arguments for agent creation
                 - module: Dana module to wrap as agent
                 - url: URL for A2A agent
                 - Other parameters for agent creation
    """
    name: str = _name if _name is not None else Misc.generate_uuid(length=6)

    # Check if module parameter is provided
    if "module" in kwargs:
        # Create module-based agent
        module = kwargs.pop("module")  # Remove module from kwargs
        return _create_module_agent(context, name, module, **kwargs)
    else:
        # Create A2A agent (existing behavior)
        return _create_a2a_agent(context, name, *args, **kwargs)


def _create_module_agent(context: SandboxContext, name: str, module, **kwargs) -> AbstractDanaAgent:
    """Create a module-based agent.

    Args:
        context: The sandbox context
        name: Agent name
        module: Dana module to wrap as agent
        **kwargs: Additional parameters
    """
    from dana.integrations.agent_to_agent import ModuleAgent

    # Try to get the module's original context for resource discovery
    # Look for the context from the module's solve function (if it's a DanaFunction)
    module_context = context  # Default fallback

    if hasattr(module, "solve"):
        solve_func = module.solve
        # Check if it's a DanaFunction with its own context
        from dana.core.lang.interpreter.functions.dana_function import DanaFunction

        if isinstance(solve_func, DanaFunction) and solve_func.context is not None:
            # Use the module's original context for resource discovery
            module_context = solve_func.context

    resource = ModuleAgent(name=name, module=module, context=module_context, **kwargs)
    context.set_agent(name, resource)
    return resource


def _create_a2a_agent(context: SandboxContext, name: str, *args, **kwargs) -> AbstractDanaAgent:
    """Create an A2A agent (existing functionality).

    Args:
        context: The sandbox context
        name: Agent name
        *args: Positional arguments for agent creation
        **kwargs: Keyword arguments for agent creation
    """
    from dana.integrations.agent_to_agent import A2AAgent

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
    from dana.integrations.agent_to_agent.pool.agent_pool import AgentPool

    resource = AgentPool(name=name, *args, **kwargs, context=context)
    context.set(name, resource)
    return resource
