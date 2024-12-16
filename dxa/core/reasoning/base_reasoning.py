"""Base class for implementing reasoning patterns in DXA.

BaseReasoning provides the foundation for all reasoning implementations:
1. Manages LLM interactions
2. Handles state and context
3. Provides error handling
4. Tracks objective evolution

Execution Flow:
    reason_about(task, context)           # Main entry point
        ↓
    _prepare_reasoning(task, context)     # Setup phase
        ↓
    _apply_reasoning(task, context)       # Core reasoning
        ↓
    _verify_reasoning(result, context)    # Validation
        ↓
    _handle_reasoning_error(...)          # Error handling if needed

Override Points:
    _apply_reasoning(): Required - Implement core reasoning logic
    _verify_reasoning(): Optional - Add custom validation
    _prepare_reasoning(): Optional - Add setup steps
    _handle_reasoning_error(): Optional - Custom error handling

Example:
    ```python
    class MyReasoning(BaseReasoning):
        @property
        def steps(self) -> List[str]:
            return ["analyze", "solve"]
        
        async def _apply_reasoning(self, task, context):
            # Core reasoning implementation
            response = await self.agent_llm.query({
                "system": "Process this task.",
                "user": str(task)
            })
            
            # Record in context
            context.history.append({
                "step": self.steps[0],
                "response": response
            })
            
            return ReasoningResult(
                success=True,
                output=response.get("content"),
                insights={},
                confidence=1.0,
                reasoning_path=self.steps
            )
    ```

State Management:
    - context.workspace: Shared memory between steps
    - context.history: Record of reasoning steps
    - objective_state: Tracks objective understanding
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
import logging
from dxa.core.resource import LLMResource

class ReasoningStatus(str, Enum):
    """Possible statuses from reasoning."""
    NEED_EXPERT = "NEED_EXPERT"
    NEED_INFO = "NEED_INFO"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

class ReasoningLevel(Enum):
    """Reasoning complexity levels."""
    DIRECT = 1.0      # Direct execution
    REFLECTIVE = 2.0  # Basic validation
    COT = 3.0         # Chain of thought
    OODA = 4.0        # Full OODA loop
    META_OODA = 5.0   # Self-modifying OODA
    DANA = 6.0        # Domain-aware neurosymbolic agent
@dataclass
class StepResult:
    """Result of a reasoning step."""
    status: ReasoningStatus
    content: str
    next_step: Optional[str] = None
    # For NEED_EXPERT/NEED_INFO
    resource_request: Optional[Dict[str, Any]] = None
    # For COMPLETE
    final_answer: Optional[str] = None
    # For ERROR
    error_message: Optional[str] = None

@dataclass
class ReasoningConfig:
    """Configuration for reasoning engine."""
    agent_llm: Optional[LLMResource] = None
    strategy: str = "cot"
    temperature: float = 0.7
    max_tokens: int = 1000

@dataclass
class ReasoningResult:
    """Result from any reasoning process."""
    success: bool
    output: Any
    insights: Dict[str, Any]  # New understanding gained
    needs_objective_refinement: bool = False
    confidence: float = 0.0
    reasoning_path: List[str] = None

@dataclass
class ReasoningContext:
    """Context for reasoning execution."""
    objective: str
    resources: Dict[str, Any]
    workspace: Dict[str, Any]  # Working memory
    history: List[Dict[str, Any]]  # Execution history
    status: str = "initializing"
    metadata: Dict[str, Any] = field(default_factory=dict)
    observations: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ObjectiveState:
    """Tracks the evolution of an objective/problem statement."""
    original: str
    current: str
    refinements: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    
    def add_refinement(self, refinement: str, reason: str, confidence: float):
        """Add a refinement to the objective."""
        self.refinements.append({
            "from": self.current,
            "to": refinement,
            "reason": reason,
            "timestamp": datetime.now().timestamp()
        })
        self.current = refinement
        self.confidence = confidence

@dataclass
class ReasoningTask:
    """Task for reasoning system to process.
    
    Attributes:
        objective: Main goal/command to achieve
        context: Additional task context/parameters
        system_prompt: Optional system prompt override
        temperature: Optional temperature override
        metadata: Additional task metadata
    """
    objective: str
    context: Dict[str, Any] = field(default_factory=dict)
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningTask":
        """Create Task from dictionary."""
        if isinstance(data, str):
            return cls(objective=data)
        return cls(
            objective=data.get("objective", data.get("command", str(data))),
            context=data.get("context", {}),
            system_prompt=data.get("system_prompt"),
            temperature=data.get("temperature"),
            metadata=data.get("metadata", {})
        )

class BaseReasoning(ABC):
    """Base class for implementing reasoning patterns."""
    
    def __init__(self, config: Optional[ReasoningConfig] = None):
        self.config = config or ReasoningConfig()
        self._agent_llm = self.config.agent_llm
        self.logger = logging.getLogger(self.__class__.__name__)
        self.objective_state = None

    @property
    @abstractmethod
    def steps(self) -> List[str]:
        """Get ordered list of reasoning steps."""
        pass

    @property
    def agent_llm(self) -> Optional[LLMResource]:
        """Get the LLM provided by the Agent."""
        if self._agent_llm is None:
            raise ValueError("No LLM configured. Agent must set LLM before reasoning.")
        return self._agent_llm

    @agent_llm.setter
    def agent_llm(self, llm: LLMResource):
        """Set the LLM for reasoning."""
        self._agent_llm = llm

    async def reason_about(self, task: Dict[str, Any], context: ReasoningContext) -> ReasoningResult:
        """Main reasoning entry point."""
        try:
            await self._prepare_reasoning(task, context)
            result = await self._apply_reasoning(task, context)
            return await self._verify_reasoning(result, context)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            return await self._handle_reasoning_error(e, task, context)

    # pylint: disable=unused-argument
    async def _prepare_reasoning(self, task: Dict[str, Any], context: ReasoningContext) -> None:
        """Setup reasoning context."""
        await self._init_objective(context)
        context.workspace.clear()  # Fresh workspace
        context.history.clear()    # Fresh history

    async def _apply_reasoning(self, task: Dict[str, Any], context: ReasoningContext) -> ReasoningResult:
        """Apply the reasoning pattern. Override this in subclasses."""
        response = await self.agent_llm.query({
            "system": "Process this task directly.",
            "user": str(task.get('command', task)),
            "temperature": self.config.temperature
        })
        
        # Record step in history
        context.history.append({
            "step": self.steps[0],
            "task": task,
            "response": response.get("content")
        })
        
        return ReasoningResult(
            success=True,
            output=response.get("content", "Task completed"),
            insights={},
            confidence=1.0,
            reasoning_path=self.steps
        )

    async def _verify_reasoning(self, result: ReasoningResult, context: ReasoningContext) -> ReasoningResult:
        """Verify reasoning result. Override for custom verification."""
        return result

    async def _init_objective(self, context: ReasoningContext) -> None:
        """Initialize objective tracking."""
        self.objective_state = ObjectiveState(
            original=context.objective,
            current=context.objective
        )

    async def _handle_reasoning_error(
        self, 
        error: Exception, 
        task: Dict[str, Any], 
        context: ReasoningContext
    ) -> ReasoningResult:
        """Handle reasoning errors."""
        self.logger.error("Reasoning error: %s", str(error))
        return ReasoningResult(
            success=False,
            output=str(error),
            insights={"error_type": error.__class__.__name__},
            confidence=0.0,
            reasoning_path=[]
        )

    async def initialize(self) -> None:
        """Initialize the reasoning system."""
        if self.agent_llm:
            await self.agent_llm.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.agent_llm:
            await self.agent_llm.cleanup()

    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()