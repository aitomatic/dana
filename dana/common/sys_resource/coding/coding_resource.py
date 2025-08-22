import os
import subprocess
import sys
import tempfile
from dana.common.mixins.tool_callable import ToolCallable
from dana.common.sys_resource.base_sys_resource import BaseSysResource
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest


class CodingResource(BaseSysResource):
    """Coding resource for generating and executing Python code from natural language requests."""

    def __init__(self, name: str = "coding_resource", description: str | None = None, debug: bool = True, timeout: int = 30, **kwargs):
        super().__init__(name, description)
        self.debug = debug
        self.timeout = timeout
        # Initialize LLM resource for code generation
        try:
            self._llm_resource = LLMResource(name=f"{name}_llm", description="LLM for code generation", **kwargs)
        except Exception as e:
            self.error(f"Failed to create LLM resource: {e}")
            self._llm_resource = None

        self._is_ready = False
        self._available_packages = None

    def _get_available_packages(self) -> list[str]:
        """Get list of available packages in the current environment."""

        # Fallback to common packages
        self._available_packages = [
            "os",
            "sys",
            "math",
            "random",
            "datetime",
            "json",
            "csv",
            "collections",
            "itertools",
            "functools",
            "re",
            "string",
            "numpy",
            "pandas",
            "matplotlib",
            "requests",
            "urllib",
        ]

        return self._available_packages

    async def initialize(self) -> None:
        """Initialize the coding resource and LLM."""
        await super().initialize()

        if self._llm_resource:
            try:
                await self._llm_resource.initialize()
                self._is_ready = True
                if self.debug:
                    print(f"Coding resource [{self.name}] initialized successfully")
            except Exception as e:
                self.error(f"Failed to initialize LLM resource: {e}")
                self._is_ready = False
        else:
            self.warning("No LLM resource available, coding resource will use fallback methods")
            self._is_ready = True

    @ToolCallable.tool
    async def execute_code(self, request: str, max_retries: int = 3) -> str:
        """Generate Python code from natural language request and execute it to get results. Useful for calculations, data analysis, etc. `request` should contain all necessary raw data. Do not precompute and always provide granularity, resolution, cadence, aggregation level, etc .. in the data. For example, quarterly revenue, annual revenue, ... DO NOT just provide : revenue without the granularity."""
        if not self._is_ready:
            await self.initialize()

        if self.debug:
            print(f"Executing Python code for request: \n```\n{request}\n```")

        last_error = None
        last_python_code = None

        for attempt in range(max_retries + 1):
            try:
                if attempt == 0:
                    # First attempt: generate and execute
                    python_code = await self._generate_python_code(request)
                else:
                    # Retry attempts: use error feedback to improve
                    python_code = await self._generate_python_code_with_feedback(request, last_error, last_python_code, attempt)

                # Execute the generated code with timeout
                result = self._execute_python_code(python_code, timeout=self.timeout)

                # Check if execution was successful
                if not result.startswith("Error:") and not result.startswith("TimeoutError:"):
                    if attempt > 0:
                        if self.debug:
                            print(f"Successfully executed code on attempt {attempt + 1}")
                    if self.debug:
                        print(f"Result: \n```\n{result}\n```")
                    return result
                else:
                    last_error = result
                    last_python_code = python_code

            except Exception as e:
                last_error = f"Error: {str(e)}"
                self.error(f"Attempt {attempt + 1} failed: {e}")

        # All attempts failed
        return f"Failed after {max_retries + 1} attempts. Last error: {last_error}"

    async def _generate_python_code(self, request: str) -> str:
        """Generate Python code from natural language request."""

        if self._llm_resource and self._llm_resource._is_available:
            return await self._generate_with_llm(request)
        else:
            # Only use fallback if LLM is completely unavailable
            return self._generate_fallback(request)

    async def _generate_with_llm(self, request: str) -> str:
        """Generate Python code using LLM."""

        # Get available packages
        available_packages = self._get_available_packages()
        packages_info = ", ".join(available_packages[:50])  # Limit to first 50 for readability
        if len(available_packages) > 50:
            packages_info += f" ... and {len(available_packages) - 50} more"

        prompt = f"""
# ROLE: You are a senior Python engineer.
# TASK: Write an *executable* Python 3.12 script that fulfils the user’s request.
# ENVIRONMENT PACKAGES: {packages_info}
# RULES (strict):
#  1. OUTPUT *ONLY* runnable Python code – no comments, markdown, or explanations.
#  2. Use only the packages listed above; fall back to the standard library if a needed package is missing.
#  3. Insert print() statements immediately after every logical step to display intermediate and final results. Provide granularity, resolution, cadence, aggregation level, etc .. in your print statements. For example, quarterly revenue, annual revenue, ... DO NOT just provide : revenue without the granularity.
#  4. Wrap risky operations in try/except blocks and print a helpful message on failure.
#  5. Keep the code concise, readable, and PEP-8 compliant.

# EXAMPLE REQUEST
#   Calculate the projected revenue for the next year based on a 20 % quarterly
#   growth rate applied to the latest quarterly revenue of $750 034.

# EXAMPLE OUTPUT (format only – do **NOT** include this example in your answer):
# def project_revenue(latest_q_rev: float, growth_rate: float, quarters: int = 4):
#     try:
#         for q in range(1, quarters + 1):
#             latest_q_rev *= (1 + growth_rate)
#             print(f"Q{{q}} projected revenue: {{latest_q_rev:,.2f}}")
#         annual_rev = latest_q_rev
#         print(f"Projected annual revenue after {{quarters}} quarters: {{annual_rev:,.2f}}")
#         return annual_rev
#     except Exception as e:
#         print(f"Error: {{e}}")
#
# print(project_revenue(750034, 0.20))

# USER REQUEST
{request}
```
"""

        llm_request = BaseRequest(
            arguments={
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            }
        )

        response = await self._llm_resource.query(llm_request)

        if response.success:
            content = response.content
            if isinstance(content, dict):
                if "choices" in content and content["choices"]:
                    code = content["choices"][0].get("message", {}).get("content", "")
                else:
                    for key in ["content", "text", "message", "result", "code"]:
                        if key in content:
                            code = content[key]
                            break
                    else:
                        code = str(content)
            else:
                code = str(content)

            return self._clean_code(code)
        else:
            self.error(f"LLM generation failed: {response.error}")
            raise Exception(f"LLM generation failed: {response.error}")

    async def _generate_python_code_with_feedback(self, request: str, last_error: str, last_python_code: str, attempt: int) -> str:
        """Generate Python code using LLM with error feedback from previous attempts."""

        # Get available packages
        available_packages = self._get_available_packages()
        packages_info = ", ".join(available_packages[:50])  # Limit to first 50 for readability
        if len(available_packages) > 50:
            packages_info += f" ... and {len(available_packages) - 50} more"

        prompt = f"""Generate Python code that: {request}

Available packages in this environment: {packages_info}

Previous attempt failed with error: {last_error}

Previous code that failed:
```python
{last_python_code}
```

This is attempt {attempt + 1}. Please fix the issues from the previous attempt:

Requirements:
- Return ONLY executable Python code
- No explanations or markdown formatting
- Include print statements to show results
- Handle basic errors gracefully
- Use simple, readable code
- Fix the specific error from the previous attempt
- ONLY use packages from the available list above
- If you need a package not in the list, use standard library alternatives

Common fixes:
- If syntax error: Check for missing colons, parentheses, or indentation
- If import error: Use only standard library modules or handle missing imports
- If runtime error: Add proper error handling and validation
- If logic error: Simplify the approach and add debugging prints

Example output format:
```python
def calculate_factorial(n):
    if n < 0:
        return "Error: Negative number"
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

print(calculate_factorial(5))
```
"""

        llm_request = BaseRequest(
            arguments={
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,  # Lower temperature for more focused fixes
            }
        )

        response = await self._llm_resource.query(llm_request)

        if response.success:
            content = response.content
            if isinstance(content, dict):
                if "choices" in content and content["choices"]:
                    code = content["choices"][0].get("message", {}).get("content", "")
                else:
                    for key in ["content", "text", "message", "result", "code"]:
                        if key in content:
                            code = content[key]
                            break
                    else:
                        code = str(content)
            else:
                code = str(content)

            return self._clean_code(code)
        else:
            self.error(f"LLM generation with feedback failed: {response.error}")
            raise Exception(f"LLM generation with feedback failed: {response.error}")

    def _generate_fallback(self, request: str) -> str:
        """Generate simple Python code when LLM is not available."""

        return f'''def process_request():
    """{request}"""
    print("Processing request...")
    return "Result: Request processed"

print(process_request())
'''

    def _clean_code(self, code: str) -> str:
        """Clean up generated code by removing markdown formatting."""

        # Remove markdown code blocks
        if "```python" in code:
            start = code.find("```python") + 9
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()

        return code.strip()

    def _execute_python_code(self, code: str, timeout: int = 30) -> str:
        """
        Execute Python code and return the result. If execution exceeds timeout, returns TimeoutError.
        Args:
            code: Python code to execute
            timeout: Maximum seconds to allow code execution
        Returns:
            Output string, or TimeoutError string if timed out
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = f.name
            # Execute the code
            result = subprocess.run([sys.executable, temp_file], capture_output=True, text=True, timeout=timeout)
            # Clean up
            os.unlink(temp_file)
            # Return output
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "TimeoutError: Code execution timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    async def cleanup(self) -> None:
        """Clean up the coding resource."""
        if self._llm_resource:
            await self._llm_resource.cleanup()
        await super().cleanup()
        if self.debug:
            print(f"Coding resource [{self.name}] cleaned up")

    async def query(self, request: str) -> None:
        """Query the coding resource."""
        pass
