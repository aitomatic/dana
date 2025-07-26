"""
Call transformer for Dana language parsing.

This module handles function calls, method calls, and attribute access including:
- Regular function calls (func())
- Object method calls (obj.method())
- Attribute access (obj.attr)
- Indexing operations (obj[key])
- Argument processing (positional and keyword arguments)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.ast import (
    AttributeAccess,
    FunctionCall,
    Identifier,
    ObjectFunctionCall,
    SliceExpression,
    SubscriptExpression,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class CallTransformer(BaseTransformer):
    """Transformer for function calls, method calls, and attribute access."""

    def trailer(self, items):
        """
        Handle function calls, attribute access, and indexing after an atom.

        This method is responsible for detecting object method calls and creating the
        appropriate AST nodes. It distinguishes between:

        1. Object method calls (obj.method()) -> ObjectFunctionCall
        2. Regular function calls (func()) -> FunctionCall
        3. Attribute access (obj.attr) -> Identifier with dotted name
        4. Indexing operations (obj[key]) -> SubscriptExpression

        Object Method Call Detection:
        ----------------------------
        The method uses two strategies to detect object method calls:

        Strategy 1: Dotted identifier analysis
        - If base is an Identifier with dots (e.g., "local:obj.method")
        - And trailer is function call arguments
        - Split the dotted name into object parts and method name
        - Create ObjectFunctionCall with proper object and method separation

        Strategy 2: Sequential trailer analysis
        - Process trailers in sequence (e.g., obj -> .method -> ())
        - When a function call follows attribute access
        - Create ObjectFunctionCall with the base as object and previous trailer as method

        Examples:
        ---------
        - `websearch.list_tools()` -> ObjectFunctionCall(object=Identifier("local:websearch"), method_name="list_tools")
        - `obj.add(10)` -> ObjectFunctionCall(object=Identifier("local:obj"), method_name="add", args={"__positional": [10]})
        - `func()` -> FunctionCall(name="func")
        - `obj.attr` -> Identifier(name="local:obj.attr")

        Args:
            items: List containing base expression and trailer elements from parse tree

        Returns:
            AST node (ObjectFunctionCall, FunctionCall, Identifier, or SubscriptExpression)
        """
        base = items[0]
        trailers = items[1:]

        # Special case: if we have a dotted identifier followed by function call arguments,
        # this might be an object method call that was parsed as a dotted variable
        if len(trailers) == 1 and isinstance(base, Identifier) and "." in base.name:
            # Check if the trailer is either arguments or None (empty arguments)
            trailer = trailers[0]
            is_function_call = (
                hasattr(trailer, "data") and trailer.data == "arguments"
            ) or trailer is None  # Empty arguments case: obj.method()

            if is_function_call:
                # Check if this looks like an object method call
                # Split the dotted name to see if we can separate object from method
                name_parts = base.name.split(":")
                if len(name_parts) >= 3:  # e.g., "local:obj.method"
                    # Extract scope, object parts, and method name
                    scope = name_parts[0]  # "local"
                    method_name = name_parts[-1]  # "method"
                    object_parts = name_parts[1:-1]  # ["obj"] or ["obj", "subobj"]

                    # Create object identifier
                    object_name = f"{scope}.{'.'.join(object_parts)}"
                    object_expr = Identifier(name=object_name, location=getattr(base, "location", None))

                    # Create ObjectFunctionCall
                    if trailer is not None and hasattr(trailer, "children"):
                        args = self._process_function_arguments(trailer.children)
                    else:
                        args = {"__positional": []}  # Empty arguments

                    return ObjectFunctionCall(
                        object=object_expr, method_name=method_name, args=args, location=getattr(base, "location", None)
                    )

        # Original logic for other cases
        for i, t in enumerate(trailers):
            # Function call: ( ... ) or empty arguments (None)
            if (hasattr(t, "data") and t.data == "arguments") or t is None:
                # Check if this function call follows an attribute access
                if i > 0:
                    # Look at the previous trailer to see if it was attribute access
                    prev_trailer = trailers[i - 1]
                    if hasattr(prev_trailer, "type") and prev_trailer.type == "NAME":
                        # We have obj.method() - create ObjectFunctionCall

                        # The base object is everything except the last attribute
                        object_expr = base
                        method_name = prev_trailer.value

                        if t is not None and hasattr(t, "children"):
                            args = self._process_function_arguments(t.children)
                        else:
                            args = {"__positional": []}  # Empty arguments

                        return ObjectFunctionCall(
                            object=object_expr, method_name=method_name, args=args, location=getattr(base, "location", None)
                        )

                # Regular function call on base
                # For AttributeAccess nodes, keep them as-is for method call handling
                # For Identifier nodes, use the name string
                if isinstance(base, AttributeAccess):
                    name = base  # Keep AttributeAccess object for method calls
                else:
                    name = getattr(base, "name", None)
                    if not isinstance(name, str):
                        name = str(base)

                if t is not None and hasattr(t, "children"):
                    args = self._process_function_arguments(t.children)
                else:
                    args = {"__positional": []}  # Empty arguments

                return FunctionCall(name=name, args=args, location=getattr(base, "location", None))

            # Attribute access: .NAME
            elif hasattr(t, "type") and t.type == "NAME":
                # Always create AttributeAccess nodes for proper attribute access execution
                # This ensures that obj.attr is treated as attribute access, not a dotted variable name
                base = AttributeAccess(object=base, attribute=t.value, location=getattr(base, "location", None))

            # Indexing or Slicing: [ ... ]
            elif hasattr(t, "data") and t.data == "slice_list":
                # The slice_list contains either a single slice/index or multiple slice/index expressions
                slice_list_content = t.children[0] if hasattr(t, "children") and len(t.children) == 1 else t
                base = SubscriptExpression(object=base, index=slice_list_content, location=getattr(base, "location", None))

        return base

    def argument(self, items):
        """Transform an argument rule into an expression or keyword argument pair."""
        # items[0] is either a kw_arg tree or an expression
        arg_item = items[0]

        # If it's a kw_arg tree, return it as-is for now
        # The function call handler will process it properly
        if hasattr(arg_item, "data") and arg_item.data == "kw_arg":
            return arg_item

        # Otherwise, transform it as a regular expression
        # Note: This requires access to the main expression transformer
        # We'll need to handle this in the integration
        return arg_item

    def _process_function_arguments(self, arg_children):
        """Process function call arguments, handling both positional and keyword arguments."""
        args = []  # List of positional arguments
        kwargs = {}  # Dict of keyword arguments

        for arg_child in arg_children:
            # Skip None values (from optional COMMENT tokens)
            if arg_child is None:
                continue
            # Check if this is a kw_arg tree
            elif hasattr(arg_child, "data") and arg_child.data == "kw_arg":
                # Extract keyword argument name and value
                name = arg_child.children[0].value
                # Note: This requires the main expression transformer for the value
                # We'll handle this in the integration phase
                kwargs[name] = arg_child.children[1]  # Store raw value for now
            else:
                # Regular positional argument
                # Note: This requires the main expression transformer
                # We'll handle this in the integration phase
                args.append(arg_child)  # Store raw expression for now

        # Build the final args dict
        result = {"__positional": args}
        result.update(kwargs)
        return result

    def slice_or_index(self, items):
        """Handle slice_or_index rule - returns either a slice_expr or expr."""
        return items[0]  # Return the slice_expr or expr directly

    def slice_start_only(self, items):
        """Transform [start:] slice pattern."""
        return SliceExpression(start=items[0], stop=None, step=None)

    def slice_stop_only(self, items):
        """Transform [:stop] slice pattern."""
        return SliceExpression(start=None, stop=items[0], step=None)

    def slice_start_stop(self, items):
        """Transform [start:stop] slice pattern."""
        return SliceExpression(start=items[0], stop=items[1], step=None)

    def slice_start_stop_step(self, items):
        """Transform [start:stop:step] slice pattern."""
        return SliceExpression(start=items[0], stop=items[1], step=items[2])

    def slice_all(self, items):
        """Transform [:] slice pattern."""
        return SliceExpression(start=None, stop=None, step=None)

    def slice_step_only(self, items):
        """Transform [::step] slice pattern."""
        return SliceExpression(start=None, stop=None, step=items[0])

    def slice_expr(self, items):
        """Handle slice_expr containing one of the specific slice patterns."""
        # This method receives the result from one of the specific slice pattern methods
        return items[0]

    def slice_list(self, items):
        """Handle slice_list - returns either a single slice/index or a SliceTuple for multi-dimensional slicing."""
        if len(items) == 1:
            # Single dimension - return the slice/index directly
            return items[0]
        else:
            # Multi-dimensional - return a SliceTuple
            from dana.core.lang.ast import SliceTuple

            return SliceTuple(slices=items)

    def _get_full_attribute_name(self, attr):
        """Recursively extract full dotted name from AttributeAccess chain."""
        parts = []
        while isinstance(attr, AttributeAccess):
            parts.append(attr.attribute)
            attr = attr.object
        if isinstance(attr, Identifier):
            parts.append(attr.name)
        else:
            parts.append(str(attr))
        return ".".join(reversed(parts))
