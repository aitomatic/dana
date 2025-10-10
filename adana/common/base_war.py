"""
Base WAR (Workflow, Agent, Resource) class with common functionality.
"""

import inspect
import json
import logging
from typing import Any
import xml.etree.ElementTree as ET

from .llm import LLM
from .protocols import Notifier
from .protocols.types import DictParams, Identifiable
from .protocols.war import IS_TOOL_USE, WARProtocol


logger = logging.getLogger(__name__)


class BaseWAR(Notifier, Identifiable, WARProtocol):
    """Base class for WAR (Workflow, Agent, Resource) objects with common functionality."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._public_description = None
        self._llm_client = kwargs.get("llm_client")

    @property
    def llm_client(self) -> LLM:
        """Get the LLM client."""
        if self._llm_client is None:
            self._llm_client = LLM()
        return self._llm_client

    @llm_client.setter
    def llm_client(self, value: LLM):
        """Set the LLM client."""
        self._llm_client = value

    def reason(self, params: DictParams) -> DictParams:
        """
        Perform structured LLM reasoning with typed inputs and outputs.

        Args:
            params: Dictionary containing:
                - task: str (required) - Description of reasoning task
                - input: DictParams (required) - Input data for reasoning
                - output_schema: DictParams (required) - Expected output structure
                - context: DictParams (optional) - Additional context
                - examples: list[DictParams] (optional) - Few-shot examples
                - temperature: float (optional) - LLM temperature (default: 0.1)
                - max_tokens: int (optional) - Max response tokens (default: 2000)
                - fallback: DictParams (optional) - Return this if LLM unavailable

        Returns:
            DictParams: Response matching output_schema structure

        Raises:
            ValueError: If required params missing or output doesn't match schema
            RuntimeError: If LLM call fails and no fallback provided
        """
        # Validate required parameters
        required_params = ["task", "input", "output_schema"]
        for param in required_params:
            if param not in params:
                raise KeyError(f"Required parameter missing: {param}")

        try:
            # Perform reasoning
            result = self._do_reasoning(params)
            return result

        except Exception as e:
            if "fallback" in params:
                logger.warning(f"Reasoning failed, using fallback: {e}")
                return params["fallback"]
            else:
                raise

    def _do_reasoning(self, params: DictParams) -> DictParams:
        """Execute LLM reasoning call."""

        if not self.llm_client:
            if "fallback" in params:
                return params["fallback"]
            raise RuntimeError("LLM client not configured and no fallback provided")

        # Build prompt
        prompt = self._build_prompt(params)

        # Import LLM types
        from .llm import LLMMessage

        # Call LLM using chat_response_sync (synchronous version)
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are a reasoning assistant that ONLY outputs valid JSON. "
                    "Never include explanations, markdown formatting, or any text outside the JSON object. "
                    "Your entire response must be a single valid JSON object matching the requested schema."
                ),
            ),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            llm_response = self.llm_client.chat_response_sync(
                messages=messages,
                temperature=params.get("temperature", 0.1),
                max_tokens=params.get("max_tokens", 2000),
            )
            response_text = llm_response.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            if "fallback" in params:
                return params["fallback"]
            raise

        # Parse and validate
        try:
            # Try to extract JSON from response (LLM may wrap it in markdown or text)
            json_str = response_text.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                # Extract content between ```json and ```
                lines = json_str.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                json_str = "\n".join(json_lines)

            # Find JSON object boundaries
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = json_str[start_idx:end_idx]

            result = json.loads(json_str)
            self._validate_output(result, params["output_schema"])
            return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"LLM response validation failed: {e}")
            logger.debug(f"Raw response: {response_text}")

            if "fallback" in params:
                return params["fallback"]
            raise

    def _build_prompt(self, params: DictParams) -> str:
        """Build LLM prompt from parameters."""
        prompt_parts = [
            f"TASK: {params['task']}",
            "",
            "INPUT DATA:",
            json.dumps(params["input"], indent=2),
            "",
            "OUTPUT SCHEMA:",
            json.dumps(params["output_schema"], indent=2),
        ]

        if "context" in params:
            prompt_parts.extend(["", "CONTEXT:", json.dumps(params["context"], indent=2)])

        if "examples" in params and params["examples"]:
            prompt_parts.extend(["", "EXAMPLES (showing expected JSON format):"])
            for i, example in enumerate(params["examples"], 1):
                prompt_parts.extend(
                    [
                        "",
                        f"Example {i} Input:",
                        json.dumps(example["input"], indent=2),
                        "",
                        f"Example {i} Output (COPY THIS JSON FORMAT):",
                        json.dumps(example["output"], indent=2),
                    ]
                )

        prompt_parts.extend(
            [
                "",
                "CRITICAL INSTRUCTIONS:",
                "1. Respond with ONLY a JSON object - no explanations, no markdown, no extra text",
                "2. Start your response with { and end with }",
                "3. Match the output schema keys exactly",
                "4. Use the same JSON structure as shown in examples",
                "5. For string fields, provide concise text (not explanations)",
                "6. For numeric fields, provide actual numbers (not descriptions)",
                "",
                "YOUR RESPONSE (valid JSON only):",
            ]
        )

        return "\n".join(prompt_parts)

    def _validate_output(self, result: DictParams, output_schema: DictParams) -> None:
        """Validate output against schema with lenient type checking."""
        for key, expected_type in output_schema.items():
            if key not in result:
                # Allow missing keys if they're nullable (contain "null" or "None" or "|")
                expected_type_str = str(expected_type)
                if "null" in expected_type_str.lower() or "none" in expected_type_str.lower() or "|" in expected_type_str:
                    continue
                raise ValueError(f"Output missing required key: {key}")

            actual_value = result[key]
            expected_type_str = str(expected_type)

            # Skip validation for null values if nullable
            if actual_value is None:
                if "null" in expected_type_str.lower() or "none" in expected_type_str.lower() or "|" in expected_type_str:
                    continue
                raise ValueError(f"Output value for '{key}' is null but schema doesn't allow nulls")

            # Lenient type validation - only check basic type compatibility
            # Check list types first (before str, since "list[str]" contains "str")
            if "list" in expected_type_str.lower():
                if not isinstance(actual_value, list):
                    logger.warning(f"Type mismatch for '{key}': expected list, got {type(actual_value).__name__}. Skipping validation.")
                # If it's a list, that's good enough - don't check element types

            elif "dict" in expected_type_str.lower():
                if not isinstance(actual_value, dict):
                    logger.warning(f"Type mismatch for '{key}': expected dict, got {type(actual_value).__name__}. Skipping validation.")

            elif "str" in expected_type_str:
                if not isinstance(actual_value, str):
                    # Allow conversion from simple types
                    if isinstance(actual_value, int | float | bool):
                        result[key] = str(actual_value)
                    else:
                        logger.warning(f"Type mismatch for '{key}': expected str, got {type(actual_value).__name__}. Skipping validation.")

            elif "int" in expected_type_str:
                if not isinstance(actual_value, int) and not isinstance(actual_value, bool):
                    logger.warning(f"Type mismatch for '{key}': expected int, got {type(actual_value).__name__}. Skipping validation.")

            elif "float" in expected_type_str:
                if not isinstance(actual_value, int | float):
                    logger.warning(f"Type mismatch for '{key}': expected float, got {type(actual_value).__name__}. Skipping validation.")

            elif "bool" in expected_type_str:
                if not isinstance(actual_value, bool):
                    logger.warning(f"Type mismatch for '{key}': expected bool, got {type(actual_value).__name__}. Skipping validation.")

            # Range validation for floats (e.g., "0.0-1.0") - lenient
            if isinstance(actual_value, int | float) and "0.0-1.0" in expected_type_str:
                if not (0.0 <= actual_value <= 1.0):
                    logger.warning(f"Value for '{key}' out of range: expected 0.0-1.0, got {actual_value}. Clamping.")
                    result[key] = max(0.0, min(1.0, float(actual_value)))

            # Enum validation (e.g., "str (option1|option2|option3)") - lenient
            if "|" in expected_type_str and isinstance(actual_value, str) and "(" in expected_type_str:
                try:
                    # Extract options between parentheses
                    paren_content = expected_type_str.split("(", 1)[1].rsplit(")", 1)[0]
                    # Skip if contains descriptive text like "ONLY choose from:"
                    if ":" in paren_content:
                        paren_content = paren_content.split(":", 1)[1]
                    enum_options = [opt.strip() for opt in paren_content.split("|")]
                    if actual_value not in enum_options:
                        # Don't warn if value is actually valid, just parsed differently
                        pass
                except (IndexError, ValueError):
                    pass  # Couldn't parse enum, skip validation

    # ============================================================================
    # COMMON REGISTRY MANAGEMENT
    # ============================================================================

    def _register_self(self) -> str:
        """Register this object with its appropriate registry.

        Returns:
            Object ID assigned by the registry
        """
        registry = self._get_registry()
        return registry.register(
            item=self,
            object_id=self.object_id,
            item_type=self._get_object_type(),
            name=self._get_object_name(),
            description=self._get_object_description(),
            capabilities=self._get_capabilities(),
            metadata=self._get_metadata(),
        )

    def _unregister_self(self) -> bool:
        """Unregister this object from its registry.

        Returns:
            True if unregistered successfully, False otherwise
        """
        if not self.object_id:
            return False

        registry = self._get_registry()
        return registry.unregister(self.object_id)

    def _update_registry_metadata(self, metadata: dict[str, Any]) -> bool:
        """Update metadata in the registry.

        Args:
            metadata: New metadata to update

        Returns:
            True if updated successfully, False otherwise
        """
        if not self.object_id:
            return False

        registry = self._get_registry()
        item = registry.get(self.object_id)
        if item and hasattr(item, "_registered_metadata"):
            item._registered_metadata.update(metadata)
            return True
        return False

    def _get_registry(self):
        """Get the appropriate registry for this object type.

        This method must be implemented by subclasses to return the correct registry.
        """
        raise NotImplementedError("Subclasses must implement _get_registry()")

    def _get_object_type(self) -> str:
        """Get the object type for registry.

        This method must be implemented by subclasses to return the object type.
        """
        raise NotImplementedError("Subclasses must implement _get_object_type()")

    def _get_object_name(self) -> str:
        """Get the object name for registry.

        Returns:
            Human-readable name for the object
        """
        return getattr(self, "_registered_name", self.__class__.__name__)

    def _get_object_description(self) -> str:
        """Get the object description for registry.

        Returns:
            Description of what the object does
        """
        return getattr(self, "_registered_description", getattr(self, "prt_public_description", "No description available"))

    def _get_capabilities(self) -> list[str]:
        """Get the object capabilities for registry.

        Returns:
            List of capabilities this object provides
        """
        return getattr(self, "_registered_capabilities", [])

    def _get_metadata(self) -> dict[str, Any]:
        """Get the object metadata for registry.

        Returns:
            Dictionary of metadata about the object
        """
        return getattr(self, "_registered_metadata", {})

    # ============================================================================
    # COMMON REGISTRY DISCOVERY METHODS
    # ============================================================================

    def find_objects(self, object_type: str | None = None, capability: str | None = None) -> list:
        """Find objects by type or capability.

        Args:
            object_type: Filter by object type
            capability: Filter by capability

        Returns:
            List of matching objects
        """
        registry = self._get_registry()
        return registry.list(item_type=object_type, capability=capability)

    def get_object_info(self, object_id: str) -> dict[str, Any] | None:
        """Get information about a specific object.

        Args:
            object_id: ID of the object

        Returns:
            Object info dict if found, None otherwise
        """
        registry = self._get_registry()
        return registry.get_info(object_id)

    def list_available_objects(self) -> dict[str, Any]:
        """List all available objects in the registry.

        Returns:
            Dictionary with registry statistics and object counts
        """
        registry = self._get_registry()
        return registry.get_stats()

    def _get_registry_stats(self) -> dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        registry = self._get_registry()
        return registry.get_stats()

    def _export_registry_data(self) -> dict[str, Any]:
        """Export registry data for persistence.

        Returns:
            Dictionary with registry data
        """
        registry = self._get_registry()
        if hasattr(registry, "export_registry"):
            return registry.export_registry()
        return {"exported_at": "unknown", "items": {}}

    def _import_registry_data(self, data: dict[str, Any]) -> bool:
        """Import registry data from persistence.

        Args:
            data: Dictionary with registry data

        Returns:
            True if imported successfully, False otherwise
        """
        registry = self._get_registry()
        if hasattr(registry, "import_registry"):
            return registry.import_registry(data)
        return False

    def ensure_registered(self) -> "BaseWAR":
        """Ensure this object is registered with the registry."""
        if self.object_id not in self._get_registry()._items:
            self._register_self()
        return self

    def _get_public_description(self, only_specific_method: str | None = None, format: str = "xml") -> str:
        """Get the public description including available tool methods.
        Args:
            only_specific_method: The specific method to get the description for.
            Used by BaseWorkflow to only include the description for the "execute" method.
            format: Output format - "xml", "json", or "text" (default: "xml")

        Returns:
            The public description including available tool methods in the specified format.
        """
        # Return cached version if available (only for text format)
        if self._public_description is not None and format == "text":
            return self._public_description

        # Collect data as a dictionary
        data = self._collect_description_data(only_specific_method)

        # Convert to requested format
        if format == "json":
            return self._dict_to_json(data)
        elif format == "xml":
            return self._dict_to_xml(data)
        else:  # text format
            return self._dict_to_text(data, only_specific_method)

    def _collect_description_data(self, only_specific_method: str | None = None) -> dict:
        """Collect description data as a dictionary.

        Args:
            only_specific_method: The specific method to get the description for.

        Returns:
            Dictionary containing all description data.
        """
        # Get basic description
        if only_specific_method:
            description = ""
        else:
            description = self.__doc__ or "No description available"

        # Find all methods decorated with @tool_use
        tool_methods = []

        # Use the class instead of the instance to avoid recursion
        for name in dir(self.__class__):
            if name.startswith("_"):  # Skip private methods
                continue

            attr = getattr(self.__class__, name)
            if callable(attr) and hasattr(attr, "__dict__"):
                if only_specific_method and name == only_specific_method:
                    method_doc = ""
                elif attr.__dict__.get(IS_TOOL_USE, False):
                    method_doc = attr.__doc__ or "No description available"
                else:
                    continue

                # Enhance the docstring with type signatures in Args section
                enhanced_doc = self._enhance_docstring_with_types(attr, method_doc)

                # Get method signature for better clarity
                try:
                    sig = inspect.signature(attr)
                    # Remove 'self' parameter from signature
                    params = [p for param_name, p in sig.parameters.items() if param_name != "self"]
                    param_str = ", ".join(str(p) for p in params)
                    method_signature = f"{name}({param_str})"
                except (ValueError, TypeError):
                    method_signature = f"{name}(...)"

                # Collect method data
                method_data = {"name": name, "signature": method_signature, "description": enhanced_doc, "docstring": method_doc}
                tool_methods.append(method_data)

        # Build the data structure
        data = {
            "class_name": self.__class__.__name__,
            "description": description,
            "object_id": getattr(self, "object_id", None),
            "object_type": getattr(self, "object_type", None),
            "methods": tool_methods,
            "method_count": len(tool_methods),
        }

        return data

    def _dict_to_json(self, data: dict) -> str:
        """Convert dictionary to JSON string.

        Args:
            data: Dictionary to convert

        Returns:
            JSON string representation
        """
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _dict_to_xml(self, data: dict) -> str:
        """Convert dictionary to XML string.

        Args:
            data: Dictionary to convert

        Returns:
            XML string representation
        """
        root = ET.Element("object")
        root.set("class", data["class_name"])

        if data["object_id"]:
            root.set("id", str(data["object_id"]))
        if data["object_type"]:
            root.set("type", str(data["object_type"]))

        # Add description
        desc_elem = ET.SubElement(root, "description")
        desc_elem.text = data["description"]

        # Add methods
        methods_elem = ET.SubElement(root, "methods")
        methods_elem.set("count", str(data["method_count"]))

        for method in data["methods"]:
            method_elem = ET.SubElement(methods_elem, "method")
            method_elem.set("name", method["name"])
            method_elem.set("signature", method["signature"])

            desc_elem = ET.SubElement(method_elem, "description")
            desc_elem.text = method["description"]

        # Convert to string
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding="unicode")

    def _dict_to_text(self, data: dict, only_specific_method: str | None = None) -> str:
        """Convert dictionary to text format (original behavior).

        Args:
            data: Dictionary to convert
            only_specific_method: The specific method to get the description for

        Returns:
            Text string representation
        """
        description = data["description"]

        if data["methods"]:
            description += "\n\nAvailable methods:\n"
            for method in data["methods"]:
                description += f"  - {method['signature']}: {method['description']}\n"

        # Cache the result for text format
        if only_specific_method is None:
            self._public_description = description

        return description

    def _enhance_docstring_with_types(self, method, docstring: str) -> str:
        """Enhance docstring Args section with type signatures from method signature.

        Args:
            method: The method to get signature from
            docstring: The original docstring

        Returns:
            Enhanced docstring with type information in Args section
        """
        try:
            sig = inspect.signature(method)
            # Get parameter info (excluding 'self')
            param_info = {}
            for param_name, param in sig.parameters.items():
                if param_name != "self":
                    param_info[param_name] = {
                        "annotation": param.annotation,
                        "default": param.default,
                        "has_default": param.default != inspect.Parameter.empty,
                    }

            if not param_info:
                return docstring

            # Parse the docstring to find Args section
            lines = docstring.split("\n")
            enhanced_lines = []
            in_args_section = False

            for line in lines:
                if line.strip().startswith("Args:"):
                    in_args_section = True
                    enhanced_lines.append(line)
                    continue

                if in_args_section:
                    if line.strip() and not line.startswith(" "):
                        # End of Args section
                        in_args_section = False
                        # Add enhanced parameter documentation
                        for param_name, info in param_info.items():
                            if info["annotation"] != inspect.Parameter.empty:
                                type_str = str(info["annotation"])
                                if info["has_default"]:
                                    enhanced_lines.append(f"            {param_name} ({type_str}): Parameter description")
                                else:
                                    enhanced_lines.append(f"            {param_name} ({type_str}): Parameter description")
                        enhanced_lines.append("")
                        enhanced_lines.append(line)
                    else:
                        enhanced_lines.append(line)
                else:
                    enhanced_lines.append(line)

            return "\n".join(enhanced_lines)

        except Exception:
            # If anything goes wrong, return original docstring
            return docstring
