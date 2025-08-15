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

from dana.common.exceptions import ParseError
from dana.core.lang.ast import (
    AgentDefinition,
    AgentField,
    Decorator,
    FunctionDefinition,
    Identifier,
    MethodDefinition,
    Parameter,
    ResourceDefinition,
    ResourceField,
    ResourceMethod,
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

    def method_def(self, items):
        """Transform a method definition rule into a MethodDefinition node.

        Grammar: method_def: [decorators] "def" "(" typed_parameter ")" NAME "(" [parameters] ")" ["->" basic_type] ":" [COMMENT] block
        """
        relevant_items = self.main_transformer._filter_relevant_items(items)

        if len(relevant_items) < 3:
            raise ValueError(f"Method definition must have at least receiver, name, and body, got {len(relevant_items)} items")

        current_index = 0
        decorators = []

        # Check for decorators
        if current_index < len(relevant_items) and isinstance(relevant_items[current_index], list):
            first_item = relevant_items[current_index]
            if first_item and hasattr(first_item[0], "name"):  # Check if it's a list of Decorator objects
                decorators = first_item
                current_index += 1

        # Extract receiver parameter
        receiver_param = relevant_items[current_index]
        if not isinstance(receiver_param, Parameter):
            if hasattr(receiver_param, "data") and receiver_param.data == "typed_parameter":
                receiver_param = self.main_transformer.assignment_transformer.typed_parameter(receiver_param.children)
            else:
                raise ValueError(f"Expected receiver Parameter, got {type(receiver_param)}")
        current_index += 1

        # Extract method name
        method_name_token = relevant_items[current_index]
        if not (isinstance(method_name_token, Token) and method_name_token.type == "NAME"):
            raise ValueError(f"Expected method name token, got {method_name_token}")
        method_name = method_name_token.value
        current_index += 1

        # Extract parameters (if any)
        parameters = []
        if current_index < len(relevant_items):
            # Check if the next item is a list of parameters or something else
            item = relevant_items[current_index]
            if isinstance(item, list) or (hasattr(item, "data") and item.data == "parameters"):
                parameters, current_index = self._resolve_function_parameters(relevant_items, current_index)
            elif not (isinstance(item, Tree) and item.data == "block") and not isinstance(item, TypeHint):
                # If it's not a block or type hint, try to parse it as parameters
                parameters, current_index = self._resolve_function_parameters(relevant_items, current_index)

        # Extract return type (if any)
        return_type = None
        if current_index < len(relevant_items):
            item = relevant_items[current_index]
            if isinstance(item, TypeHint) or (hasattr(item, "data") and item.data == "basic_type"):
                return_type, current_index = self._extract_return_type(relevant_items, current_index)

        # Extract method body
        block_items = self._extract_function_body(relevant_items, current_index)

        location = self.main_transformer.create_location(method_name_token)

        return MethodDefinition(
            receiver=receiver_param,
            name=Identifier(name=method_name, location=location),
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

        Grammar: parameters: typed_parameter ("," [COMMENT] typed_parameter)*
        """
        result = []
        for item in items:
            # Skip None values (from optional COMMENT tokens) and comment tokens
            if item is None:
                continue
            elif hasattr(item, "type") and item.type == "COMMENT":
                continue
            elif isinstance(item, Parameter):
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
        docstring = None

        if hasattr(struct_block, "data") and struct_block.data == "struct_block":
            # The children of struct_block are NL, INDENT, [docstring], struct_fields, DEDENT...
            for child in struct_block.children:
                if hasattr(child, "data") and child.data == "docstring":
                    # Extract docstring content
                    docstring = child.children[0].value.strip('"')
                elif hasattr(child, "data") and child.data == "struct_fields":
                    struct_fields_tree = child
                    fields = [field for field in struct_fields_tree.children if isinstance(field, StructField)]

        return StructDefinition(name=name_token.value, fields=fields, docstring=docstring)

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

        # Extract comment if present
        comment = None
        for item in items:
            if hasattr(item, "type") and item.type == "COMMENT":
                # Remove the # prefix and strip whitespace
                comment = item.value.lstrip("#").strip()
                break

        return StructField(name=field_name, type_hint=type_hint, default_value=default_value, comment=comment)

        # === Agent Definitions ===

    def agent_definition(self, items):
        """Transform an agent blueprint definition rule into an AgentDefinition node."""
        # Items may include a leading keyword token (AGENT_BLUEPRINT)
        from lark import Token, Tree

        name_token = None
        agent_block = None

        for it in items:
            if isinstance(it, Token) and it.type == "NAME" and name_token is None:
                name_token = it
            elif isinstance(it, Tree) and getattr(it, "data", None) == "agent_block":
                agent_block = it

        if name_token is None or agent_block is None:
            # Fallback to previous positional behavior
            name_token = items[0]
            agent_block = items[2] if len(items) > 2 else items[1]

        fields = []
        if hasattr(agent_block, "data") and agent_block.data == "agent_block":
            agent_fields_tree = None
            for child in agent_block.children:
                if hasattr(child, "data") and child.data == "agent_fields":
                    agent_fields_tree = child
                    break
            if agent_fields_tree:
                fields = [child for child in agent_fields_tree.children if isinstance(child, AgentField)]

        return AgentDefinition(name=name_token.value, fields=fields)

    def singleton_agent_definition(self, items):
        """Transform a singleton agent definition into a SingletonAgentDefinition node."""
        from lark import Token, Tree

        blueprint_name = None
        overrides_block = None

        for it in items:
            if isinstance(it, Token) and it.type == "NAME" and blueprint_name is None:
                # This is the blueprint name (first NAME after 'agent (')
                blueprint_name = it.value
            elif isinstance(it, Tree) and getattr(it, "data", None) == "singleton_agent_block":
                overrides_block = it

        overrides = []
        if overrides_block is not None:
            for child in overrides_block.children:
                if hasattr(child, "data") and child.data == "singleton_agent_fields":
                    for f in child.children:
                        from dana.core.lang.ast import SingletonAgentField

                        if isinstance(f, SingletonAgentField):
                            overrides.append(f)

        from dana.core.lang.ast import SingletonAgentDefinition

        assert blueprint_name is not None
        return SingletonAgentDefinition(blueprint_name=blueprint_name, overrides=overrides, alias_name=None)

    def singleton_agent_definition_with_alias(self, items):
        """Transform alias-based singleton with block: agent Alias(Blueprint): ..."""
        from lark import Token, Tree

        alias_name = None
        blueprint_name = None
        overrides_block = None

        # Expect order: AGENT, Alias NAME, '(', Blueprint NAME, ')', ':', block
        name_tokens = [it for it in items if isinstance(it, Token) and it.type == "NAME"]
        if len(name_tokens) >= 2:
            alias_name = name_tokens[0].value
            blueprint_name = name_tokens[1].value

        for it in items:
            if isinstance(it, Tree) and getattr(it, "data", None) == "singleton_agent_block":
                overrides_block = it

        overrides = []
        if overrides_block is not None:
            for child in overrides_block.children:
                if hasattr(child, "data") and child.data == "singleton_agent_fields":
                    for f in child.children:
                        from dana.core.lang.ast import SingletonAgentField

                        if isinstance(f, SingletonAgentField):
                            overrides.append(f)

        from dana.core.lang.ast import SingletonAgentDefinition

        assert blueprint_name is not None
        return SingletonAgentDefinition(blueprint_name=blueprint_name, overrides=overrides, alias_name=alias_name)

    def singleton_agent_definition_with_alias_simple(self, items):
        """Transform alias-based singleton without block: agent Alias(Blueprint)"""
        from lark import Token

        name_tokens = [it for it in items if isinstance(it, Token) and it.type == "NAME"]
        alias_name = name_tokens[0].value if len(name_tokens) >= 1 else None
        blueprint_name = name_tokens[1].value if len(name_tokens) >= 2 else None
        from dana.core.lang.ast import SingletonAgentDefinition

        assert blueprint_name is not None
        assert alias_name is not None
        return SingletonAgentDefinition(blueprint_name=blueprint_name, overrides=[], alias_name=alias_name)

    def singleton_agent_field(self, items):
        """Transform a singleton agent override into a SingletonAgentField node."""
        name_token = items[0]
        value_expr = items[1]
        from dana.core.lang.ast import SingletonAgentField

        return SingletonAgentField(name=name_token.value, value=value_expr)

    def base_agent_singleton_definition(self, items):
        """Transform `agent Name` into a BaseAgentSingletonDefinition AST node."""
        from lark import Token

        from dana.core.lang.ast import BaseAgentSingletonDefinition

        alias_token = next((it for it in items if isinstance(it, Token) and it.type == "NAME"), None)
        if alias_token is None:
            raise ParseError("Malformed AST: expected an alias token for base agent singleton definition, but none was found.")
        alias = alias_token.value
        return BaseAgentSingletonDefinition(alias_name=alias)

    def agent_field(self, items):
        """Transform an agent field rule into an AgentField node.

        Grammar: agent_field: NAME ":" basic_type ["=" expr] [COMMENT] _NL
        """
        # Validate minimum required parts (name and type)
        if len(items) < 2:
            raise ValueError(f"Agent field must include a name and a type, got {len(items)} item(s): {items}")

        name_token = items[0]
        type_hint_node = items[1]

        # Normalize type hint to TypeHint
        if not isinstance(type_hint_node, TypeHint):
            if isinstance(type_hint_node, Token):
                type_hint = TypeHint(name=type_hint_node.value)
            else:
                raise TypeError(f"Unexpected type for type_hint_node: {type(type_hint_node)}")
        else:
            type_hint = type_hint_node

        # Optional default value expression (third positional item before any COMMENT)
        default_value = None
        if len(items) > 2:
            default_candidate = items[2]
            # Transform only if it looks like an expression tree/token, otherwise ignore
            try:
                default_value = self.main_transformer.expression_transformer.transform(default_candidate)
            except Exception:
                # If it's a trailing comment token or something non-expr, ignore gracefully
                default_value = None

        return AgentField(name=name_token.value, type_hint=type_hint, default_value=default_value)

    # === Resource Definitions ===

    def resource_definition(self, items):
        """Transform a resource definition rule into a ResourceDefinition node."""
        name_token = None
        parent_name_token = None
        resource_block = None

        # Parse items to extract name, optional parent, and block
        for _i, item in enumerate(items):
            if isinstance(item, Token) and item.type == "NAME":
                if name_token is None:
                    name_token = item
                elif parent_name_token is None:
                    parent_name_token = item
            elif hasattr(item, "data") and item.data == "resource_block":
                resource_block = item

        if name_token is None:
            raise ValueError("Resource definition must have a name")

        parent_name = parent_name_token.value if parent_name_token else None
        fields, methods, docstring = self._parse_resource_block(resource_block)

        return ResourceDefinition(name=name_token.value, parent_name=parent_name, fields=fields, methods=methods, docstring=docstring)

    def resource_field(self, items):
        """Transform a resource field rule into a ResourceField node."""
        if len(items) < 2:
            raise ValueError(f"Resource field must have name and type, got {len(items)} items")

        name_token = items[0]
        type_hint_node = items[1]

        # Normalize type hint
        if not isinstance(type_hint_node, TypeHint):
            if isinstance(type_hint_node, Token):
                type_hint = TypeHint(name=type_hint_node.value)
            else:
                raise TypeError(f"Unexpected type for type_hint_node: {type(type_hint_node)}")
        else:
            type_hint = type_hint_node

        # Handle optional default value
        default_value = None
        if len(items) > 2:
            default_value = self.main_transformer.expression_transformer.transform(items[2])

        # Extract comment if present
        comment = None
        for item in items:
            if hasattr(item, "type") and item.type == "COMMENT":
                comment = item.value.lstrip("#").strip()
                break

        return ResourceField(name=name_token.value, type_hint=type_hint, default_value=default_value, comment=comment)

    def resource_method(self, items):
        """Transform a resource method rule into a ResourceMethod node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        if len(relevant_items) < 2:
            raise ValueError(f"Resource method must have at least name and body, got {len(relevant_items)} items")

        # Extract decorators and method name
        decorators, method_name_token, current_index = self._extract_decorators_and_name(relevant_items)

        # Resolve parameters
        parameters, current_index = self._resolve_function_parameters(relevant_items, current_index)

        # Extract return type
        return_type, current_index = self._extract_return_type(relevant_items, current_index)

        # Extract method body
        block_items = self._extract_function_body(relevant_items, current_index)

        # Handle method name extraction
        if isinstance(method_name_token, Token) and method_name_token.type == "NAME":
            method_name = method_name_token.value
        else:
            raise ValueError(f"Expected method name token, got {method_name_token}")

        return ResourceMethod(name=method_name, parameters=parameters, body=block_items, return_type=return_type, decorators=decorators)

    def _parse_resource_block(self, resource_block):
        """Parse a resource block to extract fields, methods, and docstring."""
        fields = []
        methods = []
        docstring = None

        if resource_block and hasattr(resource_block, "data") and resource_block.data == "resource_block":
            for child in resource_block.children:
                if hasattr(child, "data"):
                    if child.data == "docstring":
                        docstring = child.children[0].value.strip('"')
                    elif child.data == "resource_fields_and_methods":
                        for item in child.children:
                            if isinstance(item, ResourceField):
                                fields.append(item)
                            elif isinstance(item, ResourceMethod):
                                methods.append(item)

        return fields, methods, docstring
