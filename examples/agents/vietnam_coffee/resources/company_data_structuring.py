"""
CompanyDataStructuringResource - Structure extracted data into schemas.

Domain-agnostic resource for using LLM to extract structured fields from
unstructured text. Useful for any data extraction project.
"""

import asyncio
import json
import time

from dana.common.llm.llm import LLM, LLMMessage
from dana.common.observable import observable
from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class CompanyDataStructuringResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Extracts structured data from unstructured text using LLM.

    Takes raw text (HTML, documents, etc.) and a schema definition,
    then uses an LLM to extract structured fields matching the schema.

    Features:
    - Type validation (string, int, float, bool, list)
    - Confidence scoring per field
    - Graceful fallback on errors
    - Support for nested schemas

    Useful for web scraping, document parsing, and any scenario
    where structured data needs to be extracted from unstructured sources.
    </PUBLIC_DESCRIPTION>
    """

    def __init__(self, llm_provider: str | None = None, model: str | None = None, resource_id: str | None = None, **kwargs):
        """
        Initialize the CompanyDataStructuringResource.

        Args:
            llm_provider: LLM provider (default: auto-select by priority)
            model: Model name (default: provider's default)
            resource_id: Resource identifier
        """
        super().__init__(resource_type="company-structuring", resource_id=resource_id or "company-structuring", **kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

    @tool_use
    @observable
    def structure_company_data(self, raw_text: str, schema: dict, context: str | None = None, **kwargs) -> DictParams:
        """
        Extract structured fields from unstructured text.

        Args:
            raw_text: Raw text to extract from (HTML, documents, etc.)
            schema: Schema definition (field_name: {type, description, required})
            context: Optional context to help with extraction

        Returns:
            Structured data matching schema + confidence scores
        """
        result = asyncio.run(self._structure_company_data(raw_text, schema, context, **kwargs))
        return result

    async def _structure_company_data(self, raw_text: str, schema: dict, context: str | None = None, **kwargs) -> DictParams:
        """Internal async implementation"""
        start_time = time.time()

        if not raw_text or not raw_text.strip():
            return {"success": False, "error": "Empty input text", "data": None, "processing_time": time.time() - start_time}

        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(raw_text, schema, context)

            system_message = """You are an expert data extraction specialist.
Extract structured information from unstructured text accurately and conservatively.
If a field cannot be determined from the text, return null rather than guessing."""

            # Call LLM
            response = await self.llm.chat_response(
                messages=[LLMMessage(role="user", content=prompt)], system_message=system_message, max_tokens=1500, temperature=0.1
            )

            content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
            structured_data = self._parse_json_response(content)

            # Validate against schema
            validated_data, field_confidences = self._validate_and_score(structured_data, schema, raw_text)

            # Calculate overall confidence
            confidences = [c for c in field_confidences.values() if c is not None]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "success": True,
                "data": validated_data,
                "field_confidences": field_confidences,
                "overall_confidence": overall_confidence,
                "processing_time": time.time() - start_time,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "data": None, "processing_time": time.time() - start_time}

    @tool_use
    @observable
    def extract_specific_field(self, raw_text: str, field_name: str, field_type: str, description: str, **kwargs) -> DictParams:
        """
        Extract a single specific field from text.

        Args:
            raw_text: Raw text to extract from
            field_name: Name of the field to extract
            field_type: Type (string, int, float, bool, list)
            description: Description of what to extract

        Returns:
            Extracted field value with confidence
        """
        schema = {field_name: {"type": field_type, "description": description, "required": False}}

        result = asyncio.run(self._structure_company_data(raw_text, schema, None, **kwargs))

        if result["success"]:
            field_value = result["data"].get(field_name)
            field_confidence = result["field_confidences"].get(field_name, 0.0)

            return {
                "success": True,
                "field_name": field_name,
                "value": field_value,
                "confidence": field_confidence,
                "processing_time": result["processing_time"],
            }
        else:
            return {"success": False, "error": result["error"], "field_name": field_name, "value": None}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _build_extraction_prompt(self, raw_text: str, schema: dict, context: str | None) -> str:
        """Build LLM prompt for data extraction"""

        # Build schema description
        schema_lines = []
        for field_name, field_def in schema.items():
            field_type = field_def.get("type", "string")
            description = field_def.get("description", "")
            required = field_def.get("required", False)
            req_text = " (REQUIRED)" if required else " (optional)"

            schema_lines.append(f'  "{field_name}": {field_type}{req_text} - {description}')

        schema_description = "\n".join(schema_lines)

        # Build example output
        example_output = {field: None for field in schema.keys()}
        example_json = json.dumps(example_output, indent=2)

        context_section = f"\nCONTEXT:\n{context}\n" if context else ""

        prompt = f"""TASK: Extract structured data from the following text.

{context_section}
SOURCE TEXT:
{raw_text[:3000]}

SCHEMA TO EXTRACT:
{schema_description}

OUTPUT FORMAT (JSON):
{example_json}

INSTRUCTIONS:
1. Extract only information explicitly stated in the text
2. Return null for fields that cannot be determined
3. For numeric fields, extract numbers only (no currency symbols or units in the value)
4. For boolean fields, return true/false
5. For list fields, return array of items
6. Be conservative - accuracy over completeness

Return ONLY valid JSON matching the schema."""

        return prompt

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from LLM response"""
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        # Try to find JSON object
        json_start = content.find("{")
        json_end = content.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in response")

    def _validate_and_score(self, data: dict, schema: dict, original_text: str) -> tuple[dict, dict]:
        """
        Validate extracted data against schema and compute confidence scores.

        Returns:
            (validated_data, field_confidences)
        """
        validated = {}
        confidences = {}

        for field_name, field_def in schema.items():
            expected_type = field_def.get("type", "string")
            required = field_def.get("required", False)
            value = data.get(field_name)

            # Check if required field is missing
            if required and (value is None or value == ""):
                validated[field_name] = None
                confidences[field_name] = 0.0
                continue

            # Validate type
            validated_value, confidence = self._validate_field_type(value, expected_type, field_name, original_text)

            validated[field_name] = validated_value
            confidences[field_name] = confidence

        return validated, confidences

    def _validate_field_type(self, value: any, expected_type: str, field_name: str, original_text: str) -> tuple[any, float]:
        """
        Validate field type and compute confidence.

        Returns:
            (validated_value, confidence_score)
        """
        if value is None:
            return None, 0.0

        try:
            # Type conversion and validation
            if expected_type == "string":
                validated = str(value) if value else None
                confidence = 0.8 if validated else 0.0

            elif expected_type == "int":
                # Handle numeric strings
                if isinstance(value, str):
                    value = value.replace(",", "").strip()
                validated = int(float(value))
                confidence = 0.9  # High confidence if parseable

            elif expected_type == "float":
                if isinstance(value, str):
                    value = value.replace(",", "").strip()
                validated = float(value)
                confidence = 0.9

            elif expected_type == "bool":
                if isinstance(value, bool):
                    validated = value
                else:
                    validated = str(value).lower() in ["true", "yes", "1", "true"]
                confidence = 0.8

            elif expected_type == "list":
                if isinstance(value, list):
                    validated = value
                elif isinstance(value, str):
                    validated = [item.strip() for item in value.split(",")]
                else:
                    validated = [value]
                confidence = 0.7

            else:
                # Unknown type, keep as-is
                validated = value
                confidence = 0.5

            # Boost confidence if value appears in original text
            if validated and isinstance(validated, str):
                if validated.lower() in original_text.lower():
                    confidence = min(1.0, confidence + 0.1)

            return validated, confidence

        except (ValueError, TypeError):
            # Type conversion failed
            return None, 0.0
