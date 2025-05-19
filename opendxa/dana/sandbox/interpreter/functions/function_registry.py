"""
Unified Function Registry for DANA and Python functions.

This registry supports namespacing, type tagging, and unified dispatch for both DANA and Python functions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Callable, Dict, List, Optional


class FunctionRegistry:
    def __init__(self):
        # {namespace: {name: (func, type, metadata)}}
        self._functions: Dict[str, Dict[str, tuple]] = {}

    def register(
        self, name: str, func: Callable, namespace: Optional[str] = None, func_type: str = "dana", metadata: Optional[dict] = None
    ):
        ns = namespace or ""
        if ns not in self._functions:
            self._functions[ns] = {}
        if name in self._functions[ns]:
            print(f"Warning: Overwriting function '{name}' in namespace '{ns}'")
        self._functions[ns][name] = (func, func_type, metadata or {})

    def resolve(self, name: str, namespace: Optional[str] = None) -> Callable:
        ns = namespace or ""
        if ns in self._functions and name in self._functions[ns]:
            return self._functions[ns][name][0]
        raise KeyError(f"Function '{name}' not found in namespace '{ns}'")

    def call(
        self,
        name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Any = None,
        namespace: Optional[str] = None,
    ) -> Any:
        func = self.resolve(name, namespace)
        call_args = args if args is not None else []
        call_kwargs = kwargs if kwargs is not None else {}
        # Optionally: pass context if required by func_type/metadata
        return func(context, *call_args, **call_kwargs)

    def list(self, namespace: Optional[str] = None):
        ns = namespace or ""
        return list(self._functions.get(ns, {}).keys())

    def has(self, name: str, namespace: Optional[str] = None) -> bool:
        ns = namespace or ""
        return ns in self._functions and name in self._functions[ns]
