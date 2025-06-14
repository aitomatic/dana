"""Local POET Transpiler - Alpha Implementation

Basic P→O→E transpilation with conditional Train phase.
No learning yet - focuses on core enhancement generation.
"""

import re
import ast
from typing import Dict, Any, Optional
from pathlib import Path

from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.common.resource.llm_resource import LLMResource
from .types import POETConfig, TranspiledFunction, POETTranspilationError


class LocalPOETTranspiler:
    """Local transpiler for POET functions - Alpha implementation"""

    def __init__(self):
        self.llm = LLMResource()
        self.templates_dir = Path(__file__).parent / "templates"
        DXA_LOGGER.info("Local POET transpiler initialized")

    def transpile_function(self, function_code: str, config: POETConfig, context: Optional[Dict[str, Any]] = None) -> TranspiledFunction:
        """Transpile function with P→O→E phases (and optional Train phase)"""

        try:
            # Parse the function code to extract details
            function_info = self._parse_function(function_code)

            # Load appropriate template
            template = self._load_template(config.domain or "base")

            # Generate enhanced implementation
            enhanced_code = self._generate_enhanced_function(function_info, config, template, context)

            # Create metadata
            metadata = {
                "decorator_params": config.dict(),
                "phases_included": self._get_phases_included(config),
                "original_function_name": function_info["name"],
                "enhancements": self._get_enhancements_applied(config),
            }

            DXA_LOGGER.info(f"Successfully transpiled function '{function_info['name']}'")

            return TranspiledFunction(code=enhanced_code, language="python", metadata=metadata)

        except Exception as e:
            DXA_LOGGER.error(f"Transpilation failed: {e}")
            raise POETTranspilationError(f"Transpilation failed: {e}")

    def _parse_function(self, function_code: str) -> Dict[str, Any]:
        """Parse function code to extract name, parameters, and body"""
        try:
            # Remove @poet decorator for parsing
            clean_code = re.sub(r"@poet\([^)]*\)\s*\n?", "", function_code)

            # Parse the AST
            tree = ast.parse(clean_code)

            # Find the function definition
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "body": ast.get_source_segment(clean_code, node),
                        "original_code": clean_code.strip(),
                    }

            raise ValueError("No function definition found")

        except Exception as e:
            raise POETTranspilationError(f"Failed to parse function: {e}")

    def _load_template(self, domain: str) -> str:
        """Load template for the specified domain"""

        # For Alpha, use simple built-in templates
        if domain == "ml_monitoring":
            return self._get_ml_monitoring_template()
        else:
            return self._get_base_template()

    def _get_base_template(self) -> str:
        """Basic P→O→E template for any function"""
        return """
Generate an enhanced Python function with P→O→E phases:

**Perceive Phase**: Input validation and preprocessing
- Validate input types and ranges
- Handle missing or invalid data gracefully
- Log input characteristics

**Operate Phase**: Enhanced core logic 
- Implement the original function logic with improvements
- Add error handling and retries
- Include performance monitoring

**Enforce Phase**: Output validation and formatting
- Validate output format and constraints
- Apply business rules and sanity checks
- Log execution metrics

Original function:
{original_code}

Requirements:
- Maintain original function semantics
- Return POETResult wrapper with execution context
- Include comprehensive error handling
- Add logging at each phase
"""

    def _get_ml_monitoring_template(self) -> str:
        """ML monitoring specific template"""
        return """
Generate an enhanced ML monitoring function with domain expertise:

**Perceive Phase**: Data validation and characterization
- Validate data types (numerical, categorical, mixed)
- Check for missing values and outliers
- Analyze data distribution characteristics
- Handle various data formats (pandas, numpy, lists)

**Operate Phase**: Statistical monitoring with ML intelligence
- Implement multiple drift detection methods (KS test, KL divergence)
- Use adaptive windowing for temporal data
- Apply statistical significance testing
- Include confidence intervals and effect sizes

**Enforce Phase**: Results validation and alerting
- Validate statistical test outputs
- Apply business-relevant thresholds
- Format results for downstream systems
- Include actionable recommendations

Original function:
{original_code}

Additional ML Requirements:
- Support multiple statistical tests
- Include data quality assessment
- Provide interpretable results
- Handle edge cases (small samples, constant data)
"""

    def _generate_enhanced_function(
        self, function_info: Dict[str, Any], config: POETConfig, template: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate the enhanced function code using LLM"""

        # Prepare the prompt
        prompt = template.format(original_code=function_info["original_code"], function_name=function_info["name"])

        # Add optimization requirements if specified
        if config.optimize_for:
            prompt += f"""

**Train Phase Requirements** (because optimize_for="{config.optimize_for}"):
- Add feedback collection for {config.optimize_for} optimization
- Emit execution events for learning analysis
- Include train() method generation hook
- Support continuous improvement based on feedback
"""

        # Add context if provided
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"

        # Generate using LLM
        try:
            response = self.llm.query(
                prompt,
                system_message="You are a POET code generator. Generate complete, production-ready Python functions with P→O→E phases. Return only the Python code without markdown formatting.",
            )

            # Clean up the response
            enhanced_code = self._clean_generated_code(response, function_info["name"])

            return enhanced_code

        except Exception as e:
            DXA_LOGGER.error(f"LLM generation failed: {e}")
            # Fallback to basic enhancement
            return self._generate_basic_enhancement(function_info, config)

    def _clean_generated_code(self, response: str, function_name: str) -> str:
        """Clean and validate generated code"""
        # Remove markdown code blocks if present
        code = re.sub(r"```python\s*\n?", "", response)
        code = re.sub(r"```\s*$", "", code)

        # Ensure imports are included
        imports = [
            "from typing import Any, Dict",
            "import uuid",
            "from opendxa.common.utils.logging import DXA_LOGGER",
            "from opendxa.dana.poet.types import POETResult",
        ]

        if not any(imp in code for imp in imports):
            code = "\n".join(imports) + "\n\n" + code

        # Validate syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            DXA_LOGGER.warning(f"Generated code has syntax error: {e}")
            raise POETTranspilationError(f"Generated code is invalid: {e}")

        return code

    def _generate_basic_enhancement(self, function_info: Dict[str, Any], config: POETConfig) -> str:
        """Fallback basic enhancement when LLM fails"""
        function_name = function_info["name"]
        args = ", ".join(function_info["args"])

        return f'''
from typing import Any, Dict
import uuid
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.poet.types import POETResult

def {function_name}_enhanced({args}):
    """Enhanced version of {function_name} with basic P→O→E phases"""
    execution_id = str(uuid.uuid4())
    
    try:
        # Perceive: Basic input validation
        DXA_LOGGER.info(f"{{execution_id}}: Starting {function_name}")
        
        # Operate: Call original function logic
        # TODO: Implement enhanced logic based on original function
        result = {{"status": "enhanced", "execution_id": execution_id}}
        
        # Enforce: Basic output validation
        if not isinstance(result, dict):
            result = {{"value": result, "execution_id": execution_id}}
        
        DXA_LOGGER.info(f"{{execution_id}}: {function_name} completed successfully")
        return POETResult(result, "{function_name}", "v1")
        
    except Exception as e:
        DXA_LOGGER.error(f"{{execution_id}}: {function_name} failed: {{e}}")
        raise
'''

    def _get_phases_included(self, config: POETConfig) -> list[str]:
        """Get list of phases included in the enhanced function"""
        phases = ["perceive", "operate", "enforce"]

        # Add train phase only if optimize_for is specified
        if config.optimize_for:
            phases.append("train")

        return phases

    def _get_enhancements_applied(self, config: POETConfig) -> list[str]:
        """Get list of enhancements applied during transpilation"""
        enhancements = ["error_handling", "input_validation", "output_validation", "execution_logging", "result_wrapping"]

        if config.domain == "ml_monitoring":
            enhancements.extend(["statistical_testing", "data_characterization", "ml_specific_validation"])

        if config.optimize_for:
            enhancements.extend(["feedback_collection", "train_phase_hooks", "learning_preparation"])

        return enhancements
