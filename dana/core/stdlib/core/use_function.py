from dana.common.resource.base_resource import BaseResource
from dana.common.utils.misc import Misc
from dana.core.lang.sandbox_context import SandboxContext


def use_function(context: SandboxContext, function_name: str, *args, _name: str | None = None, **kwargs) -> BaseResource:
    """Use a function in the context.
    This function is used to call a function in the context.
    It is used to call a function in the context.
    It is used to call a function in the context.

    Args:
        context: The sandbox context
        function_name: The name of the function to use
        *args: Positional arguments
        **kwargs: Keyword arguments
    """
    if _name is None:
        _name = Misc.generate_base64_uuid(length=6)
    if function_name.lower() == "mcp":
        from dana.integrations.mcp import MCPResource

        resource = MCPResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "rag":
        from dana.common.resource.rag.rag_resource import RAGResource

        resource = RAGResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    else:
        raise NotImplementedError(f"Function {function_name} not implemented")
