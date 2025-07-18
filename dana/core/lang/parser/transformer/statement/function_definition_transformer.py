"""
Function definition transformer for Dana language parsing.

This module handles all function definition transformations, including:
- Function definitions (def statements)
- Decorators (@decorator syntax)
- Parameters and type hints
- Struct definitions (function-like definitions)

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from lark import Token, Tree

from dana.core.lang.ast import (
    AgentDefinition,
    AgentField,
    Decorator,
    FunctionDefinition,
    Identifier,
    Parameter,
    StructDefinition,
    StructField,
    TypeHint,
)
from dana.core.lang.parser.transformer.base_transformer import BaseTransformer


class FunctionDefinitionTransformer(BaseTransformer):
    """
    Handles function definition transformations for the Dana language.
    Converts function definition parse trees into corresponding AST nodes.
    """

    def __init__(self, main_transformer):
        """Initialize with reference to main transformer for shared utilities."""
        super().__init__()
        self.main_transformer = main_transformer
        self.expression_transformer = main_transformer.expression_transformer

    # === Function Definition ===

    def function_def(self, items):
        """Transform a function definition rule into a FunctionDefinition node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        if len(relevant_items) < 2:
            raise ValueError(f"Function definition must have at least a name and body, got {len(relevant_items)} items")

        # Extract decorators (if present) and function name
        decorators, func_name_token, current_index = self._extract_decorators_and_name(relevant_items)

        # Resolve parameters using simplified logic
        parameters, current_index = self._resolve_function_parameters(relevant_items, current_index)

        # Extract return type
        return_type, current_index = self._extract_return_type(relevant_items, current_index)

        # Extract function body
        block_items = self._extract_function_body(relevant_items, current_index)

        # Handle function name extraction
        if isinstance(func_name_token, Token) and func_name_token.type == "NAME":
            func_name = func_name_token.value
        else:
            raise ValueError(f"Expected function name token, got {func_name_token}")

        location = self.main_transformer.create_location(func_name_token)

        return FunctionDefinition(
            name=Identifier(name=func_name, location=location),
            parameters=parameters,
            body=block_items,
            return_type=return_type,
            decorators=decorators,
            location=location,
        )

    def _extract_decorators_and_name(self, relevant_items):
        """Extract decorators and function name from relevant items."""
        current_index = 0
        decorators = []

        # Check if the first item is decorators
        if current_index < len(relevant_items) and isinstance(relevant_items[current_index], list):
            first_item = relevant_items[current_index]
            if first_item and hasattr(first_item[0], "name"):  # Check if it's a list of Decorator objects
                decorators = first_item
                current_index += 1

        # The next item should be the function name
        if current_index >= len(relevant_items):
            raise ValueError("Expected function name after decorators")

        func_name_token = relevant_items[current_index]
        current_index += 1

        return decorators, func_name_token, current_index

    def _resolve_function_parameters(self, relevant_items, current_index):
        """Resolve function parameters from relevant items."""
        parameters = []

        if current_index < len(relevant_items):
            item = relevant_items[current_index]

            if isinstance(item, list):
                # Check if already transformed Parameter objects
                if item and hasattr(item[0], "name") and hasattr(item[0], "type_hint"):
                    parameters = item
                # Check if it's a list of Identifier objects (for test compatibility)
                elif item and isinstance(item[0], Identifier):
                    # Convert Identifier objects to Parameter objects
                    parameters = [Parameter(name=identifier.name) for identifier in item]
                else:
                    parameters = self._transform_parameters(item)
                current_index += 1
            elif isinstance(item, Tree) and item.data == "parameters":
                parameters = self.parameters(item.children)
                current_index += 1

        return parameters, current_index

    def _extract_return_type(self, relevant_items, current_index):
        """Extract return type from relevant items."""
        return_type = None

        if current_index < len(relevant_items):
            item = relevant_items[current_index]

            if not isinstance(item, list):
                from dana.core.lang.ast import TypeHint

                if isinstance(item, Tree) and item.data == "basic_type":
                    return_type = self.main_transformer.assignment_transformer.basic_type(item.children)
                    current_index += 1
                elif isinstance(item, TypeHint):
                    return_type = item
                    current_index += 1

        return return_type, current_index

    def _extract_function_body(self, relevant_items, current_index):
        """Extract function body from relevant items."""
        block_items = []

        if current_index < len(relevant_items):
            block_tree = relevant_items[current_index]
            if isinstance(block_tree, Tree) and block_tree.data == "block":
                block_items = self.main_transformer._transform_block(block_tree.children)
            elif isinstance(block_tree, list):
                block_items = self.main_transformer._transform_block(block_tree)

        return block_items

    # === Decorators ===

    def decorators(self, items):
        """Transform decorators rule into a list of Decorator nodes."""
        return [self._transform_decorator(item) for item in items if item is not None]

    def decorator(self, items):
        """Transform decorator rule into a Decorator node."""
        return self._transform_decorator_from_items(items)

    def _transform_decorators(self, decorators_tree):
        """Helper to transform a 'decorators' Tree into a list of Decorator nodes."""
        if not decorators_tree:
            return []
        if hasattr(decorators_tree, "children"):
            return [self._transform_decorator(d) for d in decorators_tree.children]
        return [self._transform_decorator(decorators_tree)]

    def _transform_decorator(self, decorator_tree):
        """Transforms a 'decorator' Tree into a Decorator node."""
        if isinstance(decorator_tree, Decorator):
            return decorator_tree
        return self._transform_decorator_from_items(decorator_tree.children)

    def _transform_decorator_from_items(self, items):
        """Creates a Decorator from a list of items (name, args, kwargs)."""
        if len(items) < 2:
            raise ValueError(f"Expected at least 2 items for decorator (AT and NAME), got {len(items)}: {items}")

        # Skip the AT token and get the NAME token
        name_token = items[1]  # Changed from items[0] to items[1]
        decorator_name = name_token.value
        args, kwargs = self._parse_decorator_arguments(items[2]) if len(items) > 2 else ([], {})

        return Decorator(
            name=decorator_name,
            args=args,
            kwargs=kwargs,
            location=self.main_transformer.create_location(name_token),
        )

    def _parse_decorator_arguments(self, arguments_tree):
        """Parses arguments from a decorator's argument list tree."""
        args = []
        kwargs = {}

        if not arguments_tree:
            return args, kwargs

        # If it's not a tree, just return empty
        if not hasattr(arguments_tree, "children"):
            return args, kwargs

        for arg in arguments_tree.children:
            if hasattr(arg, "data") and arg.data == "kw_arg":
                key = arg.children[0].value
                value = self.expression_transformer.expression([arg.children[1]])
                kwargs[key] = value
            else:
                args.append(self.expression_transformer.expression([arg]))
        return args, kwargs

    # === Parameters ===

    def _transform_parameters(self, parameters_tree):
        """Transform parameters tree into list of Parameter nodes."""
        if hasattr(parameters_tree, "children"):
            return [self._transform_parameter(child) for child in parameters_tree.children]
        return []

    def _transform_parameter(self, param_tree):
        """Transform a parameter tree into a Parameter node."""
        # This is a simplification; a real implementation would handle types, defaults, etc.
        if hasattr(param_tree, "children") and param_tree.children:
            # For now, assuming a simple structure
            name_token = param_tree.children[0]
            return Parameter(name=name_token.value, location=self.main_transformer.create_location(name_token))
        return Parameter(name=str(param_tree), location=None)

    def parameters(self, items):
        """Transform parameters rule into a list of Parameter objects.

        Grammar: parameters: typed_parameter ("," typed_parameter)*
        """
        result = []
        for item in items:
            if isinstance(item, Parameter):
                # Already a Parameter object from typed_parameter
                result.append(item)
            elif isinstance(item, Identifier):
                # Convert Identifier to Parameter
                param_name = item.name if "." in item.name else f"local:{item.name}"
                result.append(Parameter(name=param_name))
            elif hasattr(item, "data") and item.data == "typed_parameter":
                # Handle typed_parameter via the typed_parameter method
                param = self.main_transformer.assignment_transformer.typed_parameter(item.children)
                result.append(param)
            elif hasattr(item, "data") and item.data == "parameter":
                # Handle old-style parameter via the parameter method
                param = self.parameter(item.children)
                # Convert Identifier to Parameter
                if isinstance(param, Identifier):
                    result.append(Parameter(name=param.name))
                else:
                    result.append(param)
            else:
                # Handle unexpected item
                self.warning(f"Unexpected parameter item: {item}")
        return result

    def parameter(self, items):
        """Transform a parameter rule into an Identifier object.

        Grammar: parameter: NAME ["=" expr]
        Note: Default values are handled at runtime, not during parsing.
        """
        # Extract name from the first item (NAME token)
        if len(items) > 0:
            name_item = items[0]
            if hasattr(name_item, "value"):
                param_name = name_item.value
            else:
                param_name = str(name_item)

            # Create an Identifier with the proper local scope
            return Identifier(name=f"local:{param_name}")

        # Fallback
        return Identifier(name="local:param")

    # === Struct Definitions ===

    def struct_definition(self, items):
        """Transform a struct definition rule into a StructDefinition node."""
        name_token = items[0]
        # items are [NAME, optional COMMENT, struct_block]
        struct_block = items[2] if len(items) > 2 else items[1]

        fields = []
        if hasattr(struct_block, "data") and struct_block.data == "struct_block":
            # The children of struct_block are NL, INDENT, struct_fields, DEDENT...
            # The struct_fields tree is what we want
            struct_fields_tree = None
            for child in struct_block.children:
                if hasattr(child, "data") and child.data == "struct_fields":
                    struct_fields_tree = child
                    break

            if struct_fields_tree:
                fields = [child for child in struct_fields_tree.children if isinstance(child, StructField)]

        return StructDefinition(name=name_token.value, fields=fields)

    def struct_field(self, items):
        """Transform a struct field rule into a StructField node."""

        name_token = items[0]
        type_hint_node = items[1]

        field_name = name_token.value

        # The type_hint_node should already be a TypeHint object
        # from the 'basic_type' rule transformation.
        if not isinstance(type_hint_node, TypeHint):
            # Fallback if it's a token
            if isinstance(type_hint_node, Token):
                type_hint = TypeHint(name=type_hint_node.value)
            else:
                # This would be an unexpected state
                raise TypeError(f"Unexpected type for type_hint_node: {type(type_hint_node)}")
        else:
            type_hint = type_hint_node

        # Handle optional default value
        default_value = None
        if len(items) > 2:
            # We have a default value expression
            default_value = self.main_transformer.expression_transformer.transform(items[2])

        return StructField(name=field_name, type_hint=type_hint, default_value=default_value)

        # === Agent Definitions ===

    def agent_definition(self, items):
        """Transform an agent definition rule into an AgentDefinition node."""
        name_token = items[0]
        # items are [NAME, optional COMMENT, agent_block]
        agent_block = items[2] if len(items) > 2 else items[1]

        fields = []
        if hasattr(agent_block, "data") and agent_block.data == "agent_block":
            # The children of agent_block are NL, INDENT, agent_fields, DEDENT...
            # The agent_fields tree is what we want
            agent_fields_tree = None
            for child in agent_block.children:
                if hasattr(child, "data") and child.data == "agent_fields":
                    agent_fields_tree = child
                    break

            if agent_fields_tree:
                fields = [child for child in agent_fields_tree.children if isinstance(child, AgentField)]

        return AgentDefinition(name=name_token.value, fields=fields)

    def agent_field(self, items):
        """Transform an agent field rule into an AgentField node."""

        name_token = items[0]
        type_hint_node = items[1]
        default_value = None

        # Check if there's a default value (items[2] would be the default expression)
        if len(items) > 2:
            default_value = self.main_transformer.expression_transformer.transform(items[2])

        field_name = name_token.value

        # The type_hint_node should already be a TypeHint object
        # from the 'basic_type' rule transformation.
        if not isinstance(type_hint_node, TypeHint):
            # Fallback if it's a token
            if isinstance(type_hint_node, Token):
                type_hint = TypeHint(name=type_hint_node.value)
            else:
                # This would be an unexpected state
                raise TypeError(f"Unexpected type for type_hint_node: {type(type_hint_node)}")
        else:
            type_hint = type_hint_node

        return AgentField(name=field_name, type_hint=type_hint, default_value=default_value)