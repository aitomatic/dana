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
    parameters from the incoming kwargs context.

    Example:
        ```python
        # Create a workflow that returns data
        workflow = SearchWorkflow()

        # Compose with a callable that transforms the data
        def extract_titles(results):
            return [item['title'] for item in results]

        composed = workflow | extract_titles
        result = composed.execute(query="search term")
        # result contains merged workflow outputs including the list of titles
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

    def _extract_callable_params(self, kwargs_data: Any, sig: inspect.Signature) -> dict:
        """
        Extract parameters for the callable from kwargs based on its signature.

        Args:
            kwargs_data: The kwargs dict to extract from
            sig: The signature of the callable

        Returns:
            Dictionary of parameters to pass to the callable
        """
        params = {}

        # If not a dict, try to pass as single parameter
        if not isinstance(kwargs_data, dict):
            param_list = [
                p for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            if len(param_list) == 1:
                param_name = param_list[0].name
                return {param_name: kwargs_data}
            return {}

        # Extract parameters based on signature
        for param_name, param in sig.parameters.items():
            # Skip *args and **kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Priority 1: Check "result" key first for chaining support
            if "result" in kwargs_data:
                result_value = kwargs_data["result"]
                # If result is a dict and has the parameter
                if isinstance(result_value, dict) and param_name in result_value:
                    params[param_name] = result_value[param_name]
                    continue
                # If result is not a dict and callable has single param, use it
                elif not isinstance(result_value, dict):
                    param_list = [
                        p
                        for p in sig.parameters.values()
                        if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    ]
                    if len(param_list) == 1 and param_name == param_list[0].name:
                        params[param_name] = result_value
                        continue

            # Priority 2: Check top-level kwargs
            if param_name in kwargs_data:
                params[param_name] = kwargs_data[param_name]
            elif param.default is not inspect.Parameter.empty:
                # Has default, will be handled by callable
                continue
            # If required parameter is missing, we don't add it
            # The callable will raise TypeError if truly required

        return params

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute the wrapped callable with parameters extracted from kwargs.

        Args:
            **kwargs: Keyword arguments containing data from previous workflow stages

        Returns:
            The callable's return value
        """
        # Extract parameters from kwargs based on callable signature
        sig = inspect.signature(self._func)
        callable_params = self._extract_callable_params(kwargs, sig)

        # Call the function with extracted parameters
        callable_result = self._func(**callable_params)

        # If result is a dict, return it directly
        # Otherwise, wrap in a result key for consistency
        if isinstance(callable_result, dict):
            return callable_result
        else:
            return {"result": callable_result}

    def __repr__(self) -> str:
        """Get string representation of the workflow."""
        return f"<CallableWorkflow '{self._name}' workflow_id='{self.workflow_id}'>"
