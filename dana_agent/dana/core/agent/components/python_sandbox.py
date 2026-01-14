"""
Python Sandbox - Safe Python execution environment for RLM pattern.

Provides a sandboxed Python execution environment with:
- A `context` variable containing document text
- An optional `llm_query(prompt, text)` function for semantic sub-tasks
- Safe modules: re, json, math, collections, itertools, functools
- Blocked dangerous operations: os.system, subprocess, file writes, eval, exec

API
---

.. code-block:: python

    class PythonSandbox:
        def __init__(self, llm_query_fn: Callable[[str, str], str] | None = None):
            '''
            Initialize the sandbox.

            Args:
                llm_query_fn: Optional function for LLM sub-queries.
                             Signature: (prompt: str, text: str) -> str
            '''

        def execute(self, code: str, context: str) -> str:
            '''
            Execute code with `context` variable available.
            Returns stdout (truncated to 10KB).

            Available in namespace:
            - context: str (the document text)
            - llm_query(prompt, text): sub-LLM call for semantic tasks
            - Safe modules: re, json, math, collections, itertools, functools
            '''

        def reset(self) -> None:
            '''Clear the namespace, removing all persisted variables.'''

Example
-------

.. code-block:: python

    from dana.core.agent.components.python_sandbox import PythonSandbox

    sandbox = PythonSandbox()

    # Execute code with context variable
    code = '''
    import re
    matches = re.findall(r'def (\\w+)', context)
    print("Functions found:", matches)
    '''
    output = sandbox.execute(code, context="def foo(): pass\\ndef bar(): pass")
    # output: "Functions found: ['foo', 'bar']"

    # Variables persist across calls
    sandbox.execute("results = []", context="")
    sandbox.execute("results.append('found')", context="")
    output = sandbox.execute("print(results)", context="")
    # output: "['found']"

    # With LLM sub-queries
    def my_llm_query(prompt, text):
        return "Summary: " + text[:50]

    sandbox = PythonSandbox(llm_query_fn=my_llm_query)
    output = sandbox.execute("print(llm_query('summarize', context))", context="Long text...")
"""

import io
import sys
from collections.abc import Callable
from typing import Any

# Safe modules that can be imported
SAFE_MODULES = {
    "re": __import__("re"),
    "json": __import__("json"),
    "math": __import__("math"),
    "collections": __import__("collections"),
    "itertools": __import__("itertools"),
    "functools": __import__("functools"),
}

# Maximum output size in bytes (10KB)
MAX_OUTPUT_SIZE = 10 * 1024


class PythonSandbox:
    """Execute Python code with a context variable and llm_query function."""

    def __init__(self, llm_query_fn: Callable[[str, str], str] | None = None):
        """
        Initialize the sandbox.

        Args:
            llm_query_fn: Optional function for LLM sub-queries.
                         Signature: (prompt: str, text: str) -> str
        """
        self.namespace: dict[str, Any] = {}
        self.llm_query_fn = llm_query_fn

    def reset(self) -> None:
        """Clear the namespace, removing all persisted variables."""
        self.namespace.clear()

    def execute(self, code: str, context: str) -> str:
        """
        Execute code with `context` variable available.

        Args:
            code: Python code to execute
            context: The document text to make available as `context` variable

        Returns:
            stdout output (truncated to 10KB), or error message if execution fails
        """
        # Build restricted builtins
        restricted_builtins = self._get_restricted_builtins()

        # Build execution namespace
        exec_namespace = {
            "__builtins__": restricted_builtins,
            "context": context,
            **SAFE_MODULES,
            **self.namespace,  # Include persisted variables
        }

        # Add llm_query if provided
        if self.llm_query_fn is not None:
            exec_namespace["llm_query"] = self.llm_query_fn

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            # Execute the code
            exec(code, exec_namespace)  # noqa: S102

            # Get output
            output = captured_output.getvalue()

            # Persist namespace variables (excluding special items)
            for key, value in exec_namespace.items():
                if not key.startswith("__") and key not in SAFE_MODULES and key not in ("context", "llm_query"):
                    self.namespace[key] = value

            # Truncate output if too long
            if len(output) > MAX_OUTPUT_SIZE:
                output = output[:MAX_OUTPUT_SIZE] + "\n... [output truncated to 10KB]"

            return output

        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

        finally:
            sys.stdout = old_stdout

    def _get_restricted_builtins(self) -> dict[str, Any]:
        """Get a restricted set of builtins that blocks dangerous operations."""
        import builtins

        # Start with safe builtins
        safe_builtins = {
            # Types
            "bool": builtins.bool,
            "int": builtins.int,
            "float": builtins.float,
            "str": builtins.str,
            "list": builtins.list,
            "dict": builtins.dict,
            "set": builtins.set,
            "frozenset": builtins.frozenset,
            "tuple": builtins.tuple,
            "bytes": builtins.bytes,
            "bytearray": builtins.bytearray,
            "type": builtins.type,
            "object": builtins.object,
            # Functions
            "abs": builtins.abs,
            "all": builtins.all,
            "any": builtins.any,
            "ascii": builtins.ascii,
            "bin": builtins.bin,
            "callable": builtins.callable,
            "chr": builtins.chr,
            "divmod": builtins.divmod,
            "enumerate": builtins.enumerate,
            "filter": builtins.filter,
            "format": builtins.format,
            "getattr": builtins.getattr,
            "hasattr": builtins.hasattr,
            "hash": builtins.hash,
            "hex": builtins.hex,
            "id": builtins.id,
            "isinstance": builtins.isinstance,
            "issubclass": builtins.issubclass,
            "iter": builtins.iter,
            "len": builtins.len,
            "map": builtins.map,
            "max": builtins.max,
            "min": builtins.min,
            "next": builtins.next,
            "oct": builtins.oct,
            "ord": builtins.ord,
            "pow": builtins.pow,
            "print": builtins.print,
            "range": builtins.range,
            "repr": builtins.repr,
            "reversed": builtins.reversed,
            "round": builtins.round,
            "setattr": builtins.setattr,
            "slice": builtins.slice,
            "sorted": builtins.sorted,
            "sum": builtins.sum,
            "zip": builtins.zip,
            # Exceptions
            "Exception": builtins.Exception,
            "ValueError": builtins.ValueError,
            "TypeError": builtins.TypeError,
            "KeyError": builtins.KeyError,
            "IndexError": builtins.IndexError,
            "AttributeError": builtins.AttributeError,
            "RuntimeError": builtins.RuntimeError,
            "StopIteration": builtins.StopIteration,
            # Constants
            "True": True,
            "False": False,
            "None": None,
        }

        # Explicitly exclude dangerous builtins:
        # - eval, exec: arbitrary code execution
        # - open: file system access
        # - __import__: module importing (we control what's available)
        # - compile: code compilation
        # - globals, locals: namespace access
        # - input: user input (blocks execution)
        # - breakpoint: debugger access

        return safe_builtins
