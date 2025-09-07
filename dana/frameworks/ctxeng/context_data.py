"""
Context Data Structure for the Context Engineering Framework.

This module defines structured data classes for holding context information
that can be assembled into rich prompts for LLM interactions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProblemContextData:
    """Structured problem context information."""

    problem_statement: str
    objective: str = ""
    original_problem: str = ""
    depth: int = 0
    constraints: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Set default values if not provided."""
        if not self.objective:
            self.objective = self.problem_statement
        if not self.original_problem:
            self.original_problem = self.problem_statement


@dataclass
class WorkflowContextData:
    """Structured workflow execution context."""

    current_workflow: str = ""
    workflow_state: str = ""
    workflow_values: dict[str, Any] = field(default_factory=dict)
    execution_progress: float = 0.0
    estimated_completion: datetime | None = None
    error_count: int = 0
    retry_count: int = 0


@dataclass
class ConversationContextData:
    """Structured conversation history context."""

    conversation_history: str = ""
    recent_events: list[str] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    conversation_tone: str = "professional"
    context_depth: str = "standard"  # minimal, standard, comprehensive


@dataclass
class ResourceContextData:
    """Structured resource context information."""

    available_resources: list[str] = field(default_factory=list)
    resource_limits: dict[str, Any] = field(default_factory=dict)
    resource_usage: dict[str, Any] = field(default_factory=dict)
    resource_errors: list[str] = field(default_factory=list)


@dataclass
class MemoryContextData:
    """Structured memory and learning context."""

    relevant_memories: list[str] = field(default_factory=list)
    learned_patterns: list[str] = field(default_factory=list)
    user_model: dict[str, Any] = field(default_factory=dict)
    world_model: dict[str, Any] = field(default_factory=dict)
    context_priorities: list[str] = field(default_factory=list)


@dataclass
class ExecutionContextData:
    """Structured execution environment context."""

    session_id: str | None = None
    execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    execution_constraints: dict[str, Any] = field(default_factory=dict)
    environment_info: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextData:
    """Comprehensive context data structure for prompt assembly.

    This dataclass holds all the structured context information that can be
    assembled into rich prompts for LLM interactions. It provides type safety,
    validation, and easy serialization.
    """

    # Core query information
    query: str
    template: str = "general"
    use_case: str = "general"

    # Structured context components
    problem: ProblemContextData | None = None
    workflow: WorkflowContextData | None = None
    conversation: ConversationContextData | None = None
    resources: ResourceContextData | None = None
    memory: MemoryContextData | None = None
    execution: ExecutionContextData | None = None

    # Additional context
    additional_context: dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    context_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template assembly.

        Returns:
            Dictionary representation suitable for template processing
        """
        context_dict: dict[str, Any] = {
            "query": self.query,
            "template": self.template,
            "use_case": self.use_case,
        }

        # Add problem context
        if self.problem:
            context_dict["problem_statement"] = self.problem.problem_statement
            context_dict["objective"] = self.problem.objective
            context_dict["original_problem"] = self.problem.original_problem
            context_dict["current_depth"] = self.problem.depth
            context_dict["constraints"] = self.problem.constraints
            context_dict["assumptions"] = self.problem.assumptions

        # Add workflow context
        if self.workflow:
            context_dict["workflow_current_workflow"] = self.workflow.current_workflow
            context_dict["workflow_workflow_state"] = self.workflow.workflow_state
            context_dict["workflow_values"] = self.workflow.workflow_values
            context_dict["execution_progress"] = self.workflow.execution_progress
            context_dict["error_count"] = self.workflow.error_count
            context_dict["retry_count"] = self.workflow.retry_count

        # Add conversation context
        if self.conversation:
            context_dict["conversation_history"] = self.conversation.conversation_history
            context_dict["recent_events"] = self.conversation.recent_events
            context_dict["user_preferences"] = self.conversation.user_preferences
            context_dict["conversation_tone"] = self.conversation.conversation_tone
            context_dict["context_depth"] = self.conversation.context_depth

        # Add resource context
        if self.resources:
            context_dict["available_resources"] = self.resources.available_resources
            context_dict["resource_limits"] = self.resources.resource_limits
            context_dict["resource_usage"] = self.resources.resource_usage
            context_dict["resource_errors"] = self.resources.resource_errors

        # Add memory context
        if self.memory:
            context_dict["relevant_memories"] = self.memory.relevant_memories
            context_dict["learned_patterns"] = self.memory.learned_patterns
            context_dict["user_model"] = self.memory.user_model
            context_dict["world_model"] = self.memory.world_model
            context_dict["context_priorities"] = self.memory.context_priorities

        # Add execution context
        if self.execution:
            context_dict["session_id"] = self.execution.session_id
            context_dict["execution_time"] = self.execution.execution_time
            context_dict["memory_usage"] = self.execution.memory_usage
            context_dict["cpu_usage"] = self.execution.cpu_usage
            context_dict["execution_constraints"] = self.execution.execution_constraints
            context_dict["environment_info"] = self.execution.environment_info

        # Add additional context
        context_dict.update(self.additional_context)

        return context_dict

    def get_available_context_keys(self) -> list[str]:
        """Get list of available context keys.

        Returns:
            List of context keys that have non-empty values
        """
        context_dict = self.to_dict()
        return [key for key, value in context_dict.items() if value is not None and value != "" and value != [] and value != {}]

    def get_context_summary(self) -> dict[str, Any]:
        """Get a summary of available context.

        Returns:
            Dictionary with counts and types of available context
        """
        return {
            "total_context_keys": len(self.get_available_context_keys()),
            "has_problem_context": self.problem is not None,
            "has_workflow_context": self.workflow is not None,
            "has_conversation_context": self.conversation is not None,
            "has_resource_context": self.resources is not None,
            "has_memory_context": self.memory is not None,
            "has_execution_context": self.execution is not None,
            "additional_context_count": len(self.additional_context),
            "context_version": self.context_version,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def create_for_agent(cls, query: str, template: str = "general", **kwargs) -> "ContextData":
        """Create a basic ContextData instance for agent use.

        This is a simple factory method that creates a ContextData instance
        that can be populated by the agent's state assembly logic.

        Args:
            query: The query string
            template: Template name to use
            **kwargs: Additional context data

        Returns:
            Basic ContextData instance ready for population
        """
        return cls(query=query, template=template, **kwargs)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextData":
        """Create ContextData from dictionary.

        Args:
            data: Dictionary containing context data

        Returns:
            ContextData object
        """
        # Extract core fields
        query = data.pop("query", "")
        template = data.pop("template", "general")
        use_case = data.pop("use_case", "general")

        # Create base context data
        context_data = cls(query=query, template=template, use_case=use_case)

        # Extract structured components if present
        if any(key.startswith("problem_") for key in data.keys()):
            context_data.problem = ProblemContextData(
                problem_statement=data.pop("problem_statement", ""),
                objective=data.pop("objective", ""),
                original_problem=data.pop("original_problem", ""),
                depth=data.pop("current_depth", 0),
                constraints=data.pop("constraints", {}),
                assumptions=data.pop("assumptions", []),
            )

        if any(key.startswith("workflow_") for key in data.keys()):
            context_data.workflow = WorkflowContextData(
                current_workflow=data.pop("workflow_current_workflow", ""),
                workflow_state=data.pop("workflow_workflow_state", ""),
                workflow_values=data.pop("workflow_values", {}),
                execution_progress=data.pop("execution_progress", 0.0),
                error_count=data.pop("error_count", 0),
                retry_count=data.pop("retry_count", 0),
            )

        if any(key in data for key in ["conversation_history", "recent_events", "user_preferences"]):
            context_data.conversation = ConversationContextData(
                conversation_history=data.pop("conversation_history", ""),
                recent_events=data.pop("recent_events", []),
                user_preferences=data.pop("user_preferences", {}),
                conversation_tone=data.pop("conversation_tone", "professional"),
                context_depth=data.pop("context_depth", "standard"),
            )

        # Add remaining data as additional context
        context_data.additional_context = data

        return context_data
