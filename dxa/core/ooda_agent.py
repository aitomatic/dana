"""Base classes for the MUA system."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
import time
import openai
from dxa.core.types import OODAPhase, AgentState

class OODAAgent(ABC):
    """Abstract base agent implementing the OODA loop decision cycle."""
    
    def __init__(
        self,
        agent_llm_config: Dict,
        agent_system_prompt: Optional[str] = None
    ):
        """Initialize the OODA agent with single LLM."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.agent_llm = self._setup_llm(agent_llm_config)
        self.state = None
        self.agent_system_prompt = agent_system_prompt or self._get_default_agent_system_prompt()
        self._system_prompt_logged = False
        self.logger.info("Initialized %s", self.__class__.__name__)

    def _setup_llm(self, config: Dict):
        """Configure and return an LLM client based on provided config."""
        return openai.AsyncOpenAI(**config)

    def _get_default_agent_system_prompt(self) -> str:
        """Return the default system prompt for the agent LLM."""
        return """You are an intelligent agent operating in an OODA loop paradigm.
        Your role is to coordinate problem-solving through careful analysis.
        Follow the OODA loop phases:
        1. Observe: Gather information about the current situation
        2. Orient: Analyze and understand the information
        3. Decide: Determine the best course of action
        4. Act: Execute the decided action and evaluate results"""

    @abstractmethod
    async def start_session(self, initial_problem: Optional[str] = None):
        """Start a new problem-solving session."""
        pass

    @abstractmethod
    async def handle_interruption(self) -> bool:
        """Handle interruption in the problem-solving process."""
        pass

    @abstractmethod
    def _is_stuck(self) -> bool:
        """Determine if the agent is stuck and needs help."""
        pass

    def initialize_problem(self, problem_statement: str) -> None:
        """Initialize a new problem-solving session."""
        self.state = AgentState(
            current_phase=OODAPhase.OBSERVE,
            observations=[],
            context_window=[],
            problem_statement=problem_statement,
            working_memory={}
        )

    async def run_ooda_loop(self) -> bool:
        """Execute one complete OODA loop cycle."""
        start_time = time.time()
        self.logger.debug("Starting OODA cycle in %s phase", self.state.current_phase)
        
        try:
            phase_methods = {
                OODAPhase.OBSERVE: self.observe,
                OODAPhase.ORIENT: self.orient,
                OODAPhase.DECIDE: self.decide,
                OODAPhase.ACT: self.act
            }
            
            await phase_methods[self.state.current_phase]()
            self._advance_phase()
            
            return self._check_solution_found()
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.debug(
                "Completed OODA cycle",
                extra={"duration_ms": duration_ms}
            )

    @abstractmethod
    async def observe(self) -> None:
        """Observation phase: Gather information about the current state."""
        pass

    @abstractmethod
    async def orient(self) -> None:
        """Orientation phase: Analyze gathered information."""
        pass

    @abstractmethod
    async def decide(self) -> None:
        """Decision phase: Determine next actions based on orientation."""
        pass

    @abstractmethod
    async def act(self) -> None:
        """Action phase: Execute decided actions and evaluate results."""
        pass

    def _advance_phase(self) -> None:
        """Advance to the next phase in the OODA loop."""
        phases = list(OODAPhase)
        current_index = phases.index(self.state.current_phase)
        next_index = (current_index + 1) % len(phases)
        self.state.current_phase = phases[next_index]

    def _check_solution_found(self) -> bool:
        """Check if a solution has been found."""
        last_action = self.state.working_memory.get("last_action", "")
        solution_indicators = ["solution found", "problem solved", "task completed"]
        return any(indicator in last_action.lower() for indicator in solution_indicators)

    async def _query_agent_llm(self, prompt: str) -> str:
        """Query the agent LLM with the given prompt."""
        start_time = time.time()
        try:
            self.logger.info("\n%s", "=" * 80)
            self.logger.info("🤖 AGENT LLM CONVERSATION")
            self.logger.info("%s", "=" * 80)
            
            if not self._system_prompt_logged:
                self.logger.info("📝 SYSTEM PROMPT TO AGENT:")
                self.logger.info("-" * 40)
                self.logger.info(self.agent_system_prompt)
                self._system_prompt_logged = True
            
            self.logger.info("\n📤 REQUEST TO AGENT:")
            self.logger.info("-" * 40)
            self.logger.info(prompt)
            
            messages = [
                {"role": "system", "content": self.agent_system_prompt}
            ]
            messages.append({"role": "user", "content": prompt})
            
            response = await self.agent_llm.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            content = response.choices[0].message.content
            self.logger.info("\n📥 RESPONSE FROM AGENT:")
            self.logger.info("-" * 40)
            self.logger.info(content)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info("\n⏱️ Response time: %.2f ms", duration_ms)
            self.logger.info("=" * 80 + "\n")
            return content
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.debug(
                "Agent LLM query completed",
                extra={"duration_ms": duration_ms}
            )
