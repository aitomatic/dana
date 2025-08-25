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
    Decorator,
    FunctionDefinition,
    Identifier,
    InterfaceDefinition,
    InterfaceMethod,
    Parameter,
    ResourceDefinition,
    StructDefinition,
    StructField,
    TypedParameter,
    TypeHint,
    WorkflowDefinition,
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
        """Transform a unified function definition rule into a FunctionDefinition node.

        Grammar: function_def: [decorators] function_header [receiver_spec] NAME "(" [parameters] ")" ["->" basic_type] ":" [COMMENT] block
        """
        # Filter out None values and Comments
        relevant_items = self.main_transformer._filter_relevant_items(items)

        if len(relevant_items) < 2:
            raise ValueError(f"Function definition must have at least a name and body, got {len(relevant_items)} items")

        current_index = 0
        decorators = []
        is_sync = False

        # Check for decorators
        if current_index < len(relevant_items) and isinstance(relevant_items[current_index], list):
            first_item = relevant_items[current_index]
            if first_item and hasattr(first_item[0], "name"):  # Check if it's a list of Decorator objects
                decorators = first_item
                current_index += 1

        # Extract receiver if present
        receiver = None
        if (
            current_index < len(relevant_items)
            and hasattr(relevant_items[current_index], "data")
            and relevant_items[current_index].data == "receiver_spec"
        ):
            receiver_tree = relevant_items[current_index]
            if receiver_tree.children:
                receiver_param = receiver_tree.children[0]
                # Check if receiver_param is already a transformed Parameter object
                if isinstance(receiver_param, Parameter):
                    receiver = receiver_param
                elif hasattr(receiver_param, "data") and receiver_param.data == "typed_parameter":
                    receiver = self.main_transformer.assignment_transformer.typed_parameter(receiver_param.children)
            current_index += 1

        # Extract function name
        func_name_token = relevant_items[current_index]
        if not (isinstance(func_name_token, Token) and func_name_token.type == "NAME"):
            raise ValueError(f"Expected function name token, got {func_name_token}")
        func_name = func_name_token.value
        current_index += 1

        # Resolve parameters using simplified logic
        parameters, current_index = self._resolve_function_parameters(relevant_items, current_index)

        # Extract return type
        return_type, current_index = self._extract_return_type(relevant_items, current_index)

        # Extract function body
        block_items = self._extract_function_body(relevant_items, current_index)

        location = self.main_transformer.create_location(func_name_token)

        return FunctionDefinition(
            name=Identifier(name=func_name, location=location),
            parameters=parameters,
            body=block_items,
            return_type=return_type,
            decorators=decorators,
            is_sync=is_sync,
            receiver=receiver,
            location=location,
        )

    def sync_function_def(self, items):
        """Transform a sync function definition rule into a FunctionDefinition node.

        This is the same as function_def but with is_sync=True.
        """
        # Call the regular function_def method but set is_sync=True
        result = self.function_def(items)
        if isinstance(result, FunctionDefinition):
            result.is_sync = True
        return result

    def function_header(self, items):
        """Transform a function_header rule into a list indicating sync status.

        Grammar: function_header: "def" | "sync" "def"
        """
        # Return a list with the tokens to indicate sync status
        return items

    def unified_function_def(self, items):
        """Transform a unified function definition rule into a FunctionDefinition node."""
        relevant_items = self.main_transformer._filter_relevant_items(items)

        if len(relevant_items) < 2:
            raise ValueError(f"Function definition must have at least a name and body, got {len(relevant_items)} items")

        current_index = 0
        decorators = []

        # Check for decorators
        if current_index < len(relevant_items) and isinstance(relevant_items[current_index], list):
            first_item = relevant_items[current_index]
            if first_item and hasattr(first_item[0], "name"):  # Check if it's a list of Decorator objects
                decorators = first_item
                current_index += 1

        # Extract receiver if present
        receiver = None
        if (
            current_index < len(relevant_items)
            and hasattr(relevant_items[current_index], "data")
            and relevant_items[current_index].data == "receiver_spec"
        ):
            receiver_tree = relevant_items[current_index]
            if receiver_tree.children:
                receiver_param = receiver_tree.children[0]
                # Check if receiver_param is already a transformed Parameter object
                if isinstance(receiver_param, Parameter):
                    receiver = receiver_param
                elif hasattr(receiver_param, "data") and receiver_param.data == "typed_parameter":
                    receiver = self.main_transformer.assignment_transformer.typed_parameter(receiver_param.children)
            current_index += 1

        # Extract function name
        func_name_token = relevant_items[current_index]
        if not (isinstance(func_name_token, Token) and func_name_token.type == "NAME"):
            raise ValueError(f"Expected function name token, got {func_name_token}")
        func_name = func_name_token.value
        current_index += 1

        # Resolve parameters using simplified logic
        parameters, current_index = self._resolve_function_parameters(relevant_items, current_index)

        # Extract return type
        return_type, current_index = self._extract_return_type(relevant_items, current_index)

        # Extract function body
        block_items = self._extract_function_body(relevant_items, current_index)

        location = self.main_transformer.create_location(func_name_token)

        return FunctionDefinition(
            name=Identifier(name=func_name, location=location),
            parameters=parameters,
            body=block_items,
            return_type=return_type,
            decorators=decorators,
            is_sync=False,
            receiver=receiver,
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

        return FunctionDefinition(
            name=Identifier(name=method_name, location=location),
            parameters=parameters,
            body=block_items,
            return_type=return_type,
            decorators=decorators,
            is_sync=False,  # Methods don't support sync keyword yet
            receiver=receiver_param,
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

        # Check for sync keyword
        is_sync = False
        if (
            current_index < len(relevant_items)
            and isinstance(relevant_items[current_index], Token)
            and relevant_items[current_index].type == "SYNC"
        ):
            is_sync = True
            current_index += 1

        # The next item should be the function name
        if current_index >= len(relevant_items):
            raise ValueError("Expected function name after decorators and sync keyword")

        func_name_token = relevant_items[current_index]
        current_index += 1

        return decorators, func_name_token, current_index, is_sync

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

    def definition(self, items):
        """Transform a unified definition rule into appropriate AST node."""

        # Extract keyword, name, optional parent, and block
        keyword_token = items[0]  # STRUCT, RESOURCE, AGENT_BLUEPRINT, or INTERFACE
        name_token = items[1]
        definition_block = None

        # Find the definition_block - it should be a dict (transformed) or Tree
        for item in items[2:]:  # Skip keyword and name
            if item is not None and (
                isinstance(item, dict) or (hasattr(item, "data") and item.data in ["struct_block", "interface_block", "definition_block"])
            ):
                definition_block = item
                break

        if keyword_token.value == "struct":
            fields, methods, docstring = self._parse_struct_block(definition_block)
            return StructDefinition(name=name_token.value, fields=fields, docstring=docstring)
        elif keyword_token.value == "resource":
            fields, methods, docstring = self._parse_struct_block(definition_block)
            return ResourceDefinition(name=name_token.value, fields=fields, methods=methods, docstring=docstring)
        elif keyword_token.value == "agent_blueprint":
            fields, methods, docstring = self._parse_struct_block(definition_block)
            return AgentDefinition(name=name_token.value, fields=fields, methods=methods, docstring=docstring)
        elif keyword_token.value == "interface":
            methods, embedded_interfaces, docstring = self._parse_interface_block(definition_block)
            return InterfaceDefinition(name=name_token.value, methods=methods, embedded_interfaces=embedded_interfaces, docstring=docstring)
        elif keyword_token.value == "workflow":
            fields, methods, docstring = self._parse_struct_block(definition_block)
            return WorkflowDefinition(name=name_token.value, fields=fields, methods=methods, docstring=docstring)
        else:
            raise ValueError(f"Unknown definition keyword: {keyword_token.value}")

    def field(self, items):
        """Transform a field rule into a StructField node."""

        name_token = items[0]
        type_hint_node = items[1]

        field_name = name_token.value

        # The type_hint_node might be a raw Tree that needs transformation
        # or it might already be a TypeHint object from the 'basic_type' rule transformation.
        if not isinstance(type_hint_node, TypeHint):
            # Check if it's a Tree that needs to be transformed
            if hasattr(type_hint_node, "data") and type_hint_node.data == "basic_type":
                # Transform the basic_type Tree using the main transformer
                type_hint = self.main_transformer.basic_type(type_hint_node.children)
            elif isinstance(type_hint_node, Token):
                # Fallback if it's a token
                type_hint = TypeHint(name=type_hint_node.value)
            else:
                # This would be an unexpected state
                raise TypeError(f"Unexpected type for type_hint_node: {type(type_hint_node)}")
        else:
            type_hint = type_hint_node

        # Handle optional default value
        default_value = None
        if len(items) > 2 and items[2] is not None:
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

    def singleton_agent_definition(self, items):
        """Transform a unified singleton agent definition into a SingletonAgentDefinition node."""
        from lark import Token, Tree

        alias_name = None
        blueprint_name = None
        overrides_block = None

        # Parse items: AGENT, [alias_name], '(', blueprint_name, ')', ':', block
        name_tokens = [it for it in items if isinstance(it, Token) and it.type == "NAME"]

        if len(name_tokens) == 1:
            # No alias: agent(Blueprint): ...
            blueprint_name = name_tokens[0].value
        elif len(name_tokens) == 2:
            # With alias: agent Alias(Blueprint): ...
            alias_name = name_tokens[0].value
            blueprint_name = name_tokens[1].value

        for it in items:
            if isinstance(it, Tree) and getattr(it, "data", None) == "singleton_agent_block":
                overrides_block = it

        overrides = []
        docstring = None
        if overrides_block is not None:
            for child in overrides_block.children:
                if hasattr(child, "data") and child.data == "docstring":
                    docstring = child.children[0].value.strip('"')
                elif hasattr(child, "data") and child.data == "singleton_agent_fields":
                    for f in child.children:
                        from dana.core.lang.ast import SingletonAgentField

                        if isinstance(f, SingletonAgentField):
                            overrides.append(f)

        from dana.core.lang.ast import SingletonAgentDefinition

        assert blueprint_name is not None
        return SingletonAgentDefinition(blueprint_name=blueprint_name, overrides=overrides, alias_name=alias_name, docstring=docstring)

    def agent_alias_def(self, items):
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

    def agent_base_def(self, items):
        """Transform `agent Name` into a BaseAgentSingletonDefinition AST node."""
        from lark import Token

        from dana.core.lang.ast import BaseAgentSingletonDefinition

        alias_token = next((it for it in items if isinstance(it, Token) and it.type == "NAME"), None)
        if alias_token is None:
            raise ParseError("Malformed AST: expected an alias token for base agent singleton definition, but none was found.")
        alias = alias_token.value
        return BaseAgentSingletonDefinition(alias_name=alias)

    def fields_and_functions(self, items):
        """Transform a fields_and_functions rule into a list of StructField and FunctionDefinition objects."""
        result = []
        for item in items:
            if item is not None:
                # The item should already be transformed by the individual field/function rules
                result.append(item)
        return result

    def struct_block(self, items):
        """Transform a struct_block rule into a structured format for parsing."""
        # The struct_block contains: [docstring?] fields_and_functions
        docstring = None
        fields_and_functions = None

        for item in items:
            if item is not None:
                if hasattr(item, "data") and item.data == "docstring":
                    docstring = item.children[0].value.strip('"') if item.children else None
                elif isinstance(item, list):
                    # This should be the transformed fields_and_functions
                    fields_and_functions = item
                else:
                    # If it's still a tree, it might be fields_and_functions
                    fields_and_functions = item

        return {"docstring": docstring, "fields_and_functions": fields_and_functions or []}

    # === Resource Definitions ===

    def _parse_struct_block(self, struct_block):
        """Parse a struct block to extract fields, functions, and docstring."""
        fields = []
        methods = []
        docstring = None

        if struct_block is None:
            return fields, methods, docstring

        # Handle the case where definition_block is a Tree with definition_block data
        if hasattr(struct_block, "data") and struct_block.data == "definition_block":
            # Extract the dict from the definition_block Tree
            if struct_block.children and isinstance(struct_block.children[0], dict):
                struct_dict = struct_block.children[0]
                docstring = struct_dict.get("docstring")
                fields_and_functions = struct_dict.get("fields_and_functions", [])

                for item in fields_and_functions:
                    if isinstance(item, StructField):
                        fields.append(item)
                    elif isinstance(item, FunctionDefinition):
                        methods.append(item)
                return fields, methods, docstring

        # Handle transformed dict format
        if isinstance(struct_block, dict):
            docstring = struct_block.get("docstring")
            fields_and_functions = struct_block.get("fields_and_functions", [])

            for item in fields_and_functions:
                if isinstance(item, StructField):
                    fields.append(item)
                elif isinstance(item, FunctionDefinition):
                    methods.append(item)
            return fields, methods, docstring

        # Handle Tree format
        if hasattr(struct_block, "data") and struct_block.data == "struct_block":
            for child in struct_block.children:
                if hasattr(child, "data"):
                    if child.data == "docstring":
                        docstring = child.children[0].value.strip('"')
                    elif child.data == "fields_and_functions":
                        # The fields_and_functions rule should be transformed into a list
                        # by the fields_and_functions method
                        if hasattr(child, "children"):
                            for item in child.children:
                                if isinstance(item, StructField):
                                    fields.append(item)
                                elif isinstance(item, FunctionDefinition):
                                    methods.append(item)
                        # If child is already transformed (a list), use it directly
                        elif isinstance(child, list):
                            for item in child:
                                if isinstance(item, StructField):
                                    fields.append(item)
                                elif isinstance(item, FunctionDefinition):
                                    methods.append(item)

        return fields, methods, docstring

    def _parse_interface_block(self, interface_block):
        """Parse an interface block into methods, embedded interfaces, and docstring."""

        methods = []
        embedded_interfaces = []
        docstring = None

        if interface_block is None:
            return methods, embedded_interfaces, docstring

        # Handle the case where definition_block is a Tree with definition_block data
        if hasattr(interface_block, "data") and interface_block.data == "definition_block":
            # Extract the dict from the Tree
            if interface_block.children and isinstance(interface_block.children[0], dict):
                block_dict = interface_block.children[0]
                methods = block_dict.get("methods", [])
                embedded_interfaces = block_dict.get("embedded_interfaces", [])
                docstring = block_dict.get("docstring", None)
                return methods, embedded_interfaces, docstring

        # Handle transformed dict format
        if isinstance(interface_block, dict):
            if "docstring" in interface_block:
                docstring = interface_block["docstring"]
            if "methods" in interface_block:
                methods = interface_block["methods"]
            if "embedded_interfaces" in interface_block:
                embedded_interfaces = interface_block["embedded_interfaces"]
            return methods, embedded_interfaces, docstring

        # Handle Tree format
        if hasattr(interface_block, "children"):
            for child in interface_block.children:
                if hasattr(child, "data"):
                    if child.data == "docstring":
                        docstring = child.children[0].value.strip("\"'")
                    elif child.data == "interface_members":
                        for member in child.children:
                            if hasattr(member, "data"):
                                if member.data == "interface_method":
                                    method = self._parse_interface_method(member)
                                    if method:
                                        methods.append(method)
                                elif member.data == "embedded_interface":
                                    embedded_name = member.children[0].value
                                    embedded_interfaces.append(embedded_name)

        return methods, embedded_interfaces, docstring

    def _parse_interface_method(self, method_tree):
        """Parse an interface method tree into an InterfaceMethod node."""

        if not hasattr(method_tree, "children") or not method_tree.children:
            return None

        # Extract method name
        method_name = method_tree.children[0].value

        # Extract parameters
        parameters = []
        return_type = None
        comment = None

        # Parse the method signature
        for child in method_tree.children:
            if hasattr(child, "data"):
                if child.data == "parameters":
                    for param_tree in child.children:
                        if hasattr(param_tree, "data") and param_tree.data == "typed_parameter":
                            param = self._parse_typed_parameter(param_tree)
                            if param:
                                parameters.append(param)
                elif child.data == "basic_type":  # Return type
                    return_type = self.main_transformer.basic_type(child.children)

        # Extract comment if present
        for child in method_tree.children:
            if hasattr(child, "type") and child.type == "COMMENT":
                comment = child.value.lstrip("#").strip()
                break

        return InterfaceMethod(name=method_name, parameters=parameters, return_type=return_type, comment=comment)

    def _parse_typed_parameter(self, param_tree):
        """Parse a typed parameter tree into a TypedParameter node."""

        if not hasattr(param_tree, "children") or not param_tree.children:
            return None

        # Extract parameter name
        param_name = param_tree.children[0].value

        # Extract type hint if present
        type_hint = None
        default_value = None

        for child in param_tree.children[1:]:
            if hasattr(child, "data") and child.data == "basic_type":
                type_hint = self.main_transformer.basic_type(child.children)
            elif hasattr(child, "data") and child.data == "expr":
                default_value = self.main_transformer.expression_transformer.transform(child.children)

        return TypedParameter(name=param_name, type_hint=type_hint, default_value=default_value)

    # === Interface Block Parsing ===

    def interface_block(self, items):
        """Transform an interface block into a dict with methods, embedded interfaces, and docstring."""
        methods = []
        embedded_interfaces = []
        docstring = None

        for item in items:
            if item is None:
                continue
            elif isinstance(item, list):
                # This is likely the transformed interface_members list
                for member in item:
                    if isinstance(member, InterfaceMethod):
                        methods.append(member)
                    elif isinstance(member, str):
                        # Embedded interface name
                        embedded_interfaces.append(member)
            elif hasattr(item, "data"):
                if item.data == "docstring":
                    docstring = item.children[0].value.strip("\"'")
                elif item.data == "interface_members":
                    for member in item.children:
                        if hasattr(member, "data"):
                            if member.data == "interface_method":
                                method = self._parse_interface_method(member)
                                if method:
                                    methods.append(method)
                            elif member.data == "embedded_interface":
                                embedded_name = member.children[0].value
                                embedded_interfaces.append(embedded_name)

        return {"methods": methods, "embedded_interfaces": embedded_interfaces, "docstring": docstring}

    def interface_members(self, items):
        """Transform interface members into a list."""
        return items

    def interface_member(self, items):
        """Transform an interface member (method or embedded interface) into the appropriate node."""
        # This will be handled by the specific methods (interface_method or embedded_interface)
        return items[0]

    def interface_method(self, items):
        """Transform an interface method into an InterfaceMethod node."""
        return self._parse_interface_method_from_items(items)

    def embedded_interface(self, items):
        """Transform an embedded interface reference into a string."""
        # Extract the interface name from the token
        interface_name = items[0].value
        return interface_name

    def _parse_interface_method_from_items(self, items):
        """Parse interface method from items list."""

        # Extract method name
        method_name = items[0].value

        # Extract parameters
        parameters = []
        return_type = None
        comment = None

        # Parse parameters if present - handle both Parameter and TypedParameter objects
        if len(items) > 1 and isinstance(items[1], list):
            param_list = items[1]
            for param_item in param_list:
                if isinstance(param_item, Parameter):
                    # Convert Parameter to TypedParameter
                    typed_param = TypedParameter(
                        name=param_item.name,
                        type_hint=param_item.type_hint,
                        default_value=param_item.default_value,
                        location=param_item.location,
                    )
                    parameters.append(typed_param)
                elif hasattr(param_item, "data") and param_item.data == "typed_parameter":
                    param = self._parse_typed_parameter(param_item)
                    if param:
                        parameters.append(param)

        # Parse return type if present
        for item in items:
            if hasattr(item, "data") and item.data == "basic_type":
                return_type = self.main_transformer.basic_type(item.children)
                break
            elif isinstance(item, TypeHint):
                return_type = item
                break

        # Extract comment if present
        for item in items:
            if hasattr(item, "type") and item.type == "COMMENT":
                comment = item.value.lstrip("#").strip()
                break

        return InterfaceMethod(name=method_name, parameters=parameters, return_type=return_type, comment=comment)
