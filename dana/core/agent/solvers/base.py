from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance
from dana.core.workflow.workflow_system import WorkflowInstance
from dana.registry import WorkflowRegistry, ResourceRegistry

if TYPE_CHECKING:
    from dana.core.agent.agent_instance import AgentInstance


# ---------------------------
# Signature Matcher (kept for backward compatibility)
# ---------------------------
class SignatureMatcher:
    """Strongly-typed signature matcher for issue patterns."""

    def __init__(self):
        self._patterns: dict[str, dict[str, Any]] = {}

    def add_pattern(self, pattern_id: str, pattern_data: dict[str, Any]) -> None:
        """Add a signature pattern."""
        self._patterns[pattern_id] = pattern_data

    def match(self, text: str, entities: dict[str, Any]) -> tuple[float, dict[str, Any] | None]:
        """Match text against known issue signatures.

        Args:
            text: The text to match
            entities: Context entities for matching

        Returns:
            Tuple of (confidence_score, match_data or None)
        """
        text_lower = text.lower()
        best_score = 0.0
        best_match = None

        for pattern_data in self._patterns.values():
            # Simple keyword matching - can be enhanced
            keywords = pattern_data.get('keywords', [])
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)

            if matches > 0:
                score = min(0.3 + (matches * 0.2), 1.0)
                if score > best_score:
                    best_score = score
                    best_match = pattern_data

        return best_score, best_match


class BaseSolver(ABC):
    def __init__(self, agent: "AgentInstance", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent
        self._llm_resource = None
        self.llm_resource = self.agent._llm_resource

    @property
    def llm_resource(self) -> "LLMResourceInstance":
        """Get the LLM resource for this solver."""
        if self._llm_resource is None:
            self._llm_resource = self.agent._llm_resource

        if self._llm_resource is None:
            self._llm_resource = LLMResourceInstance.create_default_instance()

        return self._llm_resource

    @llm_resource.setter
    def llm_resource(self, value: "LLMResourceInstance"):
        """Set the LLM resource for this solver."""
        self._llm_resource = value

    @abstractmethod
    def solve_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> Any:
        """Implementation of solve functionality."""
        pass

    def plan_sync(
        self,
        problem_or_workflow: str | WorkflowInstance,
        artifacts: dict[str, Any] | None = None,
        sandbox_context: SandboxContext | None = None,
        **kwargs,
    ) -> WorkflowInstance | None:
        """Implementation of plan functionality."""
        return None

    # ---------------------------
    # Common workflow execution
    # ---------------------------
    def _run_workflow_instance(self, wf: WorkflowInstance, sandbox_context: SandboxContext | None) -> dict[str, Any]:
        """Execute a workflow instance, handling both run() and execute() methods."""
        try:
            if hasattr(wf, "run"):
                out = wf.run(context=sandbox_context)  # type: ignore[arg-type]
            elif hasattr(wf, "execute"):
                out = wf.execute(context=sandbox_context)  # type: ignore[arg-type]
            else:
                out = {"status": "error", "message": "WorkflowInstance has no run/execute()."}
            return {"status": "ok", "output": out, "name": getattr(wf, "name", None)}
        except Exception as e:
            return {"status": "error", "message": str(e), "name": getattr(wf, "name", None)}

    # ---------------------------
    # Common resource management
    # ---------------------------
    def _attach_resource_pack(self, resource_registry: ResourceRegistry | None, entities: dict[str, Any], artifacts: dict[str, Any]) -> None:
        """Attach resource pack to artifacts if resource registry is available."""
        if resource_registry is not None:
            try:
                resources = resource_registry.pack_resources_for_llm(entities)
                artifacts["_resources"] = resources
            except Exception:
                artifacts.setdefault("_resources", {})

    # ---------------------------
    # Common dependency injection
    # ---------------------------
    def _inject_dependencies(self, **kwargs: Any) -> tuple[WorkflowRegistry | None, ResourceRegistry | None, SignatureMatcher | None]:
        """Inject dependencies from kwargs or fall back to instance attributes."""
        # Use __dict__ to avoid triggering __getattr__ recursion
        workflow_registry = kwargs.get("workflow_registry") or self.__dict__.get("workflow_registry", None)
        resource_registry = kwargs.get("resource_registry") or self.__dict__.get("resource_registry", None)
        signature_matcher = kwargs.get("signature_matcher") or self.__dict__.get("signature_matcher", None)
        return workflow_registry, resource_registry, signature_matcher

    # ---------------------------
    # Common workflow execution patterns
    # ---------------------------
    def _handle_direct_workflow_execution(
        self,
        problem_or_workflow: str | WorkflowInstance,
        sandbox_context: SandboxContext | None,
        artifacts: dict[str, Any],
        mode: str = "workflow",
    ) -> dict[str, Any] | None:
        """Handle direct workflow execution if input is a WorkflowInstance."""
        if isinstance(problem_or_workflow, WorkflowInstance):
            result = self._run_workflow_instance(problem_or_workflow, sandbox_context)
            # Handle case where artifacts might be a SandboxContext object
            if hasattr(artifacts, 'setdefault'):
                st = artifacts.setdefault("_solver_state", {})
                st.update({"mode": mode, "last_result": result, "phase": "delivered"})
            else:
                # If artifacts is not a dict-like object, create a new state dict
                st = {"mode": mode, "last_result": result, "phase": "delivered"}
            return {
                "type": "answer",
                "mode": mode,
                "result": result,
                "artifacts": artifacts,
            }
        return None

    def _match_known_workflow(
        self, query: str, entities: dict[str, Any], workflow_registry: WorkflowRegistry | None, known_match_threshold: float = 0.75
    ) -> tuple[float, WorkflowInstance | None]:
        """Match a query against known workflows in the registry."""
        if workflow_registry is None:
            return 0.0, None

        try:
            score, wf, metadata = workflow_registry.match_workflow_for_llm(query, entities)
            return float(score), wf if wf is not None and score >= known_match_threshold else None
        except Exception:
            return 0.0, None

    # ---------------------------
    # Common state management
    # ---------------------------
    def _initialize_solver_state(self, artifacts: dict[str, Any], state_key: str = "_solver_state") -> dict[str, Any]:
        """Initialize solver state in artifacts."""
        # Handle case where artifacts might be a SandboxContext object
        if hasattr(artifacts, 'get') and hasattr(artifacts, 'setdefault'):
            # It's a dictionary-like object - modify it in place
            return artifacts.setdefault(state_key, {})
        elif hasattr(artifacts, 'get') and not hasattr(artifacts, 'setdefault'):
            # It's a SandboxContext object - create a new dict for solver state
            return {}
        else:
            # It's None or not the expected type - create a new dict
            artifacts = artifacts or {}
            return artifacts.setdefault(state_key, {})

    def _extract_entities(self, artifacts: dict[str, Any]) -> dict[str, Any]:
        """Extract entities from artifacts."""
        # Handle case where artifacts might be a SandboxContext object
        if hasattr(artifacts, 'get') and hasattr(artifacts, 'setdefault'):
            # It's a dictionary-like object
            return artifacts.get("_entities", {})
        elif hasattr(artifacts, 'get') and not hasattr(artifacts, 'setdefault'):
            # It's a SandboxContext object - return empty entities
            return {}
        else:
            # It's None or not the expected type
            artifacts = artifacts or {}
            return artifacts.get("_entities", {})

    # ---------------------------
    # Common response patterns
    # ---------------------------
    def _create_ask_response(self, message: str, missing: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        """Create a standardized ask response."""
        response: dict[str, Any] = {
            "type": "ask",
            "message": message,
        }
        if missing:
            response["missing"] = missing
        response.update(kwargs)
        return response

    def _create_answer_response(self, mode: str, artifacts: dict[str, Any], selected: str, **kwargs: Any) -> dict[str, Any]:
        """Create a standardized answer response."""
        return {
            "type": "answer",
            "mode": mode,
            "artifacts": artifacts,
            **kwargs,
        }

    # ---------------------------
    # Common conversation handling
    # ---------------------------
    def _is_conversation_termination(self, message: str) -> bool:
        """Check if message is a conversation termination command."""
        message_lower = message.lower().strip()

        # Common conversation termination commands
        termination_commands = [
            "quit",
            "exit",
            "bye",
            "goodbye",
            "good bye",
            "see you later",
            "talk to you later",
            "end",
            "stop",
            "done",
            "finished",
            "that's all",
            "that is all",
        ]

        return message_lower in termination_commands

    def _get_conversation_context(self, max_turns: int = 30) -> str:
        """Get conversation context from agent timeline."""
        try:
            if hasattr(self.agent, "state") and hasattr(self.agent.state, "timeline"):
                context_string = self.agent.state.timeline.get_conversation_turns(max_turns=max_turns)
                if context_string:
                    return f"\n\nPrevious conversation context:\n{context_string}"
        except Exception:
            pass
        return ""

    # ---------------------------
    # Common LLM handling
    # ---------------------------
    def _validate_llm_resource(self) -> bool:
        """Validate that LLM resource is available."""
        return hasattr(self, "llm_resource") and self.llm_resource is not None

    def _create_llm_request(self, messages: list[dict], system_prompt: str | None = None) -> Any:
        """Create a BaseRequest for LLM interaction."""
        from dana.common.types import BaseRequest

        # Add system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        return BaseRequest(arguments={"messages": messages})

    def _extract_llm_response_content(self, response: Any) -> str | None:
        """Extract text content from various LLM response formats."""
        try:
            # Handle BaseResponse object
            if hasattr(response, "success") and not response.success:
                return None

            # Handle different response types
            if hasattr(response, "content") and isinstance(response.content, str):
                return response.content
            elif hasattr(response, "content") and isinstance(response.content, dict):
                # Handle OpenAI-style response with choices
                if "choices" in response.content and len(response.content["choices"]) > 0:
                    choice = response.content["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
            elif hasattr(response, "text"):
                return response.text
            elif isinstance(response, str):
                return response
            else:
                return str(response)
        except Exception:
            return None

    def _generate_llm_response_with_context(self, prompt: str, system_prompt: str | None = None, max_turns: int = 30) -> str | None:
        """Generate LLM response with conversation context."""
        if not self._validate_llm_resource():
            return None

        try:
            # Build conversation context
            conversation_context = self._get_conversation_context(max_turns)

            # Create enhanced system prompt with conversation context
            enhanced_system_prompt = system_prompt or ""
            if conversation_context:
                enhanced_system_prompt = f"{enhanced_system_prompt}\n\n{conversation_context}"

            # Debug prints
            print("=" * 80)
            print("🔧 [DEBUG] LLM REQUEST DETAILS")
            print("=" * 80)
            print(f"📋 SYSTEM_PROMPT:\n{enhanced_system_prompt}")
            print("-" * 80)
            print(f"👤 USER_PROMPT:\n{prompt}")
            print("-" * 80)

            # Create request with clean user message and enhanced system prompt
            request = self._create_llm_request([{"role": "user", "content": prompt}], enhanced_system_prompt)

            # Query LLM
            if self.agent._llm_resource is None:
                return None
            response = self.agent._llm_resource.query_sync(request)

            # Extract content
            llm_response = self._extract_llm_response_content(response)

            # Debug print for response
            print(f"🤖 LLM_RESPONSE:\n{llm_response}")
            print("=" * 80)

            return llm_response

        except Exception as e:
            print(f"❌ [DEBUG] LLM request failed: {e}")
            return None

    # ---------------------------
    # Common logging
    # ---------------------------
    def _log_solver_phase(self, phase: str, message: str, emoji: str = "🔧") -> None:
        """Log solver phase with optional emoji prefix."""
        print(f"{emoji} [{phase.upper()}] {message}")
