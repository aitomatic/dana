from typing import Any, Protocol
from abc import ABC, abstractmethod

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance
from dana.core.workflow.workflow_system import WorkflowInstance
from dana.frameworks.ctxeng import ContextEngineer


# ---------------------------
# Formal Interfaces
# ---------------------------
class WorkflowCatalog(Protocol):
    """Protocol for workflow catalog implementations."""

    def match(self, query: str, entities: dict[str, Any]) -> tuple[float, WorkflowInstance | None]:
        """Match a query against known workflows.

        Args:
            query: The search query
            entities: Context entities for matching

        Returns:
            Tuple of (confidence_score, WorkflowInstance or None)
        """
        ...

    def expand_step(self, step_text: str, entities: dict[str, Any]) -> WorkflowInstance | None:
        """Expand a step into a known workflow.

        Args:
            step_text: The step description
            entities: Context entities for expansion

        Returns:
            WorkflowInstance if expansion successful, None otherwise
        """
        ...


class SignatureMatcher(Protocol):
    """Protocol for signature matcher implementations."""

    def match(self, text: str, entities: dict[str, Any]) -> tuple[float, dict[str, Any] | None]:
        """Match text against known issue signatures.

        Args:
            text: The text to match
            entities: Context entities for matching

        Returns:
            Tuple of (confidence_score, match_data or None)
        """
        ...


class ResourceIndex(Protocol):
    """Protocol for resource index implementations."""

    def pack(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Pack resources based on entities.

        Args:
            entities: Context entities for resource selection

        Returns:
            Dictionary of packed resources (docs, kb, specs, etc.)
        """
        ...


class BaseSolverMixin(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context_engineer = None
        self._llm_resource: LLMResourceInstance | None = getattr(self, "_llm_resource", None)

    @property
    def context_engineer(self) -> ContextEngineer:
        """Get or create the context engineer for this agent."""
        if self._context_engineer is None:
            self._context_engineer = ContextEngineer.from_agent(self)
        return self._context_engineer

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
    def _attach_resource_pack(self, resource_index: ResourceIndex | None, entities: dict[str, Any], artifacts: dict[str, Any]) -> None:
        """Attach resource pack to artifacts if resource index is available."""
        if resource_index is not None:
            try:
                resources = resource_index.pack(entities)
                artifacts["_resources"] = resources
            except Exception:
                artifacts.setdefault("_resources", {})

    # ---------------------------
    # Common dependency injection
    # ---------------------------
    def _inject_dependencies(self, **kwargs: Any) -> tuple[WorkflowCatalog | None, ResourceIndex | None, SignatureMatcher | None]:
        """Inject dependencies from kwargs or fall back to instance attributes."""
        # Use __dict__ to avoid triggering __getattr__ recursion
        workflow_catalog = kwargs.get("workflow_catalog") or self.__dict__.get("workflow_catalog", None)
        resource_index = kwargs.get("resource_index") or self.__dict__.get("resource_index", None)
        signature_matcher = kwargs.get("signature_matcher") or self.__dict__.get("signature_matcher", None)
        return workflow_catalog, resource_index, signature_matcher

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
                "telemetry": {"mixin": self.MIXIN_NAME, "selected": "direct"},
                "artifacts": artifacts,
            }
        return None

    def _match_known_workflow(
        self, query: str, entities: dict[str, Any], workflow_catalog: WorkflowCatalog | None, known_match_threshold: float = 0.75
    ) -> tuple[float, WorkflowInstance | None]:
        """Match a query against known workflows in the catalog."""
        if workflow_catalog is None:
            return 0.0, None

        try:
            score, wf = workflow_catalog.match(query, entities)
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
        response = {
            "type": "ask",
            "message": message,
            "telemetry": {"mixin": self.MIXIN_NAME},
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
            "telemetry": {"mixin": self.MIXIN_NAME, "selected": selected},
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

    def _get_conversation_context(self, max_turns: int = 3) -> str:
        """Get conversation context from agent timeline."""
        try:
            if hasattr(self, "state") and hasattr(self.state, "timeline"):
                context_string = self.state.timeline.get_conversation_context(max_turns=max_turns)
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
        return hasattr(self, "_llm_resource") and self._llm_resource is not None

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

    def _generate_llm_response_with_context(self, prompt: str, system_prompt: str | None = None, max_turns: int = 3) -> str | None:
        """Generate LLM response with conversation context."""
        if not self._validate_llm_resource():
            return None

        try:
            # Build conversation context
            conversation_context = self._get_conversation_context(max_turns)

            # Create full prompt with context
            full_prompt = f"{prompt}{conversation_context}"

            # Create request
            request = self._create_llm_request([{"role": "user", "content": full_prompt}], system_prompt)

            # Query LLM
            if self._llm_resource is None:
                return None
            response = self._llm_resource.query_sync(request)

            # Extract content
            return self._extract_llm_response_content(response)

        except Exception:
            return None

    # ---------------------------
    # Common logging
    # ---------------------------
    def _log_solver_phase(self, phase: str, message: str, emoji: str = "🔧") -> None:
        """Log solver phase with optional emoji prefix."""
        print(f"{emoji} [{phase.upper()}] {message}")
