from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.resource.builtins.llm_resource_instance import LLMResourceInstance
from dana.core.workflow.workflow_system import WorkflowInstance
from dana.registry import WorkflowRegistry, ResourceRegistry

if TYPE_CHECKING:
    from dana.core.agent.agent_instance import AgentInstance


# ---------------------------
# Solver Response Standardization
# ---------------------------
class SolverResponse:
    """Standardized response format for all solvers."""

    def __init__(self, content: str, response_type: str = "answer", metadata: dict | None = None):
        self.content = content  # Always a string for display
        self.response_type = response_type  # "answer", "ask", "error"
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation for display."""
        return self.content

    def to_dict(self) -> dict:
        """Dictionary representation for programmatic use."""
        return {"type": self.response_type, "content": self.content, "metadata": self.metadata}

    def is_answer(self) -> bool:
        """Check if this is an answer response."""
        return self.response_type == "answer"

    def is_ask(self) -> bool:
        """Check if this is an ask response."""
        return self.response_type == "ask"

    def is_error(self) -> bool:
        """Check if this is an error response."""
        return self.response_type == "error"


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
            keywords = pattern_data.get("keywords", [])
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
        self.llm_resource = self.agent.llm_resource

    @property
    def llm_resource(self) -> "LLMResourceInstance":
        """Get the LLM resource for this solver."""
        if self._llm_resource is None:
            agent_llm = self.agent.llm_resource
            if agent_llm is not None and isinstance(agent_llm, LLMResourceInstance):
                self._llm_resource = agent_llm
            else:
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
    def _attach_resource_pack(
        self, resource_registry: ResourceRegistry | None, entities: dict[str, Any], artifacts: dict[str, Any]
    ) -> None:
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
            if hasattr(artifacts, "setdefault"):
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
        if hasattr(artifacts, "get") and hasattr(artifacts, "setdefault"):
            # It's a dictionary-like object - modify it in place
            return artifacts.setdefault(state_key, {})
        elif hasattr(artifacts, "get") and not hasattr(artifacts, "setdefault"):
            # It's a SandboxContext object - create a new dict for solver state
            return {}
        else:
            # It's None or not the expected type - create a new dict
            artifacts = artifacts or {}
            return artifacts.setdefault(state_key, {})

    def _extract_entities(self, artifacts: dict[str, Any]) -> dict[str, Any]:
        """Extract entities from artifacts."""
        # Handle case where artifacts might be a SandboxContext object
        if hasattr(artifacts, "get") and hasattr(artifacts, "setdefault"):
            # It's a dictionary-like object
            return artifacts.get("_entities", {})
        elif hasattr(artifacts, "get") and not hasattr(artifacts, "setdefault"):
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
        """Create a standardized ask response (legacy format)."""
        response: dict[str, Any] = {
            "type": "ask",
            "message": message,
        }
        if missing:
            response["missing"] = missing
        response.update(kwargs)
        return response

    def _create_answer_response(self, mode: str, artifacts: dict[str, Any], selected: str, **kwargs: Any) -> dict[str, Any]:
        """Create a standardized answer response (legacy format)."""
        return {
            "type": "answer",
            "mode": mode,
            "artifacts": artifacts,
            **kwargs,
        }

    # ---------------------------
    # New standardized response methods
    # ---------------------------
    def _create_solver_response(self, content: str, response_type: str = "answer", metadata: dict | None = None) -> SolverResponse:
        """Create a standardized SolverResponse."""
        return SolverResponse(content, response_type, metadata)

    def _create_solver_ask_response(self, message: str, missing: list[str] | None = None, **kwargs: Any) -> SolverResponse:
        """Create a standardized ask response using SolverResponse."""
        metadata = kwargs.copy()
        if missing:
            metadata["missing"] = missing
        return SolverResponse(message, "ask", metadata)

    def _create_solver_answer_response(self, content: str, mode: str = "solver", **kwargs: Any) -> SolverResponse:
        """Create a standardized answer response using SolverResponse."""
        metadata = kwargs.copy()
        metadata["mode"] = mode
        return SolverResponse(content, "answer", metadata)

    def _create_solver_error_response(self, message: str, error: Exception | None = None, **kwargs: Any) -> SolverResponse:
        """Create a standardized error response using SolverResponse."""
        metadata = kwargs.copy()
        if error:
            metadata["error"] = str(error)
            metadata["error_type"] = type(error).__name__
        return SolverResponse(message, "error", metadata)

    # ---------------------------
    # Recursion handling
    # ---------------------------
    def _check_recursion_limit(self, artifacts: dict[str, Any], max_depth: int = 3, state_key: str = "_solver_state") -> tuple[bool, int]:
        """Check if recursion limit has been reached and return current depth."""
        st = self._initialize_solver_state(artifacts, state_key)
        current_depth = st.get("recursion_depth", 0)

        if current_depth >= max_depth:
            return True, current_depth

        # Increment recursion depth for this call
        st["recursion_depth"] = current_depth + 1
        return False, current_depth + 1

    def _create_recursion_limit_response(self, problem: str, max_depth: int, mode: str = "solver") -> SolverResponse:
        """Create a standardized recursion limit response."""
        message = f"Recursion limit reached ({max_depth} levels) for: {problem}"
        metadata = {"recursion_limit": True, "max_depth": max_depth, "problem": str(problem), "mode": mode}
        return SolverResponse(message, "error", metadata)

    def _prepare_recursive_call(
        self,
        subgoal: str,
        parent_artifacts: dict[str, Any],
        entities: dict[str, Any],
        recursion_depth: int,
        state_key: str = "_solver_state",
    ) -> dict[str, Any]:
        """Prepare artifacts for recursive solver calls."""
        child_artifacts = {
            "_entities": entities,
            state_key: {"recursion_depth": recursion_depth},
            "_parent_goal": parent_artifacts.get(state_key, {}).get("goal", ""),
            "_call_stack": parent_artifacts.get("_call_stack", []) + [subgoal],
        }
        return child_artifacts

    # ---------------------------
    # Error handling
    # ---------------------------
    def _handle_llm_failure(self, error: Exception, context: str = "LLM operation", fallback_message: str | None = None) -> SolverResponse:
        """Handle LLM failures with standardized error response."""
        if fallback_message is None:
            fallback_message = (
                "I'm having trouble processing your request right now. Could you try rephrasing it or providing more details?"
            )

        metadata = {"error_type": "llm_failure", "context": context, "original_error": str(error)}

        self._log_solver_phase("ERROR", f"LLM failure in {context}: {error}", "❌")
        return self._create_solver_error_response(fallback_message, None, **metadata)

    def _handle_missing_dependencies(self, missing: list[str], context: str = "solver operation") -> SolverResponse:
        """Handle missing dependencies with standardized error response."""
        if not missing:
            missing = ["required dependencies"]

        message = f"I need more information to help you: {', '.join(missing)}"
        metadata = {"error_type": "missing_dependencies", "context": context, "missing": missing}

        self._log_solver_phase("ERROR", f"Missing dependencies in {context}: {missing}", "❌")
        return self._create_solver_error_response(message, **metadata)

    def _handle_workflow_failure(
        self, error: Exception, workflow_name: str = "workflow", context: str = "workflow execution"
    ) -> SolverResponse:
        """Handle workflow execution failures with standardized error response."""
        message = f"I encountered an issue while running {workflow_name}. Let me try a different approach."
        metadata = {"error_type": "workflow_failure", "context": context, "workflow_name": workflow_name, "original_error": str(error)}

        self._log_solver_phase("ERROR", f"Workflow failure in {context} ({workflow_name}): {error}", "❌")
        return self._create_solver_error_response(message, None, **metadata)

    def _handle_parsing_failure(self, error: Exception, data_type: str = "response", context: str = "data parsing") -> SolverResponse:
        """Handle data parsing failures with standardized error response."""
        message = f"I had trouble understanding the {data_type}. Let me try a different approach."
        metadata = {"error_type": "parsing_failure", "context": context, "data_type": data_type, "original_error": str(error)}

        self._log_solver_phase("ERROR", f"Parsing failure in {context} ({data_type}): {error}", "❌")
        return self._create_solver_error_response(message, None, **metadata)

    def _handle_general_error(
        self, error: Exception, context: str = "solver operation", user_friendly_message: str | None = None
    ) -> SolverResponse:
        """Handle general errors with standardized error response."""
        if user_friendly_message is None:
            user_friendly_message = "I encountered an unexpected issue. Let me try to help you in a different way."

        metadata = {"error_type": "general_error", "context": context, "original_error": str(error)}

        self._log_solver_phase("ERROR", f"General error in {context}: {error}", "❌")
        return self._create_solver_error_response(user_friendly_message, None, **metadata)

    def _safe_execute(
        self, operation: callable, error_context: str = "operation", fallback_response: str | None = None
    ) -> SolverResponse | Any:
        """Safely execute an operation with standardized error handling."""
        try:
            return operation()
        except Exception as e:
            if fallback_response:
                return self._create_solver_error_response(fallback_response, e, context=error_context)
            else:
                return self._handle_general_error(e, error_context)

    # ---------------------------
    # Artifact validation and processing
    # ---------------------------
    def _validate_and_prepare_artifacts(self, artifacts: dict[str, Any] | None, required_fields: list[str] | None = None) -> dict[str, Any]:
        """Validate and prepare artifacts with standardized processing."""
        # Handle None artifacts
        if artifacts is None:
            artifacts = {}

        # Ensure artifacts is a proper dict
        if not isinstance(artifacts, dict):
            self._log_solver_phase("WARNING", f"Artifacts is not a dict (type: {type(artifacts)}), converting to empty dict", "⚠️")
            artifacts = {}

        # Initialize standard fields
        artifacts.setdefault("_entities", {})
        artifacts.setdefault("_solver_state", {})
        artifacts.setdefault("_resources", {})

        # Validate required fields if specified
        if required_fields:
            missing_fields = [field for field in required_fields if field not in artifacts]
            if missing_fields:
                self._log_solver_phase("WARNING", f"Missing required artifact fields: {missing_fields}", "⚠️")

        return artifacts

    def _validate_artifacts_structure(self, artifacts: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate the structure of artifacts and return validation status and issues."""
        issues = []

        # Check if artifacts is a dict
        if not isinstance(artifacts, dict):
            issues.append(f"Artifacts must be a dict, got {type(artifacts)}")
            return False, issues

        # Check for required standard fields
        standard_fields = ["_entities", "_solver_state", "_resources"]
        for field in standard_fields:
            if field not in artifacts:
                issues.append(f"Missing standard field: {field}")

        # Validate entities field
        if "_entities" in artifacts and not isinstance(artifacts["_entities"], dict):
            issues.append("_entities field must be a dict")

        # Validate solver_state field
        if "_solver_state" in artifacts and not isinstance(artifacts["_solver_state"], dict):
            issues.append("_solver_state field must be a dict")

        # Validate resources field
        if "_resources" in artifacts and not isinstance(artifacts["_resources"], dict):
            issues.append("_resources field must be a dict")

        return len(issues) == 0, issues

    def _sanitize_artifacts(self, artifacts: dict[str, Any]) -> dict[str, Any]:
        """Sanitize artifacts by removing or cleaning problematic data."""
        sanitized = artifacts.copy()

        # Remove any None values that might cause issues
        sanitized = {k: v for k, v in sanitized.items() if v is not None}

        # Ensure string keys (in case of mixed types)
        sanitized = {str(k): v for k, v in sanitized.items()}

        # Limit the size of large values to prevent memory issues
        for key, value in sanitized.items():
            if isinstance(value, str) and len(value) > 10000:
                sanitized[key] = value[:10000] + "... [truncated]"
                self._log_solver_phase("WARNING", f"Truncated large value for key: {key}", "⚠️")

        return sanitized

    def _merge_artifacts(
        self, base_artifacts: dict[str, Any], new_artifacts: dict[str, Any], merge_strategy: str = "update"
    ) -> dict[str, Any]:
        """Merge artifacts with different strategies."""
        if merge_strategy == "update":
            # Simple update - new values override old ones
            result = base_artifacts.copy()
            result.update(new_artifacts)
            return result

        elif merge_strategy == "deep_merge":
            # Deep merge for nested dicts
            result = base_artifacts.copy()
            for key, value in new_artifacts.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_artifacts(result[key], value, "deep_merge")
                else:
                    result[key] = value
            return result

        elif merge_strategy == "preserve_base":
            # Only add new keys, don't override existing ones
            result = base_artifacts.copy()
            for key, value in new_artifacts.items():
                if key not in result:
                    result[key] = value
            return result

        else:
            self._log_solver_phase("WARNING", f"Unknown merge strategy: {merge_strategy}, using 'update'", "⚠️")
            return self._merge_artifacts(base_artifacts, new_artifacts, "update")

    def _extract_artifacts_metadata(self, artifacts: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata about artifacts for debugging and analysis."""
        metadata = {
            "total_keys": len(artifacts),
            "has_entities": "_entities" in artifacts,
            "has_solver_state": "_solver_state" in artifacts,
            "has_resources": "_resources" in artifacts,
            "entity_count": len(artifacts.get("_entities", {})),
            "state_keys": list(artifacts.get("_solver_state", {}).keys()),
            "resource_keys": list(artifacts.get("_resources", {}).keys()),
        }

        # Add size information
        try:
            import sys

            metadata["estimated_size_bytes"] = sys.getsizeof(artifacts)
        except Exception:
            metadata["estimated_size_bytes"] = "unknown"

        return metadata

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

    def _query_llm_with_prteng(self, prompt: str, system_prompt: str | None = None, max_turns: int = 30) -> str | None:
        """Generate LLM response with conversation context using PromptEngineer if available."""
        if not self._validate_llm_resource():
            return None

        try:
            # Build conversation context internally
            conversation_context = self._get_conversation_context(max_turns)

            # Use PromptEngineer if available, otherwise fall back to static prompts
            if hasattr(self.agent, "prompt_engineer") and self.agent.prompt_engineer:
                # Generate optimized prompt using PromptEngineer
                prompt_obj = self.agent.prompt_engineer.generate(
                    user_query=prompt,
                    system_template=system_prompt or "You are a helpful AI assistant.",
                    template_data={"conversation_context": conversation_context},
                )
                enhanced_system_prompt = prompt_obj.system_message
                user_prompt = prompt_obj.user_message
            else:
                print("🔧 [DEBUG] Using static prompt generation (PromptEngineer not available)")

                # Fallback to current behavior with proper formatting
                enhanced_system_prompt = system_prompt or ""
                if conversation_context and "{conversation_context}" in enhanced_system_prompt:
                    # Format the system prompt with conversation context
                    enhanced_system_prompt = enhanced_system_prompt.format(conversation_context=conversation_context)
                elif conversation_context:
                    # Fallback: append conversation context if no placeholder found
                    enhanced_system_prompt = f"{enhanced_system_prompt}\n\n{conversation_context}"
                user_prompt = prompt

            # Debug prints
            print("=" * 80)
            print("🔧 [DEBUG] LLM REQUEST DETAILS")
            print("=" * 80)
            print(f"📋 SYSTEM_PROMPT:\n{enhanced_system_prompt}")
            print("-" * 80)
            print(f"👤 USER_PROMPT:\n{user_prompt}")
            print("-" * 80)

            # Create request with clean user message and enhanced system prompt
            request = self._create_llm_request([{"role": "user", "content": user_prompt}], enhanced_system_prompt)

            # Query LLM
            if self.agent.llm_resource is None:
                return None
            response = self.agent.llm_resource.query_sync(request)

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
