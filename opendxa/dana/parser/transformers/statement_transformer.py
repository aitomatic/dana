"""Statement transformers for DANA language parsing."""

from lark import Token

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.parser.ast import (
    Assignment,
    Conditional,
    FunctionCall,
    Identifier,
    PrintStatement,
    Program,
    WhileLoop,
)
from opendxa.dana.parser.transformers.base_transformer import BaseTransformer
from opendxa.dana.parser.transformers.expression_transformer import ExpressionTransformer


class StatementTransformer(BaseTransformer):
    """Transformer for statement-related AST nodes."""

    def __init__(self):
        """Initialize the statement transformer."""
        super().__init__()
        self.expression_transformer = ExpressionTransformer()

    def start(self, items):
        """Transform the start rule into a Program node."""
        # If items is a list containing a single list, flatten it
        if len(items) == 1 and isinstance(items[0], list):
            statements = items[0]
        else:
            # Filter out None items (e.g., from comments or empty lines)
            statements = [item for item in items if item is not None]
        return Program(statements=statements)

    def statement(self, items):
        """Transform a statement rule."""
        # Return the first non-None item
        for item in items:
            if item is not None:
                return item
        return None

    def assignment(self, items):
        """Transform an assignment rule into an Assignment node."""
        target = items[0]
        value = items[1]

        # Ensure target has a scope prefix
        if not any(target.name.startswith(prefix) for prefix in RuntimeScopes.ALL_WITH_DOT):
            target = Identifier(name=self._insert_local_scope(target.name))

        return Assignment(target=target, value=value)

    def level(self, items):
        """Transform a log level into a string."""
        return items[0]

    def print_statement(self, items):
        """Transform a print statement rule into a PrintStatement node."""
        message = items[0]
        return PrintStatement(message=message)

    def conditional(self, items):
        """Transform a conditional rule into a Conditional node."""
        if_part = items[0]
        else_body = []

        # If we have an else part, extract the else body
        if len(items) > 1 and items[1] is not None:
            else_body = items[1]

        # Extract condition and if body from if_part
        condition = if_part[0]
        if_body = if_part[1:]

        # Use line info from the parse tree if available
        line_num = getattr(condition, "line", 0) or 0
        return Conditional(condition=condition, body=if_body, else_body=else_body, line_num=line_num)

    def if_part(self, items):
        """Transform if part of conditional into a list with condition first, then body statements."""
        # First item is the condition, rest are the body statements
        condition = items[0]

        # Filter out INDENT/DEDENT tokens and None values from the body
        body = [item for item in items[1:] if not (isinstance(item, Token) or item is None)]

        return [condition] + body

    def else_part(self, items):
        """Transform else part of conditional into a list of body statements."""
        # Filter out INDENT/DEDENT tokens and None values
        return [item for item in items if not (isinstance(item, Token) or item is None)]

    def while_loop(self, items):
        """Transform a while loop rule into a WhileLoop node."""
        condition = items[0]
        # Filter out INDENT/DEDENT tokens and None values from the body
        body = [item for item in items[1:] if not (isinstance(item, Token) or item is None)]
        # Use line info from the parse tree if available
        line_num = getattr(condition, "line", 0) or 0
        return WhileLoop(condition=condition, body=body, line_num=line_num)

    def function_call(self, items):
        """Transform a function call into a FunctionCall node."""
        name = items[0].name  # Identifier node

        # Process arguments
        args = {}
        if len(items) > 1:
            # We have arguments
            arg_items = items[1:]

            # Filter out None values
            arg_items = [item for item in arg_items if item is not None]

            # Process each argument
            for arg in arg_items:
                if isinstance(arg, dict):
                    # Named arguments
                    args.update(arg)
                elif isinstance(arg, list):
                    # List of arguments
                    positional_args = []
                    for _, sub_arg in enumerate(arg):
                        if isinstance(sub_arg, tuple):
                            # Named argument
                            key, value = sub_arg
                            args[key] = value
                        else:
                            # Positional argument
                            positional_args.append(sub_arg)
                    if positional_args:
                        args["__positional"] = positional_args
                elif isinstance(arg, tuple):
                    # Named argument
                    key, value = arg
                    args[key] = value
                else:
                    # Single positional argument
                    args["__positional"] = [arg]

        # If we have a single positional argument that's a dictionary of named arguments,
        # use that as our args
        if len(args) == 1 and "arg0" in args and isinstance(args["arg0"], dict):
            args = args["arg0"]

        return FunctionCall(name=name, args=args)

    def arg_list(self, items):
        """Transform an argument list into a list of arguments."""
        return items

    def positional_args(self, items):
        """Transform positional arguments into a list."""
        return items

    def named_args(self, items):
        """Transform named arguments into a dictionary."""
        # Convert list of tuples to dictionary
        args = {}
        for item in items:
            if isinstance(item, tuple):
                key, value = item
                args[key] = value
        return args

    def named_arg(self, items):
        """Transform a named argument into a tuple of (name, value)."""
        name = items[0].value
        value = items[1]
        return (name, value)

    def identifier(self, items):
        # This method is now handled by VariableTransformer
        raise NotImplementedError("identifier is handled by VariableTransformer")
