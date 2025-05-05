"""Parser for DANA language."""

import re
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

from opendxa.dana.exceptions import ParseError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    FStringExpression,
    FunctionCall,
    Identifier,
    Literal,
    LiteralExpression,
    LogLevel,
    LogLevelSetStatement,
    LogStatement,
    Program,
    ReasonStatement,
    WhileLoop,
)
from opendxa.dana.language.types import validate_identifier


class ParseResult(NamedTuple):
    """Result of parsing a DANA program."""

    program: Program
    errors: List[ParseError] = []

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful (no errors)."""
        return len(self.errors) == 0

    @property
    def error(self) -> Optional[ParseError]:
        """Get the first error if any exist, for backward compatibility."""
        return self.errors[0] if self.errors else None


# Regex patterns for different statement types
# Allow nested identifiers like scope.sub.var and end-of-line comments
# Changed assignment regex to not be greedy and to be more specific about what it captures on the right side
ASSIGNMENT_REGEX = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*=\s*([^#]+?)(?:\s*#.*)?$")
# Updated Log Regex to capture content inside parentheses and optional level
LOG_REGEX = re.compile(r"^\s*log(?:\.(debug|info|warn|error))?\((.*)\)\s*(?:#.*)?$")
# Make LogLevelSet regex less strict to capture any string in quotes, validation happens later
LOG_LEVEL_SET_REGEX = re.compile(r"^\s*log\.setLevel\(\s*\"([^\"]*)\"\s*\)\s*(?:#.*)?$")
IF_REGEX = re.compile(r"^\s*if\s+(.*):\s*(?:#.*)?$")
WHILE_REGEX = re.compile(r"^\s*while\s+(.*):\s*(?:#.*)?$")
FUNCTION_CALL_REGEX = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\((.*)\)\s*(?:#.*)?$")
# Reason regex to capture variable assignment, prompt, and optional context and parameters
REASON_REGEX = re.compile(r"^\s*(?:([a-zA-Z_][a-zA-Z0-9_\.]*)\s*=\s*)?reason\s*\(\s*(.*?)(?:\s*,\s*context\s*=\s*(\[[^\]]*\]|\{[^\}]*\}|[a-zA-Z_][a-zA-Z0-9_\.]*))?\s*(?:\s*,\s*([^\)]*))?\s*\)\s*(?:#.*)?$")


def parse_literal(value_str: str) -> Literal:
    """Parse a string into a Literal value."""
    value_str = value_str.strip()

    # Check for boolean values
    if value_str.lower() == "true":
        return Literal(value=True)
    if value_str.lower() == "false":
        return Literal(value=False)

    # Check for float values
    if "." in value_str and value_str.replace(".", "", 1).isdigit():
        return Literal(value=float(value_str))

    # Check for integers
    if value_str.isdigit() or (value_str.startswith("-") and value_str[1:].isdigit()):
        return Literal(value=int(value_str))

    # Check for quoted strings
    if value_str.startswith('"') and value_str.endswith('"'):
        # Check if it's an f-string
        if value_str.startswith('f"') or value_str.startswith("f'"):
            # Remove the f and quotes
            content = value_str[2:-1]
            parts = []
            current_pos = 0
            while current_pos < len(content):
                # Find the next {
                brace_start = content.find("{", current_pos)
                if brace_start == -1:
                    # No more expressions, add remaining text
                    parts.append(content[current_pos:])
                    break

                # Add text before the {
                if brace_start > current_pos:
                    parts.append(content[current_pos:brace_start])

                # Find the matching }
                brace_level = 1
                brace_end = brace_start + 1
                while brace_end < len(content) and brace_level > 0:
                    if content[brace_end] == "{":
                        brace_level += 1
                    elif content[brace_end] == "}":
                        brace_level -= 1
                    brace_end += 1

                if brace_level > 0:
                    raise ParseError("Unmatched { in f-string")

                # Parse the expression inside {}
                expr_str = content[brace_start + 1 : brace_end - 1]
                try:
                    expr = parse_expression(expr_str)
                    parts.append(expr)
                except ParseError as e:
                    raise ParseError("Invalid expression in f-string") from e

                current_pos = brace_end

            return Literal(value=FStringExpression(parts=parts))

        # Regular string
        return Literal(value=value_str[1:-1])

    raise ParseError(f"Invalid literal value: '{value_str}'")


def tokenize_expression(expr_str: str) -> List[str]:
    """Split an expression into tokens while preserving operators, parentheses, and string literals."""
    tokens = []
    pos = 0
    n = len(expr_str)
    operators = {"+", "-", "*", "/", "<", ">", "=", "!", "%"}  # All possible operator characters
    whitespace = re.compile(r"\s+")

    while pos < n:
        # Skip whitespace
        match = whitespace.match(expr_str, pos)
        if match:
            pos = match.end()
            continue

        char = expr_str[pos]

        # String literals
        if char == '"':
            start = pos
            pos += 1
            while pos < n and expr_str[pos] != '"':
                # TODO: Handle escape characters if needed later
                pos += 1
            if pos < n and expr_str[pos] == '"':
                pos += 1
                tokens.append(expr_str[start:pos])
            else:
                raise ParseError(f"Unterminated string literal starting at position {start}")
            continue

        # Check for negative numbers
        if char == "-" and pos + 1 < n and expr_str[pos + 1].isdigit():
            # This is a negative number
            start = pos
            pos += 1  # Skip the minus sign
            while pos < n and (expr_str[pos].isdigit() or expr_str[pos] == "."):
                pos += 1
            tokens.append(expr_str[start:pos])
            continue

        # Operators and Parentheses
        if char in operators or char in "()":
            # Check for multi-character operators like <=, >=, ==, !=
            if pos + 1 < n:
                if char == '<' and expr_str[pos + 1] == '=':
                    tokens.append("<=")
                    pos += 2
                    continue
                elif char == '>' and expr_str[pos + 1] == '=':
                    tokens.append(">=")
                    pos += 2
                    continue
                elif char == '=' and expr_str[pos + 1] == '=':
                    tokens.append("==")
                    pos += 2
                    continue
                elif char == '!' and expr_str[pos + 1] == '=':
                    tokens.append("!=")
                    pos += 2
                    continue
            
            # Single character operators
            tokens.append(char)
            pos += 1
            continue

        # Numbers (int/float) or Identifiers
        start = pos
        while pos < n and not expr_str[pos].isspace() and expr_str[pos] not in operators and expr_str[pos] not in '()"':
            pos += 1
        tokens.append(expr_str[start:pos])

    return tokens


def parse_expression(expr_str: str) -> Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]:
    """Parse an expression string into an Expression node."""
    expr_str = expr_str.strip()
    if not expr_str:
        raise ParseError("Empty expression")

    # Check for f-string
    if expr_str.startswith('f"') or expr_str.startswith("f'"):
        # Parse as f-string
        content = expr_str[2:-1]  # Remove f" and "
        parts = []
        current_pos = 0
        while current_pos < len(content):
            # Find the next {
            brace_start = content.find("{", current_pos)
            if brace_start == -1:
                # No more expressions, add remaining text
                if current_pos < len(content):
                    parts.append(content[current_pos:])
                break

            # Add text before the {
            if brace_start > current_pos:
                parts.append(content[current_pos:brace_start])

            # Find the matching }
            brace_level = 1
            brace_end = brace_start + 1
            while brace_end < len(content) and brace_level > 0:
                if content[brace_end] == "{":
                    brace_level += 1
                elif content[brace_end] == "}":
                    brace_level -= 1
                brace_end += 1

            if brace_level > 0:
                raise ParseError("Unmatched { in f-string")

            # Parse the expression inside {}
            expr_str = content[brace_start + 1 : brace_end - 1]
            try:
                expr = parse_expression(expr_str)
                parts.append(expr)
            except ParseError as e:
                raise ParseError("Invalid expression in f-string") from e

            current_pos = brace_end

        return LiteralExpression(literal=Literal(value=FStringExpression(parts=parts)))

    # Operator precedence mapping
    operators = {"*": BinaryOperator.MULTIPLY, "/": BinaryOperator.DIVIDE, "+": BinaryOperator.ADD, "-": BinaryOperator.SUBTRACT}

    tokens = tokenize_expression(expr_str)

    def evaluate(tokens: List[str]) -> Union[LiteralExpression, Identifier, BinaryExpression, FunctionCall]:
        if not tokens:
            raise ParseError("Empty expression")

        # Handle parentheses first
        if len(tokens) >= 2 and tokens[0] == "(" and tokens[-1] == ")":
            inner_tokens = tokens[1:-1]
            if not inner_tokens:
                raise ParseError("Empty parentheses")
            return evaluate(inner_tokens)

        if len(tokens) == 1:
            return parse_simple_expression(tokens[0])

        # Find the operator with lowest precedence outside parentheses
        # Define all operators and their precedence
        all_operators = {
            # Arithmetic operators (higher precedence)
            "*": 3, "/": 3, "%": 3,
            "+": 2, "-": 2,
            # Comparison operators (lowest precedence)
            "<": 1, ">": 1, "<=": 1, ">=": 1, "==": 1, "!=": 1,
            # Logical operators
            "and": 0, "or": 0
        }
        
        lowest_prec = float("inf")
        lowest_idx = -1
        paren_level = 0

        for i, token in enumerate(tokens):
            if token == "(":
                paren_level += 1
            elif token == ")":
                paren_level -= 1
            elif token in all_operators and paren_level == 0:
                prec = all_operators[token]
                # For equal precedence, prefer leftmost (left-to-right associativity)
                if prec <= lowest_prec:
                    lowest_prec = prec
                    lowest_idx = i

        if lowest_idx == -1:
            return parse_simple_expression(tokens[0])

        # Split at the operator and evaluate both sides
        left = evaluate(tokens[:lowest_idx])
        right = evaluate(tokens[lowest_idx + 1:])
        
        # Map operators to BinaryOperator enum values
        operator_map = {
            "+": BinaryOperator.ADD,
            "-": BinaryOperator.SUBTRACT,
            "*": BinaryOperator.MULTIPLY,
            "/": BinaryOperator.DIVIDE,
            "%": BinaryOperator.MODULO,  # Add modulo operator
            "<": BinaryOperator.LESS_THAN,
            ">": BinaryOperator.GREATER_THAN,
            "<=": BinaryOperator.LESS_EQUALS,
            ">=": BinaryOperator.GREATER_EQUALS,
            "==": BinaryOperator.EQUALS,
            "!=": BinaryOperator.NOT_EQUALS,
            "and": BinaryOperator.AND,
            "or": BinaryOperator.OR
        }
        
        # Get the operator
        op = tokens[lowest_idx]
        binary_op = operator_map.get(op)
        
        if not binary_op:
            raise ParseError(f"Unsupported operator: {op}")
        
        return BinaryExpression(left=left, operator=binary_op, right=right)

    return evaluate(tokens)


def parse_simple_expression(expr_str: str) -> Union[LiteralExpression, Identifier]:
    """Parse a simple expression (literal or identifier)."""
    expr_str = expr_str.strip()

    # Try parsing as a literal
    try:
        return LiteralExpression(literal=parse_literal(expr_str))
    except ParseError as e:
        # If not a literal, try as identifier
        if validate_identifier(expr_str):
            return Identifier(name=expr_str)
        # Pass original error message but add context if needed
        raise ParseError(f"Invalid expression part: '{expr_str}'") from e


def parse_reason_context(context_str: str) -> List[Identifier]:
    """Parse the context argument of a reason statement.
    
    Args:
        context_str: The context string from the reason statement.
        
    Returns:
        A list of Identifier AST nodes representing context variables.
    """
    context = []
    if not context_str:
        return context
        
    # Strip whitespace
    context_str = context_str.strip()
    
    # Handle list format [var1, var2, ...]
    if context_str.startswith('[') and context_str.endswith(']'):
        items = context_str[1:-1].split(',')
        for item in items:
            item = item.strip()
            if item and validate_identifier(item):
                context.append(Identifier(name=item))
    # Handle single variable or scope references
    elif validate_identifier(context_str):
        context.append(Identifier(name=context_str))
    
    return context


def parse_reason_options(options_str: str) -> Dict[str, Any]:
    """Parse the options from a reason statement.
    
    Args:
        options_str: The options string from the reason statement.
        
    Returns:
        A dictionary of options for the reasoning call.
    """
    options = {}
    if not options_str:
        return options
        
    # Split options by commas
    params = options_str.split(',')
    for param in params:
        param = param.strip()
        if '=' in param:
            key, value = param.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Parse the value based on its format
            if value.lower() in ('true', 'false'):
                options[key] = value.lower() == 'true'
            elif value.isdigit():
                options[key] = int(value)
            elif value.replace('.', '', 1).isdigit():
                options[key] = float(value)
            elif (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                options[key] = value[1:-1]
            else:
                # Just store as string for runtime evaluation
                options[key] = value
    
    return options


def parse_statement(
    line: str, line_num: int
) -> Tuple[Optional[Union[Assignment, LogStatement, Conditional, WhileLoop, LogLevelSetStatement, ReasonStatement, FunctionCall]], Optional[ParseError]]:
    """Parse a single line into a Statement or error."""
    line_content = line  # Store original line content

    # Strip comments from the line
    if "#" in line:
        line = line[: line.index("#")].rstrip()

    line = line.strip()
    if not line:
        return None, None

    # Try matching reason statement
    reason_match = REASON_REGEX.match(line)
    if reason_match:
        variable_name, prompt_str, context_str, options_str = reason_match.groups()
        
        try:
            # Parse prompt expression
            prompt = parse_expression(prompt_str.strip())
            
            # Parse target (optional)
            target = None
            if variable_name:
                if not validate_identifier(variable_name):
                    return None, ParseError(f"Invalid target identifier: '{variable_name}'", line_num, line_content)
                target = Identifier(name=variable_name)
            
            # Parse context (optional)
            context = None
            if context_str:
                context = parse_reason_context(context_str)
            
            # Parse options (optional)
            options = None
            if options_str:
                options = parse_reason_options(options_str)
                
            # Create and return the ReasonStatement
            return ReasonStatement(prompt=prompt, target=target, context=context, options=options), None
        except ParseError as e:
            return None, ParseError(f"Error in reason statement: {str(e)}", line_num, line_content)
        except Exception as e:
            return None, ParseError(f"Unexpected error in reason statement: {str(e)}", line_num, line_content)
    
    # Try matching log level set statement
    log_level_set_match = LOG_LEVEL_SET_REGEX.match(line)
    if log_level_set_match:
        level_str = log_level_set_match.group(1)
        try:
            level = LogLevel[level_str.upper()]
            return LogLevelSetStatement(level=level), None
        except KeyError:
            # Correctly report invalid log level if validation fails
            return None, ParseError(f"Invalid log level: '{level_str}'", line_num, line_content)

    # Try matching log statement (updated logic)
    log_match = LOG_REGEX.match(line)
    if log_match:
        level_str, message_expr_str = log_match.groups()
        message_expr_str = message_expr_str.strip()
        if not message_expr_str:
            return None, ParseError("Log statement cannot have empty message", line_num, line_content)
        try:
            # Find the position of the identifier in the f-string
            if message_expr_str.startswith('f"') or message_expr_str.startswith("f'"):
                # Parse as f-string
                content = message_expr_str[2:-1]  # Remove f" and "
                brace_start = content.find("{")
                if brace_start != -1:
                    # Find the matching }
                    brace_level = 1
                    brace_end = brace_start + 1
                    while brace_end < len(content) and brace_level > 0:
                        if content[brace_end] == "{":
                            brace_level += 1
                        elif content[brace_end] == "}":
                            brace_level -= 1
                        brace_end += 1

                    if brace_level > 0:
                        raise ParseError("Unmatched { in f-string")

                    # Extract the identifier
                    identifier = content[brace_start + 1 : brace_end - 1].strip()
                    # Calculate the column position (add 4 for 'log(' and 2 for 'f"')
                    column = line.find(message_expr_str) + 4 + 2 + brace_start + 1

                    # Create location information for the identifier
                    location = (line_num, column, line_content)

                    # Parse the expression with location information
                    message_expr = parse_expression(message_expr_str)
                    if isinstance(message_expr, LiteralExpression) and isinstance(message_expr.literal.value, FStringExpression):
                        for part in message_expr.literal.value.parts:
                            if isinstance(part, Identifier) and part.name == identifier:
                                part.location = location

            else:
                message_expr = parse_expression(message_expr_str)

            level = LogLevel[level_str.upper()] if level_str else LogLevel.INFO  # Default to INFO
            return LogStatement(message=message_expr, level=level), None
        except ParseError as e:
            # Add line info to the expression parsing error
            return None, ParseError(str(e), line_num, line_content)

    # Try matching if statement
    if_match = IF_REGEX.match(line)
    if if_match:
        condition_str = if_match.group(1)
        try:
            condition = parse_expression(condition_str)
            return Conditional(condition=condition, body=[], line_num=line_num), None
        except ParseError as e:
            # Add line info to the expression parsing error
            return None, ParseError(str(e), line_num, line_content)

    # Try matching while statement
    while_match = WHILE_REGEX.match(line)
    if while_match:
        condition_str = while_match.group(1)
        try:
            # Parse the expression, this now properly handles binary operators
            condition = parse_expression(condition_str)
            return WhileLoop(condition=condition, body=[], line_num=line_num), None
        except ParseError as e:
            # Add line info to the expression parsing error
            return None, ParseError(str(e), line_num, line_content)

    # Try matching assignment
    assign_match = ASSIGNMENT_REGEX.match(line)
    if assign_match:
        target_str, value_str = assign_match.groups()

        if not validate_identifier(target_str):
            return None, ParseError(f"Invalid target identifier format '{target_str}'", line_num, line_content)

        # Check if the value is a function call
        value_str = value_str.strip()
        function_call_match = re.match(r"([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\((.*)\)\s*$", value_str)
        
        if function_call_match:
            # This is a function call in an assignment, parse it as such
            function_name, args_str = function_call_match.groups()
            
            try:
                # Parse function arguments
                args = {}
                if args_str.strip():
                    # Split by commas, but handle nested parentheses
                    depth = 0
                    start = 0
                    arg_parts = []
                    
                    for i, char in enumerate(args_str):
                        if char == '(' or char == '[' or char == '{':
                            depth += 1
                        elif char == ')' or char == ']' or char == '}':
                            depth -= 1
                        elif char == ',' and depth == 0:
                            arg_parts.append(args_str[start:i])
                            start = i + 1
                    
                    # Add the last part
                    if start <= len(args_str):
                        arg_parts.append(args_str[start:])
                    
                    # Process each argument
                    for arg in arg_parts:
                        arg = arg.strip()
                        if '=' in arg:
                            key, val_str = arg.split('=', 1)
                            key = key.strip()
                            val_str = val_str.strip()
                            if val_str:
                                val = parse_expression(val_str)
                                args[key] = val
                
                # Create the function call
                func_call = FunctionCall(name=function_name, args=args)
                
                # Return the assignment with the function call as its value
                return Assignment(target=Identifier(name=target_str), value=func_call), None
            except ParseError as e:
                # Add line info to the expression parsing error
                return None, ParseError(f"Error in function call: {str(e)}", line_num, line_content)
            except Exception as e:
                # Add line info to any other error
                return None, ParseError(f"Unexpected error in function call: {str(e)}", line_num, line_content)
        else:
            # Regular expression value
            try:
                value = parse_expression(value_str)  # Already stripped
                return Assignment(target=Identifier(name=target_str), value=value), None
            except ParseError as e:
                # Add line info to the expression parsing error
                return None, ParseError(str(e), line_num, line_content)

    # Try matching function call
    function_call_match = FUNCTION_CALL_REGEX.match(line)
    if function_call_match:
        function_name, args_str = function_call_match.groups()
        
        try:
            # Parse function arguments
            args = {}
            if args_str.strip():
                # Split by commas, but handle nested parentheses
                depth = 0
                start = 0
                arg_parts = []
                
                for i, char in enumerate(args_str):
                    if char == '(' or char == '[' or char == '{':
                        depth += 1
                    elif char == ')' or char == ']' or char == '}':
                        depth -= 1
                    elif char == ',' and depth == 0:
                        arg_parts.append(args_str[start:i])
                        start = i + 1
                
                # Add the last part
                if start <= len(args_str):
                    arg_parts.append(args_str[start:])
                
                # Process each argument
                for arg in arg_parts:
                    arg = arg.strip()
                    if '=' in arg:
                        key, value_str = arg.split('=', 1)
                        key = key.strip()
                        value_str = value_str.strip()
                        if value_str:
                            value = parse_expression(value_str)
                            args[key] = value
            
            return FunctionCall(name=function_name, args=args), None
        except ParseError as e:
            # Add line info to the expression parsing error
            return None, ParseError(f"Error in function call: {str(e)}", line_num, line_content)
        except Exception as e:
            # Add line info to any other error
            return None, ParseError(f"Unexpected error in function call: {str(e)}", line_num, line_content)

    # General invalid syntax if nothing matched
    return None, ParseError("Invalid syntax", line_num, line_content)


def parse(code: str) -> ParseResult:
    """Parse a DANA program string into an AST."""
    statements: List[Union[Assignment, LogStatement, Conditional, LogLevelSetStatement, ReasonStatement, WhileLoop, FunctionCall]] = []
    errors: List[ParseError] = []
    lines = code.splitlines()
    # Use a stack to track nested conditionals
    conditional_stack: List[Conditional] = []
    first_error_line = None
    
    # Calculate indentation level for each line
    indented_lines = []
    for line_num, line in enumerate(lines, 1):
        if not line.strip() or line.strip().startswith("#"):
            continue  # Skip empty lines and comments
        
        # Count leading whitespace to determine indentation level
        indent = len(line) - len(line.lstrip())
        indented_lines.append((line_num, line, indent))
    
    for line_num, line, indent in indented_lines:
        statement, error = parse_statement(line, line_num)
        if error:
            errors.append(error)
            if first_error_line is None:
                first_error_line = line_num
            continue  # Skip this line but continue parsing

        # Only add statements that come before the first error
        if first_error_line is None or line_num < first_error_line:
            if statement:
                # Check if we need to pop conditionals based on indentation
                while conditional_stack and indent <= conditional_stack[-1][1]:
                    # Pop the current conditional
                    conditional_stack.pop()
                
                # Get the current conditional if we have one
                current_conditional = conditional_stack[-1][0] if conditional_stack else None
                
                if current_conditional:
                    # We're inside a conditional block
                    if isinstance(statement, (Conditional, WhileLoop)):
                        # This is a nested block structure
                        current_conditional.body.append(statement)
                        # Push this block onto the stack with its indentation
                        conditional_stack.append((statement, indent))
                    else:
                        # This is a regular statement inside a conditional
                        current_conditional.body.append(statement)
                else:
                    # We're at the top level
                    if isinstance(statement, (Conditional, WhileLoop)):
                        # This is a new top-level block structure
                        conditional_stack.append((statement, indent))
                        statements.append(statement)
                    else:
                        # This is a regular top-level statement
                        statements.append(statement)

    # All conditionals should be properly added to statements already

    return ParseResult(program=Program(statements=statements), errors=errors)
