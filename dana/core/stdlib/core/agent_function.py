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

    # A2AAgent constructor: __init__(name, description=None, config=None, url=None, headers=None, timeout=30*60, google_a2a_compatible=False)
    # Handle positional arguments properly
    if args:
        # If args provided, they should be [description, config, url, headers, timeout, google_a2a_compatible]
        # But we'll use kwargs for clarity and safety
        if len(args) > 0 and "description" not in kwargs:
            kwargs["description"] = args[0]
        if len(args) > 1 and "config" not in kwargs:
            kwargs["config"] = args[1]
        if len(args) > 2 and "url" not in kwargs:
            kwargs["url"] = args[2]
        if len(args) > 3 and "headers" not in kwargs:
            kwargs["headers"] = args[3]
        if len(args) > 4 and "timeout" not in kwargs:
            kwargs["timeout"] = args[4]
        if len(args) > 5 and "google_a2a_compatible" not in kwargs:
            kwargs["google_a2a_compatible"] = args[5]

    resource = A2AAgent(name=name, **kwargs)
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

    # AgentPool constructor: __init__(name, description=None, agents=None, exclude_self=False, context=None)
    # Handle positional arguments properly
    if args:
        if len(args) > 0 and "description" not in kwargs:
            kwargs["description"] = args[0]
        if len(args) > 1 and "agents" not in kwargs:
            kwargs["agents"] = args[1]
        if len(args) > 2 and "exclude_self" not in kwargs:
            kwargs["exclude_self"] = args[2]

    resource = AgentPool(name=name, context=context, **kwargs)
    context.set(name, resource)
    return resource
