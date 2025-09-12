from typing import cast

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance


class ReasonMixin:
    def reason_sync(
        self,
        premise: str,
        sandbox_context: SandboxContext | None = None,
        problem_context: dict | None = None,
        system_message: str | None = None,
    ) -> dict:
        """Synchronous agent reasoning method."""
        self.debug(f"REASON: Analyzing premise: '{premise}'")
        self.debug(f"Context: {problem_context}")

        try:
            # Use py_reason() for LLM-powered reasoning
            from dana.libs.corelib.py_wrappers.py_reason import py_reason

            self.debug("Calling py_reason() for LLM-powered analysis...")
            self.debug(f"Premise length: {len(premise)}")
            self.debug(f"Sandbox context: {type(sandbox_context)}")

            options = {
                "temperature": 0.3,  # Lower temperature for more focused reasoning
                "max_tokens": 800,
            }
            if system_message:
                options["system_message"] = system_message

            py_reason_result = py_reason(
                sandbox_context,
                premise,
                options=options,
                llm_resource=self.llm_resource,
            )
            self.debug("py_reason() call successful")
            self.debug(f"Response type: {type(py_reason_result)}")
            self.debug(f"py_reason result: {py_reason_result}")

            return py_reason_result

        except Exception as e:
            self.error(f"LLM reasoning failed: {e}")
            # Fallback to basic reasoning
            return {
                "analysis": f"Fallback analysis of: {premise}",
                "reasoning_chain": [
                    f"LLM reasoning failed: {e}",
                    f"Applied {self.__struct_type__.name} fallback reasoning",
                    "Used basic logical analysis",
                ],
                "confidence": 0.6,
                "conclusion": f"Reasoning completed with fallback for: {premise}",
                "methodology": "fallback_reasoning",
                "agent": self.__struct_type__.name,
                "error": str(e),
            }
