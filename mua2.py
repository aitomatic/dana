"""Implementation of a Model-Using Agent that operates using the OODA loop paradigm."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio
import logging
import time
import openai
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class OODAPhase(Enum):
    """Enumeration of phases in the OODA (Observe, Orient, Decide, Act) decision cycle."""
    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"


@dataclass
class Observation:
    """Class representing a single observation with timestamp and associated data."""
    data: Dict
    source: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class ChatHistory:
    """Manages the conversation history."""
    messages: List[Dict] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        """Add a new message to the history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().timestamp()
        })


@dataclass
class AgentState:
    """Class representing the current state of the Model-Using Agent in the OODA loop."""
    current_phase: OODAPhase
    observations: List[Observation]
    context_window: List[Dict]
    problem_statement: str
    working_memory: Dict
    agent_history: ChatHistory = field(default_factory=ChatHistory)


@dataclass
class ExpertResponse:
    """Structured response from a domain expert."""
    confidence: float
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    follow_up: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def validate(cls, data: Dict) -> bool:
        """Validate the expert response structure."""
        try:
            # Check required fields
            assert 'confidence' in data and isinstance(data['confidence'], (int, float))
            assert 0 <= data['confidence'] <= 1
            
            assert 'analysis' in data and isinstance(data['analysis'], dict)
            assert all(k in data['analysis'] for k in ['main_points', 'details', 'assumptions', 'limitations'])
            
            assert 'recommendations' in data and isinstance(data['recommendations'], list)
            for rec in data['recommendations']:
                assert all(k in rec for k in ['suggestion', 'rationale', 'priority'])
                assert 1 <= rec['priority'] <= 5
            
            assert 'follow_up' in data and isinstance(data['follow_up'], list)
            
            return True
        except AssertionError:
            return False

    @classmethod
    def create_fallback(cls, content: str, error: str = "Response format error") -> 'ExpertResponse':
        """Create a fallback response when parsing fails."""
        return cls(
            confidence=0.0,
            analysis={
                'main_points': [],
                'details': content,
                'assumptions': [],
                'limitations': [error]
            },
            recommendations=[],
            follow_up=["Please provide response in the correct format"],
            metadata={'error': error}
        )


@dataclass
class DomainExpertLLM:
    """Represents a domain expert LLM with specific expertise."""
    domain: str
    llm: Any  # The OpenAI AsyncClient
    system_prompt: str
    _system_prompt_logged: bool = field(default=False)

    @classmethod
    def create(
        cls,
        domain: str,
        llm_config: Dict,
        system_prompt: Optional[str] = None
    ) -> 'DomainExpertLLM':
        """Create a new domain expert LLM."""
        llm = openai.AsyncOpenAI(**llm_config)
        if system_prompt is None:
            system_prompt = f"""You are an expert-level specialist in {domain}.
            When consulted:
            1. State your confidence level (0-100%)
            2. Provide your main points clearly
            3. Show your detailed analysis
            4. List any assumptions
            5. Note any limitations
            6. Make specific recommendations
            7. Suggest follow-up questions if needed

            Structure your response as:

            CONFIDENCE: <percentage>%

            ANALYSIS:
            - Main point 1
            - Main point 2
            ...

            DETAILS:
            <your detailed analysis>

            ASSUMPTIONS:
            - Assumption 1
            - Assumption 2
            ...

            LIMITATIONS:
            - Limitation 1
            - Limitation 2
            ...

            RECOMMENDATIONS:
            1. First recommendation (Priority: High/Medium/Low)
            2. Second recommendation (Priority: High/Medium/Low)
            ...

            FOLLOW-UP:
            - Question 1
            - Question 2
            ..."""
        return cls(domain=domain, llm=llm, system_prompt=system_prompt)

    async def query(self, prompt: str, logger: logging.Logger) -> str:
        """Query this domain expert."""
        start_time = time.time()
        try:
            logger.info("\n" + "=" * 80)
            logger.info(f"👨‍🔬 EXPERT LLM CONVERSATION: {self.domain.upper()}")
            logger.info("=" * 80)
            
            if not self._system_prompt_logged:
                logger.info("📝 SYSTEM PROMPT TO EXPERT:")
                logger.info("-" * 40)
                logger.info(self.system_prompt)
                self._system_prompt_logged = True
            
            logger.info("\n📤 REQUEST TO EXPERT:")
            logger.info("-" * 40)
            logger.info(prompt)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            logger.info("\nWaiting for expert response...")
            response = await self.llm.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            content = response.choices[0].message.content
            logger.info("\n📥 RESPONSE FROM EXPERT:")
            logger.info("-" * 40)
            logger.info(content)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info("\n⏱️ Response time: %.2f ms", duration_ms)
            logger.info("=" * 80 + "\n")
            return content
        finally:
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"{self.domain} expert LLM query completed",
                extra={"duration_ms": duration_ms}
            )


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
        4. Act: Execute the decided action and evaluate results

        When you need expert help, write:
        CONSULT <domain>: <your question>
        CONTEXT: <relevant context>
        REASON: <why you need expert input>

        When you need user input, write:
        ASK USER <role>: <your question>
        CONTEXT: <relevant context>
        PURPOSE: <why you need their input>

        Always state your confidence level as:
        CONFIDENCE: <percentage>%"""

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
            self.logger.info("\n" + "=" * 80)
            self.logger.info("🤖 AGENT LLM CONVERSATION")
            self.logger.info("=" * 80)
            
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


@dataclass
class User:
    """Represents a human user with a specific role in the problem-solving process."""
    role: str
    name: str
    description: str
    permissions: List[str]  # e.g., ['specify_problem', 'clarify', 'validate', 'modify']

    def get_role_description(self) -> str:
        """Get a description of this user's role for the agent."""
        return f"""Role: {self.role}
        Name: {self.name}
        Description: {self.description}
        Permissions: {', '.join(self.permissions)}"""


class ModelUsingAgent(OODAAgent):
    """OODA Agent with access to domain expert LLMs."""
    
    def __init__(
        self,
        agent_llm_config: Dict,
        domain_experts: List[DomainExpertLLM],
        users: List[User],
        agent_system_prompt: Optional[str] = None
    ):
        """Initialize agent with domain expert LLMs."""
        if agent_system_prompt is None:
            agent_system_prompt = """You are an intelligent agent operating in an OODA loop paradigm.
            Your role is to coordinate problem-solving through careful analysis.
            Follow the OODA loop phases:
            1. Observe: Gather information about the current situation
            2. Orient: Analyze and understand the information
            3. Decide: Determine the best course of action
            4. Act: Execute the decided action and evaluate results

            When you need expert help, use this format:
            CONSULT <domain>: <your question>
            CONTEXT: <relevant context>
            REASON: <why you need expert input>

            When you need user input, use this format:
            ASK USER <role>: <your question>
            CONTEXT: <relevant context>
            PURPOSE: <why you need their input>

            Always be clear about your confidence level by stating:
            CONFIDENCE: <percentage>%"""

        # Add information about available experts and users
        expert_info = "\n\nYou have access to the following domain experts:\n" + \
                     "\n".join(f"- {expert.domain}" for expert in domain_experts)
        
        user_info = "\n\nYou are working with the following users:\n" + \
                   "\n".join(user.get_role_description() for user in users)
        
        interaction_info = """
        When you need to interact with users:
        {
            "user_interaction": {
                "role": "required user role",
                "purpose": "why you need to interact",
                "question": "what you need to ask or communicate",
                "context": "relevant context for the user"
            }
        }
        """
        
        full_prompt = (
            agent_system_prompt + 
            expert_info + 
            user_info + 
            "\n\nExpert Consultation Format:" +
            self._get_expert_consultation_format() +
            "\n\nUser Interaction Format:" +
            interaction_info
        )
        
        super().__init__(agent_llm_config, full_prompt)
        self.domain_experts = {expert.domain: expert for expert in domain_experts}
        self.users = {user.role: user for user in users}
        self.logger.info(
            "Initialized with experts in: %s and users: %s", 
            ", ".join(self.domain_experts.keys()),
            ", ".join(self.users.keys())
        )

    def _get_expert_consultation_format(self) -> str:
        """Get the format specification for expert consultation."""
        return """To consult an expert, structure your response like this:
        {
            "reasoning": "your reasoning for needing expert input",
            "consultations": [
                {
                    "expert": "domain name",
                    "question": "your specific question",
                    "context": "any relevant context"
                }
            ]
        }

        For example:
        {
            "reasoning": "We need mathematical verification of this calculation",
            "consultations": [
                {
                    "expert": "mathematics",
                    "question": "Is this equation correct?",
                    "context": "Given x = 5, y = 3..."
                }
            ]
        }"""

    def _should_consult_experts(self, response: str) -> List[str]:
        """Determine which experts to consult based on agent's response."""
        self.logger.debug("Analyzing response for expert consultation needs:")
        self.logger.debug("Full response: %s", response)

        try:
            # Look for JSON-like structure between curly braces
            start = response.find('{')
            end = response.rfind('}')
            
            if start != -1 and end != -1:
                consultation_str = response[start:end + 1]
                consultation_data = json.loads(consultation_str)
                
                if isinstance(consultation_data, dict) and 'consultations' in consultation_data:
                    self.logger.info("Found structured consultation request")
                    self.logger.debug("Reasoning: %s", consultation_data.get('reasoning', 'No reasoning provided'))
                    
                    needed_experts = []
                    for consult in consultation_data['consultations']:
                        expert = consult.get('expert', '').lower()
                        if expert in self.domain_experts:
                            self.logger.debug(
                                "Valid expert consultation request: %s - %s",
                                expert,
                                consult.get('question', 'No question provided')
                            )
                            needed_experts.append(expert)
                        else:
                            self.logger.warning("Unknown expert domain requested: %s", expert)
                    
                    return needed_experts

        except json.JSONDecodeError:
            self.logger.debug("No valid JSON structure found in response")
        except Exception as e:
            self.logger.warning("Error parsing consultation request: %s", str(e))

        # Fallback to keyword matching if no valid JSON structure found
        self.logger.debug("Falling back to keyword matching")
        return self._should_consult_experts_fallback(response)

    def _should_consult_experts_fallback(self, response: str) -> List[str]:
        """Fallback method using keyword matching."""
        needed_experts = []
        response_lower = response.lower()
        
        for domain in self.domain_experts:
            domain_lower = domain.lower()
            indicators = [
                f"consult {domain_lower}",
                f"need {domain_lower} expertise",
                f"ask {domain_lower}"
            ]
            if any(indicator in response_lower for indicator in indicators):
                needed_experts.append(domain)
        
        return needed_experts

    async def consult_expert(self, domain: str, response: str) -> Optional[ExpertResponse]:
        """Consult a specific domain expert."""
        if domain not in self.domain_experts:
            self.logger.warning("No expert available for domain: %s", domain)
            return None

        try:
            # Extract the specific question for this expert from the response
            start = response.find('CONSULT')
            if start != -1:
                # Find the question after "CONSULT domain:"
                question_start = response.find(':', start)
                if question_start != -1:
                    question = response[question_start + 1:].strip()
                    expert = self.domain_experts[domain]
                    raw_response = await expert.query(question, self.logger)
                    
                    # Parse the expert's response into structured format
                    try:
                        # Extract confidence
                        conf_start = raw_response.find('CONFIDENCE:')
                        conf_end = raw_response.find('%', conf_start)
                        confidence = float(raw_response[conf_start + 10:conf_end].strip()) / 100
                        
                        # Extract analysis
                        analysis_start = raw_response.find('ANALYSIS:')
                        assumptions_start = raw_response.find('ASSUMPTIONS:')
                        analysis = raw_response[analysis_start:assumptions_start].strip()
                        
                        # Extract assumptions
                        limitations_start = raw_response.find('LIMITATIONS:')
                        assumptions = raw_response[assumptions_start:limitations_start].strip()
                        
                        # Extract limitations
                        recommendations_start = raw_response.find('RECOMMENDATIONS:')
                        limitations = raw_response[limitations_start:recommendations_start].strip()
                        
                        # Extract recommendations
                        recommendations = raw_response[recommendations_start:].strip()
                        
                        return ExpertResponse(
                            confidence=confidence,
                            analysis={
                                "main_points": [analysis],
                                "details": analysis,
                                "assumptions": [a.strip() for a in assumptions.split('-') if a.strip()],
                                "limitations": [l.strip() for l in limitations.split('-') if l.strip()]
                            },
                            recommendations=[
                                {
                                    "suggestion": r.strip(),
                                    "rationale": "From expert analysis",
                                    "priority": 1
                                }
                                for r in recommendations.split('-') if r.strip()
                            ],
                            follow_up=[]
                        )
                    except Exception as e:
                        self.logger.warning("Error parsing expert response: %s", str(e))
                        return ExpertResponse.create_fallback(raw_response)

        except Exception as e:
            self.logger.warning("Error in expert consultation: %s", str(e))

        # Fallback: use the entire response as the prompt
        expert = self.domain_experts[domain]
        raw_response = await expert.query(response, self.logger)
        return ExpertResponse.create_fallback(raw_response)

    async def observe(self) -> None:
        """Observation phase: Gather information and consult experts as needed."""
        self.logger.info("Starting observation phase")
        prompt = self._construct_observation_prompt()
        response = await self._query_agent_llm(prompt)
        
        # Check if we need to consult any experts
        needed_experts = self._should_consult_experts(response)
        if needed_experts:
            expert_responses = []
            for domain in needed_experts:
                expert_response = await self.consult_expert(domain, response)
                if expert_response:
                    expert_responses.append({
                        "domain": domain,
                        "response": expert_response  # This is now an ExpertResponse object
                    })
            
            if expert_responses:
                # Format expert responses for agent analysis in a structured way
                analysis_request = {
                    "expert_consultations": [
                        {
                            "domain": er["domain"],
                            "confidence": er["response"].confidence,
                            "main_points": er["response"].analysis["main_points"],
                            "details": er["response"].analysis["details"],
                            "recommendations": [
                                {
                                    "suggestion": rec["suggestion"],
                                    "priority": rec["priority"]
                                }
                                for rec in er["response"].recommendations
                            ],
                            "limitations": er["response"].analysis["limitations"],
                            "follow_up": er["response"].follow_up
                        }
                        for er in expert_responses
                    ]
                }
                
                # Share expert responses with agent for analysis
                analysis_prompt = f"""I consulted the experts as requested. Here is their structured feedback:

                {json.dumps(analysis_request, indent=2)}

                Please analyze these expert responses and provide your analysis in this format:
                {{
                    "synthesis": {{
                        "key_findings": [str],
                        "confidence_assessment": str,
                        "critical_points": [str]
                    }},
                    "next_steps": [{{
                        "action": str,
                        "rationale": str,
                        "priority": int
                    }}],
                    "additional_consultations_needed": [{{
                        "expert": str,
                        "reason": str,
                        "question": str
                    }}]
                }}"""
                
                agent_analysis = await self._query_agent_llm(analysis_prompt)
                
                # Store structured responses in observation
                self.state.observations.append(
                    Observation(
                        data={
                            "initial_observation": response,
                            "expert_responses": [
                                {
                                    "domain": er["domain"],
                                    "response": er["response"].__dict__
                                }
                                for er in expert_responses
                            ],
                            "analysis": agent_analysis
                        },
                        source="combined"
                    )
                )
                return
        
        self.state.observations.append(
            Observation(
                data={"content": response},
                source="agent_llm"
            )
        )

    async def orient(self) -> None:
        """Orientation phase: Analyze gathered information."""
        self.logger.info("Starting orientation phase")
        prompt = self._construct_orientation_prompt()
        response = await self._query_agent_llm(prompt)
        
        # Check for user interaction needs
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                interaction_data = json.loads(response[start:end + 1])
                if 'user_interaction' in interaction_data:
                    user_req = interaction_data['user_interaction']
                    role = user_req.get('role')
                    if role in self.users:
                        self.logger.info("User interaction requested with %s", role)
                        # Handle user interaction based on implementation
                        # This will be implemented differently in Console vs API versions
                        user_response = await self._handle_user_interaction(user_req)
                        if user_response:
                            response += f"\nUser input received: {user_response}"
        except json.JSONDecodeError:
            self.logger.debug("No structured user interaction request found")
        
        # Check for expert consultation needs
        needed_experts = self._should_consult_experts(response)
        if needed_experts:
            expert_responses = []
            for domain in needed_experts:
                expert_response = await self.consult_expert(domain, response)
                if expert_response:
                    expert_responses.append({
                        "domain": domain,
                        "response": expert_response
                    })
            
            if expert_responses:
                # Format expert responses for orientation analysis
                analysis_request = {
                    "phase": "orientation",
                    "expert_insights": [
                        {
                            "domain": er["domain"],
                            "confidence": er["response"].confidence,
                            "analysis": er["response"].analysis,
                            "recommendations": er["response"].recommendations
                        }
                        for er in expert_responses
                    ]
                }
                
                # Request structured orientation analysis
                orientation_prompt = f"""Based on expert insights:

                {json.dumps(analysis_request, indent=2)}

                Please provide your orientation analysis in this format:
                {{
                    "situation_assessment": {{
                        "key_patterns": [str],
                        "implications": [str],
                        "uncertainties": [str]
                    }},
                    "expert_evaluation": {{
                        "consensus_points": [str],
                        "disagreements": [str],
                        "confidence_levels": str
                    }},
                    "knowledge_gaps": [{{
                        "area": str,
                        "impact": str,
                        "recommended_action": str
                    }}]
                }}"""
                
                orientation_analysis = await self._query_agent_llm(orientation_prompt)
                
                # Store structured orientation in context window
                self.state.context_window.append({
                    "timestamp": datetime.now().timestamp(),
                    "content": orientation_analysis,
                    "expert_insights": [
                        {
                            "domain": er["domain"],
                            "response": er["response"].__dict__
                        }
                        for er in expert_responses
                    ],
                    "phase": self.state.current_phase.value
                })
                return

        # If no expert consultation needed, store basic orientation
        self.state.context_window.append({
            "timestamp": datetime.now().timestamp(),
            "content": response,
            "phase": self.state.current_phase.value
        })

    async def decide(self) -> None:
        """Decision phase: Determine next actions based on orientation."""
        self.logger.info("Starting decision phase")
        prompt = self._construct_decision_prompt()
        response = await self._query_agent_llm(prompt)
        
        # Check for user interaction needs
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                interaction_data = json.loads(response[start:end + 1])
                if 'user_interaction' in interaction_data:
                    user_req = interaction_data['user_interaction']
                    role = user_req.get('role')
                    if role in self.users:
                        self.logger.info("User interaction requested with %s", role)
                        user_response = await self._handle_user_interaction(user_req)
                        if user_response:
                            response += f"\nUser input received: {user_response}"
        except json.JSONDecodeError:
            self.logger.debug("No structured user interaction request found")
        
        # Check for expert consultation needs
        needed_experts = self._should_consult_experts(response)
        if needed_experts:
            expert_responses = []
            for domain in needed_experts:
                expert_response = await self.consult_expert(domain, response)
                if expert_response:
                    expert_responses.append({
                        "domain": domain,
                        "response": expert_response
                    })
            
            if expert_responses:
                # Format expert responses for decision analysis
                analysis_request = {
                    "phase": "decision",
                    "expert_insights": [
                        {
                            "domain": er["domain"],
                            "confidence": er["response"].confidence,
                            "recommendations": er["response"].recommendations,
                            "limitations": er["response"].analysis["limitations"]
                        }
                        for er in expert_responses
                    ]
                }
                
                # Request structured decision analysis
                decision_prompt = f"""Based on expert insights:

                {json.dumps(analysis_request, indent=2)}

                Please provide your decision analysis in this format:
                {{
                    "decision": {{
                        "chosen_action": str,
                        "rationale": str,
                        "confidence": float,
                        "risks": [str]
                    }},
                    "alternatives": [{{
                        "action": str,
                        "pros": [str],
                        "cons": [str]
                    }}],
                    "prerequisites": [{{
                        "requirement": str,
                        "status": str
                    }}]
                }}"""
                
                decision_analysis = await self._query_agent_llm(decision_prompt)
                
                # Store structured decision
                self.state.working_memory.update({
                    "last_decision": decision_analysis,
                    "expert_insights": [
                        {
                            "domain": er["domain"],
                            "response": er["response"].__dict__
                        }
                        for er in expert_responses
                    ],
                    "timestamp": datetime.now().timestamp()
                })
                return

        # If no expert consultation needed, store basic decision
        self.state.working_memory.update({
            "last_decision": response,
            "timestamp": datetime.now().timestamp()
        })

    async def act(self) -> None:
        """Action phase: Execute decided actions and evaluate results."""
        self.logger.info("Starting action phase")
        prompt = self._construct_action_prompt()
        response = await self._query_agent_llm(prompt)
        
        # Check for user interaction needs during action
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                interaction_data = json.loads(response[start:end + 1])
                if 'user_interaction' in interaction_data:
                    user_req = interaction_data['user_interaction']
                    role = user_req.get('role')
                    if role in self.users:
                        self.logger.info("User interaction requested with %s", role)
                        user_response = await self._handle_user_interaction(user_req)
                        if user_response:
                            response += f"\nUser input received: {user_response}"
        except json.JSONDecodeError:
            self.logger.debug("No structured user interaction request found")
        
        # Check for expert consultation needs during action
        needed_experts = self._should_consult_experts(response)
        if needed_experts:
            expert_responses = []
            for domain in needed_experts:
                expert_response = await self.consult_expert(domain, response)
                if expert_response:
                    expert_responses.append({
                        "domain": domain,
                        "response": expert_response
                    })
            
            if expert_responses:
                # Format expert responses for action analysis
                analysis_request = {
                    "phase": "action",
                    "action_taken": response,
                    "expert_evaluations": [
                        {
                            "domain": er["domain"],
                            "confidence": er["response"].confidence,
                            "analysis": er["response"].analysis,
                            "follow_up": er["response"].follow_up
                        }
                        for er in expert_responses
                    ]
                }
                
                # Request structured action analysis
                action_prompt = f"""Based on expert evaluations:

                {json.dumps(analysis_request, indent=2)}

                Please provide your action analysis in this format:
                {{
                    "execution": {{
                        "status": str,
                        "outcome": str,
                        "success_metrics": [str]
                    }},
                    "issues": [{{
                        "description": str,
                        "severity": str,
                        "mitigation": str
                    }}],
                    "next_steps": [str]
                }}"""
                
                action_analysis = await self._query_agent_llm(action_prompt)
                
                # Store structured action results
                self.state.working_memory.update({
                    "last_action": action_analysis,
                    "expert_evaluations": [
                        {
                            "domain": er["domain"],
                            "response": er["response"].__dict__
                        }
                        for er in expert_responses
                    ],
                    "action_timestamp": datetime.now().timestamp()
                })
                return

        # If no expert consultation needed, store basic action
        self.state.working_memory.update({
            "last_action": response,
            "action_timestamp": datetime.now().timestamp()
        })

    def _construct_observation_prompt(self) -> str:
        """Construct prompt for the observation phase."""
        return f"""Current problem: {self.state.problem_statement}

        Based on the current state and history, what observations can you make?
        Consider:
        1. What information do we have?
        2. What information might we need?
        3. Should we consult any domain experts?

        If you need expert input, explicitly say "CONSULT <domain>: <question>"

        Previous observations: {self.state.observations[-3:] if self.state.observations else 'None'}
        """

    def _construct_orientation_prompt(self) -> str:
        """Construct prompt for the orientation phase."""
        observations = (
            self.state.observations[-3:] 
            if self.state.observations 
            else 'None'
        )
        return f"""Given our current observations and context:
        
        Problem: {self.state.problem_statement}
        Recent Observations: {observations}
        
        Please analyze this information and provide:
        1. Key patterns or insights
        2. Potential implications
        3. Areas needing further investigation
        """

    def _construct_decision_prompt(self) -> str:
        """Construct prompt for the decision phase."""
        return f"""Based on our current understanding:
        
        Problem: {self.state.problem_statement}
        Context: {self.state.context_window[-1] if self.state.context_window else 'None'}
        
        What should be our next steps? Consider:
        1. Possible actions
        2. Expected outcomes
        3. Potential risks
        """

    def _construct_action_prompt(self) -> str:
        """Construct prompt for the action phase."""
        return f"""Execute the decided action:
        
        Problem: {self.state.problem_statement}
        Decision: {self.state.working_memory.get('last_decision', 'No decision recorded')}
        
        Please:
        1. Execute the decided action
        2. Document the results
        3. Note any unexpected outcomes
        """

    @staticmethod
    def _validate_decision_format(data: Dict) -> bool:
        """Validate the decision analysis format."""
        try:
            assert 'decision' in data
            decision = data['decision']
            assert all(k in decision for k in ['chosen_action', 'rationale', 'confidence', 'risks'])
            assert isinstance(decision['confidence'], (int, float))
            assert 0 <= decision['confidence'] <= 1
            
            assert 'alternatives' in data
            for alt in data['alternatives']:
                assert all(k in alt for k in ['action', 'pros', 'cons'])
            
            assert 'prerequisites' in data
            for prereq in data['prerequisites']:
                assert all(k in prereq for k in ['requirement', 'status'])
            
            return True
        except AssertionError:
            return False

    @staticmethod
    def _validate_action_format(data: Dict) -> bool:
        """Validate the action analysis format."""
        try:
            assert 'execution' in data
            execution = data['execution']
            assert all(k in execution for k in ['status', 'outcome', 'success_metrics'])
            
            assert 'issues' in data
            for issue in data['issues']:
                assert all(k in issue for k in ['description', 'severity', 'mitigation'])
            
            assert 'next_steps' in data
            assert isinstance(data['next_steps'], list)
            
            return True
        except AssertionError:
            return False

    async def _handle_user_interaction(self, interaction_request: Dict) -> Optional[str]:
        """Handle structured user interaction request."""
        try:
            role = interaction_request.get('role')
            if role not in self.users:
                self.logger.warning("Requested interaction with unknown role: %s", role)
                return None

            user = self.users[role]
            purpose = interaction_request.get('purpose', 'No purpose specified')
            question = interaction_request.get('question', 'No question specified')
            context = interaction_request.get('context', 'No context provided')

            self.logger.info("User interaction requested:")
            self.logger.info("Role: %s (%s)", role, user.name)
            self.logger.info("Purpose: %s", purpose)
            self.logger.info("Question: %s", question)
            self.logger.info("Context: %s", context)

            # Check if user has required permissions
            required_permission = self._determine_required_permission(purpose)
            if required_permission not in user.permissions:
                self.logger.warning(
                    "User %s lacks required permission: %s",
                    user.name,
                    required_permission
                )
                return None

            # Actual interaction implementation is provided by subclasses
            return await self._get_user_response(interaction_request)

        except Exception as e:
            self.logger.error("Error handling user interaction: %s", str(e))
            return None

    def _determine_required_permission(self, purpose: str) -> str:
        """Determine required permission based on interaction purpose."""
        purpose_lower = purpose.lower()
        if 'clarif' in purpose_lower:
            return 'clarify'
        elif 'modif' in purpose_lower or 'chang' in purpose_lower:
            return 'modify'
        elif 'valid' in purpose_lower or 'verif' in purpose_lower:
            return 'validate'
        elif 'specif' in purpose_lower:
            return 'specify_problem'
        elif 'review' in purpose_lower:
            return 'review'
        elif 'approv' in purpose_lower:
            return 'approve'
        else:
            return 'clarify'  # Default permission

    @abstractmethod
    async def _get_user_response(self, interaction_request: Dict) -> Optional[str]:
        """Get response from user based on interaction request.
        
        To be implemented by console/API subclasses.
        """
        pass

    def _needs_user_input(self, context: Dict) -> Optional[Dict]:
        """Determine if user input is needed based on current context.
        
        Returns:
            Optional[Dict]: User interaction request if needed, None otherwise
        """
        phase = context.get('phase', self.state.current_phase.value)
        
        # Check confidence levels
        if 'confidence' in context and context['confidence'] < 0.7:
            return {
                "user_interaction": {
                    "role": "problem_owner",
                    "purpose": "low_confidence_verification",
                    "question": "I'm not fully confident about this approach. Would you like me to explain my concerns?",
                    "context": str(context.get('concerns', 'Confidence below threshold'))
                }
            }

        # Check for multiple viable options
        if 'alternatives' in context and len(context['alternatives']) > 1:
            return {
                "user_interaction": {
                    "role": "problem_owner",
                    "purpose": "path_selection",
                    "question": "I see multiple viable approaches. Would you like to review them?",
                    "context": str(context.get('alternatives', 'Multiple paths available'))
                }
            }

        # Phase-specific checks
        if phase == OODAPhase.OBSERVE.value:
            # Check if problem statement needs refinement
            if len(self.state.observations) <= 1:
                ambiguities = context.get('ambiguities', [])
                if ambiguities:
                    return {
                        "user_interaction": {
                            "role": "problem_owner",
                            "purpose": "clarify_problem",
                            "question": "Could you help clarify some aspects of the problem?",
                            "context": str(ambiguities)
                        }
                    }

        elif phase == OODAPhase.DECIDE.value:
            # Check for critical decisions
            risks = context.get('risks', [])
            if risks:
                return {
                    "user_interaction": {
                        "role": "problem_owner",
                        "purpose": "risk_assessment",
                        "question": "I've identified some risks with the proposed approach. Should we review them?",
                        "context": str(risks)
                    }
                }

        # Check for unexpected results
        if 'unexpected' in context:
            return {
                "user_interaction": {
                    "role": "problem_owner",
                    "purpose": "handle_unexpected",
                    "question": "I've encountered something unexpected. Would you like to review it?",
                    "context": str(context['unexpected'])
                }
            }

        return None

    async def _check_and_handle_user_interaction(
        self, 
        phase_response: str,
        context: Dict
    ) -> str:
        """Check if user interaction is needed and handle it if so."""
        # First check for explicit interaction requests in the response
        try:
            start = phase_response.find('{')
            end = phase_response.rfind('}')
            if start != -1 and end != -1:
                interaction_data = json.loads(phase_response[start:end + 1])
                if 'user_interaction' in interaction_data:
                    user_response = await self._handle_user_interaction(
                        interaction_data['user_interaction']
                    )
                    if user_response:
                        return f"{phase_response}\nUser input: {user_response}"
        except json.JSONDecodeError:
            self.logger.debug("No explicit user interaction request found")

        # Then check if we need to initiate user interaction
        interaction_request = self._needs_user_input(context)
        if interaction_request:
            user_response = await self._handle_user_interaction(
                interaction_request['user_interaction']
            )
            if user_response:
                return f"{phase_response}\nUser input: {user_response}"

        return phase_response


class ConsoleOODAAgent(OODAAgent):
    """Console implementation of OODA agent."""
    
    async def start_session(self, initial_problem: Optional[str] = None):
        """Start a console-based interaction session."""
        if not initial_problem:
            initial_problem = await self._query_user(
                "Please describe the problem you need help with:"
            )
        
        self.initialize_problem(initial_problem)
        await self._solve_problem()

    async def _solve_problem(self):
        """Main problem-solving loop."""
        self.logger.info("Starting problem-solving loop")
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                self.logger.info("Starting OODA cycle %d", cycle_count)
                solution_found = await self.run_ooda_loop()
                
                if solution_found:
                    self.logger.info("Potential solution found in cycle %d", cycle_count)
                    response = await self._query_user(
                        "I believe I have a solution. Would you like to see it? (yes/no)"
                    )
                    if response.lower().startswith('y'):
                        solution = self.state.working_memory.get('last_action')
                        await self._inform_user(f"Solution: {solution}")
                        
                        if await self._confirm_solution():
                            self.logger.info("Solution accepted by user")
                            break
                
                if self._is_stuck():
                    self.logger.warning("Agent is stuck, requesting user assistance")
                    if not await self._handle_stuck():
                        self.logger.info("User chose to end session while stuck")
                        break

        except KeyboardInterrupt:
            self.logger.warning("Session interrupted by user after %d cycles", cycle_count)
            await self.handle_interruption()

    async def handle_interruption(self) -> bool:
        """Handle keyboard interrupt by providing user options."""
        menu = (
            "Session interrupted. What would you like to do?\n"
            "1. Provide feedback/guidance\n"
            "2. Review current progress\n"
            "3. Exit session\n"
            "Enter number (1-3):"
        )
        options = await self._query_user(menu)
        
        if options == "1":
            feedback = await self._query_user("Please provide your feedback or guidance:")
            self.state.agent_history.add_message("user", feedback)
            return True
        elif options == "2":
            observations = (
                self.state.observations[-3:] 
                if self.state.observations 
                else 'None'
            )
            await self._inform_user(
                f"Current problem statement: {self.state.problem_statement}\n"
                f"Current phase: {self.state.current_phase.value}\n"
                f"Recent observations: {observations}"
            )
            await self._query_user("Press Enter to continue.")
            return True
        else:
            confirm = await self._query_user("Are you sure you want to exit? (yes/no)")
            return not confirm.lower().startswith('y')

    def _is_stuck(self) -> bool:
        """Determine if the agent is stuck and needs user input."""
        # Check for repeated similar states
        if len(self.state.observations) >= 3:
            last_three = self.state.observations[-3:]
            if all(
                obs.data.get('content') == last_three[0].data.get('content')
                for obs in last_three
            ):
                return True
        
        # Check for low confidence markers
        last_decision = self.state.working_memory.get('last_decision', '')
        uncertainty_markers = ['uncertain', 'unclear', 'not sure', 'ambiguous']
        if any(marker in last_decision.lower() for marker in uncertainty_markers):
            return True
        
        # Check for lack of progress
        if self.state.working_memory.get('no_progress_count', 0) > 3:
            return True
        
        return False

    async def _query_user(self, message: str, require_response: bool = True) -> Optional[str]:
        """Get input from user with optional prompt message."""
        self.logger.debug("Querying user: %s", message)
        print(f"\nAgent: {message}")
        if require_response:
            print("Your response (Ctrl+C to interrupt): ")
            response = input("> ").strip()
            self.logger.debug("User response: %s", response)
            return response
        return None

    async def _inform_user(self, message: str):
        """Send a message to the user."""
        print(f"\nAgent: {message}")

    async def _confirm_solution(self) -> bool:
        """Confirm if the solution is satisfactory."""
        response = await self._query_user(
            "Is this solution satisfactory? (yes/no)"
        )
        return response.lower().startswith('y')

    async def _handle_stuck(self) -> bool:
        """Handle the case when the agent is stuck."""
        help_needed = self.state.working_memory.get(
            'help_needed', 
            'proceeding with the solution'
        )
        response = await self._query_user(
            f"I'm having difficulty {help_needed}. Would you like to:\n"
            "1. Provide guidance\n"
            "2. Modify the problem statement\n"
            "3. End the session\n"
            "Please choose (1-3):"
        )
        
        if response == "1":
            guidance = await self._query_user("Please provide your guidance:")
            msg = f"Guidance: {guidance}"
            self.state.agent_history.add_message("user", msg)
            return True
        elif response == "2":
            new_statement = await self._query_user(
                "Please revise the problem statement:"
            )
            self.state.problem_statement = new_statement
            return True
        return False


class ConsoleModelUsingAgent(ModelUsingAgent, ConsoleOODAAgent):
    """Console implementation of Model-Using OODA agent."""
    
    async def start_session(self, initial_problem: Optional[str] = None):
        """Start a console-based interaction session with domain experts."""
        if not initial_problem:
            initial_problem = await self._query_user(
                "Please describe the problem you need help with:"
            )
        
        self.initialize_problem(initial_problem)
        await self._solve_problem()

    async def _determine_domain(self, problem_desc: str) -> str:
        """Determine required domain expertise and validate with user."""
        prompt = f"""Analyze this problem and determine the primary domain 
        expertise needed to solve it. Be specific and precise:
        
        Problem: {problem_desc}"""
        
        domain = await self._query_agent_llm(prompt)
        
        # Confirm domain with user
        response = await self._query_user(
            f"I believe this problem requires expertise in: {domain}\n"
            "Is this the right domain of expertise? (yes/no)"
        )
        
        if response.lower().startswith('n'):
            domain = await self._query_user(
                "What domain of expertise would be more appropriate?"
            )
        
        return domain

    async def _get_user_response(self, interaction_request: Dict) -> Optional[str]:
        """Get response from user based on interaction request."""
        try:
            role = interaction_request.get('role')
            question = interaction_request.get('question', 'No question specified')
            context = interaction_request.get('context', '')
            purpose = interaction_request.get('purpose', '')
            
            # Format the prompt with context and purpose
            prompt = f"""[User Interaction Request]
            Role: {role}
            Purpose: {purpose}
            Context: {context}
            
            Question: {question}"""
            
            # Get user response
            response = await self._query_user(prompt)
            
            # Log the interaction
            self.logger.info("User interaction completed:")
            self.logger.info("Question: %s", question)
            self.logger.info("Response: %s", response)
            
            # Store interaction in history
            self.state.agent_history.add_message(
                "user",
                f"Q: {question}\nA: {response}"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Error getting user response: %s", 
                str(e),
                exc_info=True
            )
            return None


class APIModelUsingAgent(ModelUsingAgent):
    """API implementation of Model-Using OODA agent."""
    
    def __init__(
        self,
        agent_llm_config: Dict,
        domain_experts: List[DomainExpertLLM],
        callback_url: str,
        session_id: str,
        agent_system_prompt: Optional[str] = None
    ):
        """Initialize API-based agent with callback URL and session tracking."""
        super().__init__(agent_llm_config, domain_experts, agent_system_prompt)
        self.callback_url = callback_url
        self.session_id = session_id
        self.http_client = None

    async def _wait_for_input(self, input_type: str) -> str:
        """Wait for specific type of input through API."""
        self.logger.info("Waiting for input type: %s", input_type)
        max_retries = 30
        retry_delay = 2
        
        for attempt in range(max_retries):
            self.logger.debug(
                "Attempt %d/%d waiting for %s", 
                attempt + 1, 
                max_retries, 
                input_type
            )
            response = await self._send_update({
                "type": "input_request",
                "input_type": input_type,
                "status": "waiting"
            })
            
            if response.get("status") == "input_ready":
                self.logger.info("Received input for %s", input_type)
                return response.get("input", "")
            
            self.logger.debug(
                "No input ready, waiting %d seconds before retry", 
                retry_delay
            )
            await asyncio.sleep(retry_delay)
        
        error_msg = f"Timeout waiting for {input_type} input"
        self.logger.error(error_msg)
        await self._send_update({
            "type": "error",
            "error": error_msg
        })
        
        raise TimeoutError(error_msg)

    async def _send_update(self, data: Dict) -> Dict:
        """Send update to callback URL and wait for response."""
        self.logger.debug("Sending update: %s", data)
        data['session_id'] = self.session_id
        # Implementation would use self.http_client to send POST request
        self.logger.debug("Update sent successfully")
        return {"status": "success"}  # Placeholder

    async def _solve_problem(self):
        """Main problem-solving loop for API-based interaction."""
        try:
            while True:
                solution_found = await self.run_ooda_loop()
                
                if solution_found:
                    solution = self.state.working_memory.get('last_action')
                    response = await self._send_update({
                        "type": "solution",
                        "solution": solution
                    })
                    
                    if response.get('accepted', False):
                        break
                    else:
                        feedback = response.get('feedback')
                        if feedback:
                            self.state.working_memory['solution_feedback'] = feedback
                
                if self._is_stuck():
                    if not await self._handle_stuck():
                        break

        # pylint: disable=broad-exception-caught
        except Exception as e:
            await self._send_update({
                "type": "error",
                "error": str(e)
            })

    async def _handle_stuck(self) -> bool:
        """Handle stuck state through API."""
        help_needed = self.state.working_memory.get('help_needed', 'proceeding with the solution')
        
        response = await self._send_update({
            "type": "stuck",
            "message": help_needed,
            "options": [
                "provide_guidance",
                "modify_problem",
                "end_session"
            ]
        })
        
        action = response.get('action')
        if action == 'provide_guidance':
            guidance = response.get('guidance')
            self.state.agent_history.add_message("user", f"Guidance: {guidance}")
            return True
        elif action == 'modify_problem':
            new_problem = response.get('new_problem')
            self.state.problem_statement = new_problem
            return True
        return False

    async def start_session(self, initial_problem: Optional[str] = None):
        """Start an API-based interaction session."""
        if not initial_problem:
            initial_problem = await self._wait_for_input("initial_problem")
        
        self.initialize_problem(initial_problem)
        await self._solve_problem()

    async def handle_interruption(self) -> bool:
        """Handle interruption in API context."""
        response = await self._send_update({
            "type": "interrupted",
            "options": [
                "provide_feedback",
                "review_progress",
                "end_session"
            ]
        })
        return response.get('continue', False)

    def _is_stuck(self) -> bool:
        """Determine if the agent is stuck and needs help."""
        # Use the same implementation as ConsoleOODAAgent
        if len(self.state.observations) >= 3:
            last_three = self.state.observations[-3:]
            if all(
                obs.data.get('content') == last_three[0].data.get('content')
                for obs in last_three
            ):
                return True
        
        last_decision = self.state.working_memory.get('last_decision', '')
        uncertainty_markers = ['uncertain', 'unclear', 'not sure', 'ambiguous']
        if any(marker in last_decision.lower() for marker in uncertainty_markers):
            return True
        
        if self.state.working_memory.get('no_progress_count', 0) > 3:
            return True
        
        return False

def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    json_logs: bool = False,
    include_performance: bool = True
):
    """Configure logging for the MUA system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for logs
        log_file: Path to log file (if None, logs to console only)
        json_logs: If True, output logs in JSON format
        include_performance: If True, include performance metrics in logs
    """
    if json_logs:
        format_string = (
            '{"timestamp":"%(asctime)s", "name":"%(name)s", "level":"%(levelname)s", '
            '"message":"%(message)s"'
            + (', "duration_ms":%(duration_ms)s' if include_performance else '')
            + '}'
        )
    elif not format_string:
        base_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if include_performance:
            base_format += ' - Duration: %(duration_ms)sms'
        format_string = base_format

    handlers = []
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=handlers
    )
