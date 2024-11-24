"""Model-using agent implementation."""

from typing import Dict, List, Optional
from dxa.core.ooda_agent import OODAAgent
from dxa.experts.domain import DomainExpertLLM
from dxa.users.roles import User

class AgentWithExperts(OODAAgent):
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

            When you need expert help, write:
            CONSULT <domain>: <your question>
            CONTEXT: <relevant context>
            REASON: <why you need expert input>

            When you need user input, write:
            ASK USER <role>: <your question>
            CONTEXT: <relevant context>
            PURPOSE: <why you need their input>"""

        # Add information about available experts and users
        expert_info = "\n\nYou have access to the following domain experts:\n" + \
                     "\n".join(f"- {expert.domain}" for expert in domain_experts)
        
        user_info = "\n\nYou are working with the following users:\n" + \
                   "\n".join(user.get_role_description() for user in users)
        
        full_prompt = agent_system_prompt + expert_info + user_info
        
        super().__init__(agent_llm_config, full_prompt)
        self.domain_experts = {expert.domain: expert for expert in domain_experts}
        self.users = {user.role: user for user in users}
        self.logger.info(
            "Initialized with experts in: %s and users: %s", 
            ", ".join(self.domain_experts.keys()),
            ", ".join(self.users.keys())
        )
