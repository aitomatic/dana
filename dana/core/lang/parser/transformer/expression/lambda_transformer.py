"""Transformer for lambda expressions."""

from lark import Token, Tree

from dana.core.lang.ast import LambdaExpression, Parameter, TypeHint
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer
from dana.core.lang.type_system.constants import COMMON_TYPE_NAMES


class LambdaTransformer(BaseTransformer):
    """Transform lambda expression parse trees into AST nodes."""

    def __init__(self, main_transformer=None):
        """Initialize the lambda transformer.

        Args:
            main_transformer: Optional main transformer instance for coordination.
        """
        super().__init__()
        self.main_transformer = main_transformer

    def lambda_expr(self, items):
        """Transform a lambda expression.

        Args:
            items: Parse tree children [receiver?, params?, body]

        Returns:
            LambdaExpression: The transformed lambda expression
        """
        receiver = None
        parameters = []
        body = None

        # Process items to extract receiver, parameters, and body
        for item in items:
            if isinstance(item, Tree):
                if item.data == "lambda_receiver":
                    receiver = self._transform_receiver(item.children)
                elif item.data == "lambda_params":
                    parameters = self._transform_parameters(item.children)
            else:
                # The last expression item is the body
                body = item

        # If we have a main transformer, use it to transform the body expression
        if self.main_transformer and hasattr(self.main_transformer, "expression_transformer"):
            if body and hasattr(body, "data"):
                # Transform the body using the expression transformer
                transformed_body = self.main_transformer.expression_transformer.transform(body)
                if transformed_body:
                    body = transformed_body

        return LambdaExpression(receiver=receiver, parameters=parameters, body=body)

    def lambda_receiver(self, items):
        """Transform a lambda receiver: (name: type).

        Args:
            items: Parse tree children [name, type]

        Returns:
            Tree: Raw receiver tree for later processing
        """
        # Return the raw tree for processing in lambda_expr
        return Tree("lambda_receiver", items)

    def lambda_params(self, items):
        """Transform lambda parameters.

        Args:
            items: Parse tree children representing parameters

        Returns:
            Tree: Raw parameters tree for later processing
        """
        # Return the raw tree for processing in lambda_expr
        return Tree("lambda_params", items)

    def _transform_receiver(self, items):
        """Transform receiver items into a Parameter.

        Args:
            items: [name_token, type_tree]

        Returns:
            Parameter: The receiver parameter
        """
        if len(items) < 2:
            return None

        name_token = items[0]
        type_tree = items[1]

        # Extract name
        name = name_token.value if isinstance(name_token, Token) else str(name_token)

        # Transform type
        type_hint = self._transform_type(type_tree)

        return Parameter(name=name, type_hint=type_hint)

    def _transform_parameters(self, items):
        """Transform parameter items into a list of Parameters.

        The grammar is: NAME [":" basic_type] ["=" expr] ("," NAME [":" basic_type] ["=" expr])*
        So the parsing logic needs to handle: name [type] [default] [, name [type] [default]]*

        Args:
            items: List of parameter tokens, types, and default values

        Returns:
            list[Parameter]: The transformed parameters
        """
        parameters = []
        i = 0

        while i < len(items):
            item = items[i]

            # Skip comma tokens
            if isinstance(item, Token) and item.type == "COMMA":
                i += 1
                continue

            # Each parameter starts with a NAME token
            if isinstance(item, Token) and item.type == "NAME":
                name = item.value
                type_hint = None
                default_value = None
                i += 1

                # Check for optional type annotation
                if i < len(items) and not isinstance(items[i], Token):
                    # It's a Tree (type annotation)
                    type_hint = self._transform_type(items[i])
                    i += 1
                elif i < len(items) and isinstance(items[i], Token) and items[i].value in COMMON_TYPE_NAMES:
                    # It's a simple type token
                    type_hint = self._transform_type(items[i])
                    i += 1

                # Check for optional default value (any non-name, non-comma expression)
                if i < len(items):
                    next_item = items[i]
                    # If it's not a comma and not a name token, it must be a default value
                    if not (isinstance(next_item, Token) and (next_item.type in ["COMMA", "NAME"])):
                        # It's a default value expression
                        if self.main_transformer and hasattr(self.main_transformer, "expression_transformer"):
                            default_value = self.main_transformer.expression_transformer.transform(next_item)
                        else:
                            default_value = next_item
                        i += 1

                parameters.append(Parameter(name=name, type_hint=type_hint, default_value=default_value))
            else:
                # Skip any unexpected items
                i += 1

        return parameters

    def _transform_type(self, type_tree):
        """Transform a type tree into a TypeHint.

        Args:
            type_tree: Parse tree representing a type

        Returns:
            TypeHint: The transformed type hint
        """
        if isinstance(type_tree, Token):
            return TypeHint(name=type_tree.value)
        elif isinstance(type_tree, Tree):
            # Handle union types and complex types
            type_name = self._extract_type_name_from_tree(type_tree)
            return TypeHint(name=type_name)

        return TypeHint(name="any")  # Fallback

    def _extract_type_name_from_tree(self, type_tree):
        """Extract type name from a complex type tree, handling union types.

        Args:
            type_tree: Parse tree representing a type

        Returns:
            str: The type name (possibly with union syntax)
        """
        if type_tree.data == "union_type":
            # Handle union types: Point | Circle | Rectangle
            union_parts = []
            for child in type_tree.children:
                if isinstance(child, Token):
                    union_parts.append(child.value)
                elif isinstance(child, Tree):
                    union_parts.append(self._extract_type_name_from_tree(child))
            return " | ".join(union_parts)

        elif type_tree.data == "single_type":
            # Handle single types
            for child in type_tree.children:
                if isinstance(child, Token):
                    return child.value
                elif isinstance(child, Tree):
                    return self._extract_type_name_from_tree(child)

        elif type_tree.data == "basic_type":
            # Handle basic types
            for child in type_tree.children:
                if isinstance(child, Token):
                    return child.value
                elif isinstance(child, Tree):
                    return self._extract_type_name_from_tree(child)

        # Fallback: concatenate all tokens
        tokens = []
        for child in type_tree.children:
            if isinstance(child, Token):
                tokens.append(child.value)

        return " ".join(tokens) if tokens else "any"
