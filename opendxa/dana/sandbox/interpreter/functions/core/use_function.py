from opendxa.common.resource.base_resource import BaseResource
from opendxa.common.utils.misc import Misc
from opendxa.dana.sandbox.sandbox_context import SandboxContext
from pathlib import Path
from typing import Callable
from functools import wraps


def create_function_with_better_doc_string(func: Callable, doc_string: str) -> Callable:
    """Create a function with a better doc string.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__doc__ = doc_string
    return wrapper

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
        from opendxa.contrib.mcp_a2a.resource.mcp import MCPResource

        resource = MCPResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() in ["rag", "kb"]:
        from opendxa.contrib.rag_resource import RAGResource

        resource = RAGResource(*args, name=_name, **kwargs)
        sources = kwargs.get("sources", [])
        processed_sources = []
        for source in sources:
            if source.startswith("http"):
                processed_sources.append(source)
            else:
                processed_sources.append(Path(source).stem)
        doc_string = f"{resource.query.__func__.__doc__} These are the expertise sources: {processed_sources} known as {_name}"
        resource.query = create_function_with_better_doc_string(resource.query, doc_string)
        context.set_resource(_name, resource)
        return resource
    elif function_name.lower() == "file_reader":
        from opendxa.contrib.rag_resource.common.resource.rag.file_reader_resource import FileReaderResource
        resource = FileReaderResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource

    elif function_name.lower() == "feedback":
        from opendxa.contrib.feedback_resource.common.resource import FeedbackResource

        resource = FeedbackResource(*args, name=_name, **kwargs)
        context.set_resource(_name, resource)
        return resource
    else:
        raise NotImplementedError(f"Function {function_name} not implemented")
