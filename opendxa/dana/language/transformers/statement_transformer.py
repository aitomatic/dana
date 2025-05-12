"""Statement transformers for DANA language parsing."""

from lark import Token

from opendxa.dana.common.runtime_scopes import RuntimeScopes
from opendxa.dana.language.ast import (
    Assignment,
    Conditional,
    Expression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    PrintStatement,
    Program,
    WhileLoop,
)
from opendxa.dana.language.transformers.base_transformer import BaseTransformer
from opendxa.dana.language.transformers.expression_transformer import ExpressionTransformer


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

    def bare_identifier(self, items: list[Token]) -> Expression:
        """Transform a bare identifier into an Expression.

        Args:
            items: List containing a single identifier token

        Returns:
            Identifier node representing the bare identifier
        """
        result = self.expression_transformer.identifier(items)
        # If result is a Token, wrap in Identifier
        if isinstance(result, Token):
            return Identifier(name=result.value)
        return result  # type: ignore

    def assignment(self, items):
        """Transform an assignment rule into an Assignment node."""
        target = items[0]
        value = items[1]

        # Ensure target has a scope prefix
        if not any(target.name.startswith(prefix) for prefix in RuntimeScopes.ALL_WITH_DOT):
            target = Identifier(name=self._insert_local_scope(target.name))

        return Assignment(target=target, value=value)

    def log_statement(self, items):
        """Transform a log statement rule into a LogStatement node."""
        # Default level is INFO
        level = LogLevel.INFO

        # Filter out None values
        items = [item for item in items if item is not None]

        if not items:
            return None

        # If level is specified, use it
        if len(items) > 1 and hasattr(items[0], "value"):
            level_str = items[0].value.upper()
            level = LogLevel[level_str]
            message = items[1]
        else:
            message = items[0]

        return LogStatement(message=message, level=level)

    def level(self, items):
        """Transform a log level into a string."""
        return items[0]

    def DEBUG(self, _):
        return Token("LEVEL", "DEBUG")  # type: ignore

    def INFO(self, _):
        return Token("LEVEL", "INFO")  # type: ignore

    def WARN(self, _):
        return Token("LEVEL", "WARN")  # type: ignore

    def ERROR(self, _):
        return Token("LEVEL", "ERROR")  # type: ignore

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

    def log_level_set_statement(self, items):
        """Transform a log level set statement into a LogLevelSetStatement node."""
        if not items:
            return None

        # Check what type of item we have
        item = items[0]

        # Handle string literal (log.setLevel("INFO"))
        if isinstance(item, Token) and item.type == "STRING":
            level_str = item.value.strip("\"'")
            try:
                level = LogLevel[level_str.upper()]
            except KeyError:
                # For invalid levels, use ERROR as default and let runtime handle it
                level = LogLevel.ERROR
            return LogLevelSetStatement(level=level)

        # Handle level token (log.setLevel(INFO))
        elif hasattr(item, "value"):
            level_str = item.value.upper()
            try:
                level = LogLevel[level_str]
            except KeyError:
                # For invalid levels, use ERROR as default and let runtime handle it
                level = LogLevel.ERROR
            return LogLevelSetStatement(level=level)

        # If we got here, something went wrong
        return LogLevelSetStatement(level=LogLevel.ERROR)

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
                    for i, sub_arg in enumerate(arg):
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

        # For direct reason() function calls, handle special case
        if name == "reason" and "arg0" in args:
            return self._process_reason_function_call(args)

        # If we have a single positional argument that's a dictionary of named arguments,
        # use that as our args
        if len(args) == 1 and "arg0" in args and isinstance(args["arg0"], dict):
            args = args["arg0"]

        return FunctionCall(name=name, args=args)

    def _process_reason_function_call(self, args):
        """Process a direct reason() function call."""
        # This is a special case for reason() statements without assignment
        prompt = args["arg0"]

        # Convert string tokens to LiteralExpression
        if isinstance(prompt, Token) and prompt.type in ("STRING", "DOUBLE_QUOTE_STRING", "SINGLE_QUOTE_STRING"):
            value = prompt.value.strip("\"'")
            prompt = LiteralExpression(value=value)

        context = None
        options = {}

        # Process context and options from other args
        for key, value in args.items():
            if key == "arg0":
                # Skip prompt, handled above
                continue
            elif key == "context":
                # Handle context special case
                if isinstance(value, Identifier):
                    context = [value]
                elif isinstance(value, list):
                    context = value
                elif hasattr(value, "value") and isinstance(value.value, list):
                    # Handle array literal
                    context = value.value
            else:
                # Other options
                options[key] = value

        # If options is empty, set it to None
        if not options:
            options = None

        # Create and return a ReasonStatement instead of a FunctionCall
        return ReasonStatement(prompt=prompt, target=None, context=context, options=options)  # type: ignore

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

    def reason_statement(self, items):
        """Transform a reason statement rule into a ReasonStatement node."""
        # Filter out None values
        items = [item for item in items if item is not None]

        # Check if we have a target variable
        if items and isinstance(items[0], Identifier):
            target = items[0]
            # Get the prompt from the next item
            prompt = items[1] if len(items) > 1 else LiteralExpression(value="")
            rest = items[2:]
        else:
            target = None
            # Get the prompt from the first item
            prompt = items[0] if items else LiteralExpression(value="")
            rest = items[1:]

        # Make sure we have a valid prompt
        if prompt is None:
            prompt = LiteralExpression(value="")
        elif isinstance(prompt, Token):
            # Convert token to LiteralExpression
            value = (
                prompt.value.strip("\"'") if prompt.type in ("STRING", "DOUBLE_QUOTE_STRING", "SINGLE_QUOTE_STRING") else str(prompt.value)
            )
            prompt = LiteralExpression(value=value)

        # Process optional context and options
        context = None
        options = {}

        # Process named arguments
        for item in rest:
            if isinstance(item, tuple):
                # Named argument
                arg_name, arg_value = item
                if arg_name == "context":
                    # Handle context special case
                    if isinstance(arg_value, Identifier):
                        context = [arg_value]
                    elif isinstance(arg_value, list):
                        context = arg_value
                    elif hasattr(arg_value, "value") and isinstance(arg_value.value, list):
                        # Handle array literal
                        context = arg_value.value
                else:
                    # Other options
                    options[arg_name] = arg_value
            elif isinstance(item, list):
                # List of named arguments
                for sub_item in item:
                    if isinstance(sub_item, tuple):
                        arg_name, arg_value = sub_item
                        if arg_name == "context":
                            # Handle context special case
                            if isinstance(arg_value, Identifier):
                                context = [arg_value]
                            elif isinstance(arg_value, list):
                                context = arg_value
                            elif hasattr(arg_value, "value") and isinstance(arg_value.value, list):
                                # Handle array literal
                                context = arg_value.value
                        else:
                            # Other options
                            options[arg_name] = arg_value

        # If options is empty, set it to None
        if not options:
            options = None

        return ReasonStatement(prompt=prompt, target=target, context=context, options=options)

    def context_arg(self, items):
        """Transform a context argument into a list of identifiers."""
        if len(items) == 1 and isinstance(items[0], list):
            return items[0]  # Already a list of identifiers
        elif len(items) == 1 and isinstance(items[0], Identifier):
            return [items[0]]  # Single identifier
        return []  # Empty context

    def identifier_list(self, items):
        """Transform an identifier list into a list."""
        return items

    def identifier(self, items):
        """Transform an identifier rule into an Identifier node."""
        # Convert all items to strings
        parts = []
        for item in items:
            if isinstance(item, Token):
                parts.append(item.value)

        # If no scope prefix and not a function name, add local
        if parts[0] not in RuntimeScopes.ALL + ["reason2", "reason", "log", "print"]:
            # Only add local scope if it's a simple name
            if len(parts) == 1:
                parts = self._insert_local_scope(parts)
            else:
                # For nested identifiers, keep as is
                pass

        # Join all parts with dots
        name = ".".join(parts)
        return Identifier(name=name)

    def program(self, items):
        """Transform a program rule into a list of statements."""
        # Filter out None items and NEWLINE tokens
        statements = [item for item in items if item is not None and not isinstance(item, Token)]
        return statements
