"""Core framework for DXA agents.

This module provides the foundational components for building and running agents:
- Configuration management
- State tracking and observations
- Progress monitoring
- Runtime execution
- LLM integration

All agent implementations build on top of these core components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator, Callable, Awaitable
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.common.errors import DXAError
from dxa.common.base_llm import BaseLLM

# Type aliases
ReasoningStep = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
ExecutionHook = Callable[[Dict[str, Any]], Awaitable[None]]
ContinuationCheck = Callable[[Dict[str, Any]], Awaitable[bool]]

@dataclass
class AgentConfig:
    """Configuration for DXA agents."""
    name: str
    llm_config: Dict[str, Any]
    reasoning: BaseReasoning
    additional_params: Optional[Dict[str, Any]] = None

@dataclass 
class AgentState:
    """Current state of an agent."""
    name: str
    status: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Observation:
    """An observation made by the agent."""
    content: Any
    source: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    """A message in the agent's communication."""
    content: str
    sender: str
    receiver: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentProgress:
    """Represents agent progress updates during task execution."""
    type: str  # "progress" or "result"
    message: str
    percent: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

    @property
    def is_progress(self) -> bool:
        return self.type == "progress"

    @property
    def is_result(self) -> bool:
        return self.type == "result"

class StateManager:
    """Manages agent state and execution context."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.state = AgentState(name=agent_name, status="initializing")
        self.observations: List[Observation] = []
        self.messages: List[Message] = []
        self.working_memory: Dict[str, Any] = {}

    def update_state(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.state = AgentState(name=self.agent_name, status=status, metadata=metadata or {})

    def add_observation(self, content: Any, source: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.observations.append(Observation(content=content, source=source, metadata=metadata or {}))

    def add_message(self, content: str, sender: str, receiver: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.messages.append(Message(content=content, sender=sender, receiver=receiver, metadata=metadata or {}))

    def get_recent_observations(self, n: int = 5) -> List[Observation]:
        return self.observations[-n:]

    def get_recent_messages(self, n: int = 5) -> List[Message]:
        return self.messages[-n:]

    def clear_history(self) -> None:
        self.observations.clear()
        self.messages.clear()
        self.working_memory.clear()

class AgentLLM(BaseLLM):
    """LLM implementation specialized for agent operations."""
    
    def __init__(self, name: str, config: Dict[str, Any], agent_prompts: Optional[Dict[str, str]] = None):
        super().__init__(name=name, config=config)
        self.agent_prompts = agent_prompts or {}
    
    async def query(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        combined_messages = []
        
        # Handle system messages
        system_content = []
        if self.agent_prompts.get("system_prompt"):
            system_content.append(self.agent_prompts["system_prompt"])
        system_content.extend(m["content"] for m in messages if m["role"] == "system")
        
        if system_content:
            combined_messages.append({
                "role": "system",
                "content": "\n\n".join(system_content)
            })
        
        # Handle user messages
        user_content = []
        if self.agent_prompts.get("user_prompt"):
            user_content.append(self.agent_prompts["user_prompt"])
        user_content.extend(m["content"] for m in messages if m["role"] == "user")
        
        if user_content:
            combined_messages.append({
                "role": "user",
                "content": "\n\n".join(user_content)
            })
        
        response = await super().query(combined_messages, **kwargs)
        return {"content": response.choices[0].message.content if response.choices else ""}

class AgentRuntime:
    """Manages the execution lifecycle of an agent."""
    
    def __init__(self, state_manager: StateManager, max_iterations: Optional[int] = None):
        self.state_manager = state_manager
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self._is_running = False

    async def execute_with_progress(
        self,
        task: Dict[str, Any],
        reasoning_step: ReasoningStep,
        pre_execute: Optional[ExecutionHook] = None,
        post_execute: Optional[ExecutionHook] = None,
        should_continue: Optional[ContinuationCheck] = None
    ) -> AsyncIterator[AgentProgress]:
        try:
            yield AgentProgress(type="progress", message="Starting execution", percent=0)
            
            context = task.copy()
            self._is_running = True
            self.iteration_count = 0
            
            if pre_execute:
                await pre_execute(context)
                yield AgentProgress(type="progress", message="Setup complete", percent=10)
            
            while self._is_running:
                if self.max_iterations and self.iteration_count >= self.max_iterations:
                    self.state_manager.add_observation("Reached maximum iterations", "runtime")
                    break
                
                self.iteration_count += 1
                result = await reasoning_step(context)
                
                percent = min(90, (self.iteration_count / (self.max_iterations or 10)) * 80 + 10)
                yield AgentProgress(
                    type="progress",
                    message=f"Completed iteration {self.iteration_count}",
                    percent=percent,
                    result={"iteration_result": result}
                )
                
                context.update(result)
                
                if result.get("task_complete") or result.get("is_stuck"):
                    break
                    
                if should_continue and not await should_continue(result):
                    break
            
            if post_execute:
                result = await post_execute(result)
            
            yield AgentProgress(
                type="result",
                message="Execution complete",
                percent=100,
                result={
                    "success": True,
                    "iterations": self.iteration_count,
                    "results": result,
                    "state_history": {
                        "observations": self.state_manager.observations,
                        "messages": self.state_manager.messages
                    }
                }
            )
            
        except DXAError as e:
            self.state_manager.add_observation(
                f"Runtime error: {str(e)}",
                "runtime",
                {"error_type": e.__class__.__name__}
            )
            
            yield AgentProgress(
                type="result",
                message=f"Execution failed: {str(e)}",
                percent=100,
                result={
                    "success": False,
                    "error": str(e),
                    "iterations": self.iteration_count,
                    "state_history": {
                        "observations": self.state_manager.observations,
                        "messages": self.state_manager.messages
                    }
                }
            )

    async def execute(
        self,
        task: Dict[str, Any],
        reasoning_step: ReasoningStep,
        pre_execute: Optional[ExecutionHook] = None,
        post_execute: Optional[ExecutionHook] = None,
        should_continue: Optional[ContinuationCheck] = None
    ) -> Dict[str, Any]:
        """Execute without progress updates."""
        async for progress in self.execute_with_progress(
            task=task,
            reasoning_step=reasoning_step,
            pre_execute=pre_execute,
            post_execute=post_execute,
            should_continue=should_continue
        ):
            if progress.is_result:
                return progress.result 