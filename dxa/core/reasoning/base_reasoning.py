"""Base reasoning pattern for DXA."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import logging
from dxa.agent.agent_state import StateManager
from dxa.core.resource.base_resource import BaseResource
from dxa.core.resource.expert_resource import ExpertResource
from dxa.core.resource.human_resource import HumanResource
from dxa.agent.agent_llm import AgentLLM

class ReasoningStatus(str, Enum):
    """Possible statuses from reasoning."""
    NEED_EXPERT = "NEED_EXPERT"
    NEED_INFO = "NEED_INFO"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

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
    strategy: str = "cot"
    temperature: float = 0.7
    max_tokens: int = 1000

class BaseReasoning(ABC):
    """Base class for implementing reasoning patterns in the DXA framework.

    The DXA Reasoning Paradigm:
    --------------------------
    Reasoning in DXA follows a step-based approach where complex problems are broken
    down into a sequence of smaller, focused reasoning steps. Each step:
    
    1. Receives context about the problem and previous reasoning
    2. Generates a specific prompt for the LLM
    3. Processes the LLM's response
    4. Decides whether to:
       - Move to the next step
       - Request additional information/expertise
       - Complete the reasoning process
       - Handle an error condition

    The reasoning flow is dynamic - steps can branch based on LLM responses,
    request external resources when needed, and adapt to new information.
    This creates a flexible yet structured approach to problem-solving that:
    
    - Breaks complex reasoning into manageable chunks
    - Maintains context across multiple interactions
    - Allows for backtracking and error recovery
    - Integrates external knowledge and expertise
    - Provides clear decision points and state management

    Implementation Guide:
    -------------------
    To implement a new reasoning pattern, developers should:

    1. Create a new class that inherits from BaseReasoning
    2. Define the reasoning steps by implementing:
        - steps property: List of possible step names
        - get_initial_step(): Starting point of the reasoning
        - get_next_step(): Logic for transitioning between steps
    3. Implement prompt generation:
        - get_step_prompt(): Generate step-specific prompts
        - get_reasoning_system_prompt(): Define system-level instructions
    4. Implement response handling:
        - reason_post_process(): Parse LLM responses into StepResult objects

    Example:
        ```python
        class MyReasoning(BaseReasoning):
            @property
            def steps(self) -> List[str]:
                return ["ANALYZE", "PLAN", "EXECUTE", "REVIEW"]
            
            def get_initial_step(self) -> str:
                return "ANALYZE"
            
            def get_step_prompt(self, step, context, query, previous_steps):
                if step == "ANALYZE":
                    return f"Analyze this query: {query}"
                # ... implement other steps
            
            def get_next_step(self, current_step, step_result):
                if current_step == "ANALYZE":
                    return "PLAN" if step_result.status == ReasoningStatus.COMPLETE else None
                # ... implement other transitions
        ```

    Key Features:
    - Structured step-by-step reasoning process
    - Resource management (experts, humans, tools)
    - State tracking across reasoning steps
    - Standardized interaction with LLMs
    - Error handling and recovery
    - Context management

    The reasoning process can result in:
    - COMPLETE: Reasoning reached a conclusion
    - NEED_EXPERT: External expertise required
    - NEED_INFO: Additional information needed
    - ERROR: Reasoning cannot continue

    Available Resources:
    - Expert Resources: Domain specialists
    - Human Resources: User interaction
    - Other Resources: Tools and utilities

    Tips for Implementation:
    - Keep steps atomic and focused
    - Use clear, descriptive step names
    - Include error handling in step transitions
    - Leverage previous step results in prompts
    - Document expected inputs/outputs for each step
    - Consider resource availability in reasoning flow
    """
    
    def __init__(self, config: Optional[ReasoningConfig] = None):
        self.config = config or ReasoningConfig()
        self.strategy = self.config.strategy
        self.agent_llm = None
        self.state_manager = StateManager(agent_name=self.__class__.__name__)
        self.available_resources: Dict[str, BaseResource] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_step = self.get_initial_step()
        self.previous_steps = []

    @property
    @abstractmethod
    def steps(self) -> List[str]:
        """Get list of possible steps."""
        pass
    
    @abstractmethod
    def get_initial_step(self) -> str:
        """Get the initial step for reasoning."""
        pass

    @abstractmethod
    def get_step_prompt(self,
                        step: str,
                        context: Dict[str, Any],
                        query: str,
                        previous_steps: List[Dict[str, Any]]) -> str:
        """Get the prompt for a specific step."""
        pass

    @abstractmethod
    def get_next_step(self, current_step: str, step_result: StepResult) -> Optional[str]:
        """Determine the next step based on current step and its result.
        
        Returns None if reasoning should end (success/failure/need resource).
        """
        pass

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for the current reasoning step.
        
        Combines the step-specific prompt with context and query information.
        This is typically used internally by the reason() method.
        
        Args:
            context (Dict[str, Any]): Current context for reasoning
            query (str): User's original query
            
        Returns:
            str: Generated prompt for the current step
        """
        return self.get_step_prompt(
            self.current_step, 
            context, 
            query,
            self.previous_steps
        )

    @abstractmethod
    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the reasoning system prompt."""
        pass

    def get_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the complete system prompt for LLM interaction.
        
        Combines the agent's system prompt with reasoning-specific instructions.
        This sets up the overall context and rules for the LLM.
        
        Args:
            context (Dict[str, Any]): Current context for reasoning
            query (str): User's original query
            
        Returns:
            str: Combined system prompt
        """
        system_prompt = ""

        if self.agent_llm and hasattr(self.agent_llm, 'get_system_prompt'):
            agent_system_prompt = self.agent_llm.get_system_prompt(context, query)
            if agent_system_prompt:
                system_prompt = agent_system_prompt
        
        reasoning_system_prompt = self.get_reasoning_system_prompt(context, query)
        if reasoning_system_prompt:
            system_prompt = f"{system_prompt}\n\n{reasoning_system_prompt}"

        return system_prompt

    def get_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the complete user prompt for LLM interaction.
        
        Combines the agent's user prompt with reasoning-specific prompts.
        This forms the actual query sent to the LLM.
        
        Args:
            context (Dict[str, Any]): Current context for reasoning
            query (str): User's original query
            
        Returns:
            str: Combined user prompt
        """
        prompt = ""

        if self.agent_llm and hasattr(self.agent_llm, 'get_user_prompt'):
            agent_prompt = self.agent_llm.get_user_prompt(context, query)
            if agent_prompt:
                prompt = agent_prompt

        reasoning_prompt = self.get_reasoning_prompt(context, query)
        if reasoning_prompt:
            prompt = f"{prompt}\n\n{reasoning_prompt}"

        return prompt

    async def reason(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Run a single reasoning cycle.
        
        This method executes one step in the reasoning process by:
        1. Generating appropriate prompts
        2. Querying the LLM
        3. Processing the response
        4. Determining the next step
        
        Args:
            context (Dict[str, Any]): Current context for reasoning
            query (str): User's original query
            
        Returns:
            Dict[str, Any]: Result of the reasoning step
        """
        # Get prompts
        system_prompt = self.get_system_prompt(context, query)
        user_prompt = self.get_prompt(context, query)
        
        # Query LLM
        response = await self._query_agent_llm({
            "system_prompt": system_prompt,
            "prompt": user_prompt,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        })
        
        # Process response
        step_result = self.reason_post_process(response["content"])
        
        # Store step result
        self.previous_steps.append({
            "step": self.current_step,
            "result": step_result
        })
        
        # Determine next step
        next_step = self.get_next_step(self.current_step, step_result)
        if next_step:
            self.current_step = next_step
            
        return step_result

    @abstractmethod
    def reason_post_process(self, response: str) -> StepResult:
        """Process the response from the LLM and return a standardized result.
        
        This method should parse and structure the raw LLM response into a 
        standardized StepResult object. Implementations should handle:
        
        - Extracting key information from the response
        - Determining the reasoning status (COMPLETE, NEED_INFO, etc.)
        - Formatting any resource requests or final answers
        - Error handling for malformed responses
        
        Args:
            response (str): Raw response from the LLM.
            
        Returns:
            StepResult: Structured result containing status, content, and any
                additional information like resource requests or final answers.
        """
        pass

    def reset(self) -> None:
        """Reset the reasoning process to its initial state.
        
        Clears previous steps and returns to the initial step. This is useful
        when starting a new reasoning chain or recovering from errors.
        """
        self.current_step = self.get_initial_step()
        self.previous_steps = []

    async def initialize(self) -> None:
        """Initialize the reasoning system.
        
        Performs any necessary setup before reasoning can begin, such as
        initializing the LLM agent. Should be called before first use.
        """
        if self.agent_llm:
            await self.agent_llm.initialize()

    async def cleanup(self) -> None:
        """Clean up the reasoning system.
        
        Performs cleanup tasks when reasoning is complete, such as
        closing LLM connections. Should be called when done using
        the reasoning system.
        """
        if self.agent_llm:
            await self.agent_llm.cleanup()

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for inclusion in prompts.
        
        Internal method to convert context dictionary into a formatted
        string suitable for LLM prompts.
        
        Args:
            context (Dict[str, Any]): Context to format
            
        Returns:
            str: Formatted context string
        """
        formatted = []
        for key, value in context.items():
            if isinstance(value, dict):
                formatted.append(f"{key}:")
                for k, v in value.items():
                    formatted.append(f"  {k}: {v}")
            elif isinstance(value, (list, tuple)):
                formatted.append(f"{key}:")
                for item in value:
                    formatted.append(f"  - {item}")
            else:
                formatted.append(f"{key}: {value}")
        return '\n'.join(formatted)

    def set_available_resources(self, resources: Dict[str, BaseResource]) -> None:
        """Configure available resources for the reasoning process.
        
        Resources can include domain experts, human users, or other tools
        that the reasoning process can utilize when needed.
        
        Args:
            resources (Dict[str, BaseResource]): Dictionary mapping resource
                names to their implementations
                
        Raises:
            TypeError: If resources are not properly typed
        """
        if not isinstance(resources, dict):
            raise TypeError("Resources must be provided as a dictionary")
        
        if not all(isinstance(r, BaseResource) for r in resources.values()):
            raise TypeError("All resources must inherit from BaseResource")
            
        self.available_resources = resources
        
        # Log available resources by type
        experts = [r for r in resources.values() if isinstance(r, ExpertResource)]
        humans = [r for r in resources.values() if isinstance(r, HumanResource)]
        others = [
            r for r in resources.values()
            if not isinstance(r, (ExpertResource, HumanResource))
        ]
        
        if experts:
            self.logger.info(
                "Available experts: %s",
                [f"{e.expertise.name} ({e.expertise.description})" for e in experts]
            )
        if humans:
            self.logger.info(
                "Available human users: %s",
                [f"{h.name} ({h.role})" for h in humans]
            )
        if others:
            self.logger.info(
                "Other available resources: %s",
                [f"{r.name} ({r.description})" for r in others]
            )

    def get_resource_description(self) -> str:
        """Get a formatted description of all available resources.
        
        Returns a human-readable string describing all configured resources,
        grouped by type (experts, humans, others) with their capabilities
        and metadata.
        
        Returns:
            str: Formatted resource description
        """
        description = []
        
        # Group resources by type
        experts = [
            r for r in self.available_resources.values()
            if isinstance(r, ExpertResource)
        ]
        humans = [
            r for r in self.available_resources.values()
            if isinstance(r, HumanResource)
        ]
        others = [
            r for r in self.available_resources.values()
            if not isinstance(r, (ExpertResource, HumanResource))
        ]
        
        # Add expert descriptions
        if experts:
            description.append("Available Domain Experts:")
            for expert in experts:
                description.extend([
                    f"- {expert.expertise.name}:",
                    f"  Description: {expert.expertise.description}",
                    f"  Capabilities: {', '.join(expert.expertise.capabilities)}",
                    f"  Keywords: {', '.join(expert.expertise.keywords)}"
                ])
        
        # Add human user descriptions
        if humans:
            description.append("\nAvailable Human Users:")
            for human in humans:
                description.extend([
                    f"- {human.name}:",
                    f"  Role: {human.role}",
                    f"  Description: {human.description}"
                ])
        
        # Add other resource descriptions
        if others:
            description.append("\nOther Available Resources:")
            for resource in others:
                description.extend([
                    f"- {resource.name}:",
                    f"  Description: {resource.description}"
                ])
        
        return "\n".join(description)

    def has_resource(self, resource_name: str) -> bool:
        """Check if a specific resource is available.
        
        Args:
            resource_name (str): Name of the resource to check
            
        Returns:
            bool: True if the resource exists, False otherwise
        """
        return resource_name in self.available_resources

    def set_agent_llm(self, agent_llm: AgentLLM) -> None:
        """Set the LLM agent for this reasoning engine.
        
        The LLM agent handles the actual interaction with the language model.
        
        Args:
            agent_llm (AgentLLM): LLM agent instance to use
        """
        self.agent_llm = agent_llm

    async def _query_agent_llm(self, llm_request: Dict[str, Any]) -> Dict[str, str]:
        """Query the LLM agent with the given request.
        
        Internal method to handle LLM interaction. Formats messages and
        handles basic error checking.
        
        Args:
            llm_request (Dict[str, Any]): Request parameters including
                prompts and configuration
                
        Returns:
            Dict[str, str]: LLM response
            
        Raises:
            AttributeError: If LLM agent is not properly initialized
        """
        if not hasattr(self, 'agent_llm'):
            raise AttributeError("Agent LLM not initialized. Ensure 'agent_llm' is set during initialization.")
        if not hasattr(self.agent_llm, 'query'):
            raise AttributeError("Agent LLM does not have a 'query' method.")

        messages = []
        if "system_prompt" in llm_request:
            messages.append({"role": "system", "content": llm_request["system_prompt"]})
        if "prompt" in llm_request:
            messages.append({"role": "user", "content": llm_request["prompt"]})

        response = await self.agent_llm.query(messages)
        
        # AgentLLM.query() now returns a dict with 'content' key
        return response  # Just return the response as-is since it's already in the right format

    async def __aenter__(self):
        """Context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup()

    def _format_previous_step(self, previous_steps: List[Dict[str, Any]], step_name: str) -> str:
        """Format the result from a previous reasoning step.
        
        Internal method to retrieve and format results from earlier steps
        in the reasoning process.
        
        Args:
            previous_steps (List[Dict[str, Any]]): List of previous step results
            step_name (str): Name of the step to retrieve
            
        Returns:
            str: Formatted step result or default message if step not found
        """
        for step in reversed(previous_steps):
            if step["step"] == step_name:
                return step["result"].content
        return "No previous step information available"