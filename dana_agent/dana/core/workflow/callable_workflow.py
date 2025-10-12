"""CallableWorkflow - wraps a callable function as a workflow."""

from collections.abc import Callable
import inspect
from typing import Any

from dana.common.protocols import DictParams

# Import BaseWorkflow - circular import is handled by deferred execution
from dana.core.workflow.base_workflow import BaseWorkflow


class CallableWorkflow(BaseWorkflow):
    """
    Wrapper workflow that adapts a callable function into a workflow.

    This workflow inspects the callable's signature and extracts the required
    parameters from the "result" field of the incoming context.

    Example:
        ```python
        # Create a workflow that returns data
        workflow = SearchWorkflow()

        # Compose with a callable that transforms the data
        def extract_titles(results):
            return [item['title'] for item in results]

        composed = workflow | extract_titles
        result = composed.execute(query="search term")
        # result["result"] contains the list of titles
        ```
    """

    def __init__(
        self,
        func: Callable,
        args_transform: str | None = None,
        name: str | None = None,
        pre_callable: Callable[[DictParams], None] | None = None,
        post_callable: Callable[[DictParams], None] | None = None,
        **kwargs,
    ):
        """
        Initialize the CallableWorkflow.

        Args:
            func: The callable to wrap. Parameters are extracted from the result dict.
            args_transform: Declarative transformation string for input mappings.
                Format: "param1=source.path, param2=other.path -> output_name"
                Examples:
                    "content=fetch_result.content_text, query=query"
                    "urls=result.urls -> fetch_result"
            name: Optional name for the callable (defaults to func.__name__)
            pre_callable: Optional callable to transform arguments before execution
            post_callable: Optional callable to transform the result after execution
            **kwargs: Additional arguments passed to BaseWorkflow
        """
        # Store callable info
        self._func = func
        self._name = name or getattr(func, "__name__", "callable")
        # Track if args_transform was used (affects parameter extraction)
        self._has_args_transform = args_transform is not None

        # Initialize BaseWorkflow with auto_register=False by default
        # BaseWorkflow will handle args_transform and compile it to pre_callable
        super().__init__(
            workflow_type=f"CallableWorkflow[{self._name}]",
            args_transform=args_transform,
            pre_callable=pre_callable,
            post_callable=post_callable,
            auto_register=False,
            **kwargs,
        )

    def _extract_callable_params(self, result_data: Any, sig: inspect.Signature) -> dict:
        """
        Extract parameters for the callable from result_data based on its signature.

        Args:
            result_data: The data from kwargs["result"]
            sig: The signature of the callable

        Returns:
            Dictionary of parameters to pass to the callable
        """
        params = {}

        # If result_data is not a dict, we can't extract named parameters
        if not isinstance(result_data, dict):
            # If callable accepts a single positional parameter, pass result_data as-is
            param_list = [
                p for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            if len(param_list) == 1:
                param_name = param_list[0].name
                return {param_name: result_data}
            # Otherwise, return empty dict (callable will be called with no args)
            return {}

        # Extract parameters based on signature
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Extract value from result_data if available
            if param_name in result_data:
                params[param_name] = result_data[param_name]
            elif param.default is not inspect.Parameter.empty:
                # Has default, will be handled by callable
                continue
            # If required parameter is missing, we don't add it
            # The callable will raise TypeError if truly required

        return params

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute the wrapped callable with parameters extracted from result.

        Args:
            **kwargs: Keyword arguments - we look for previous workflow result

        Returns:
            The callable's return value (will be wrapped in "result" by execute())
        """
        # Note: BaseWorkflow.execute() handles pre_callable, post_callable, and wrapping
        # This _do_execute is called by BaseWorkflow.execute() for single workflow execution

        # If args_transform was used, pre_callable has already mapped parameters to kwargs
        # In that case, use kwargs directly. Otherwise, extract from result field.
        if self._has_args_transform:
            # args_transform's pre_callable has already mapped parameters to top-level kwargs
            # Extract parameters directly from kwargs based on signature
            sig = inspect.signature(self._func)
            callable_params = self._extract_callable_params(kwargs, sig)
        else:
            # No args_transform, extract from result field as before
            # Manual pre_callable (if any) has already transformed the data
            result_data = kwargs.get("result", kwargs)
            sig = inspect.signature(self._func)
            callable_params = self._extract_callable_params(result_data, sig)

        # Call the function with extracted parameters
        callable_result = self._func(**callable_params)

        return callable_result

    def __repr__(self) -> str:
        """Get string representation of the workflow."""
        return f"<CallableWorkflow '{self._name}' workflow_id='{self.workflow_id}'>"
