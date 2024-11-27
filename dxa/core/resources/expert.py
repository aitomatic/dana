"""Expert resource implementation for DXA.

This module implements domain-expert behavior using Large Language Models (LLMs).
It combines domain expertise definitions with LLM capabilities to create
specialized agents that can handle domain-specific queries with high competency.

Classes:
    ExpertResource: LLM-powered domain expert resource

Features:
    - Domain-specific expertise configuration
    - Confidence-based query handling
    - Enhanced prompting with domain context
    - Automatic system prompt generation

Example:
    from dxa.core.capabilities.expertise import DomainExpertise
    
    expertise = DomainExpertise(
        name="Mathematics",
        capabilities=["algebra", "calculus"],
        keywords=["solve", "equation", "derivative"]
    )
    
    expert = ExpertResource(
        name="math_expert",
        expertise=expertise,
        config={"model": "gpt-4"}
    )
    
    response = await expert.query({
        "prompt": "Solve the equation x^2 + 2x + 1 = 0"
    })
"""

from typing import Dict, Any, Optional
from dxa.core.resources.llm_resource import LLMResource, LLMError
from dxa.core.capabilities.expertise import DomainExpertise

class ExpertResource(LLMResource):
    """A domain-expert LLM resource."""
    
    def __init__(
        self,
        name: str,
        expertise: DomainExpertise,
        config: Dict[str, Any],
        system_prompt: Optional[str] = None,
        confidence_threshold: float = 0.7
    ):
        """Initialize expert resource.
        
        Args:
            name: Name of this expert
            expertise: Domain expertise definition
            config: LLM configuration
            system_prompt: System prompt defining expert's role
            confidence_threshold: Threshold for accepting queries
        """
        super().__init__(
            name=name,
            config=config,
            system_prompt=system_prompt or self._generate_system_prompt(expertise)
        )
        self.expertise = expertise
        self.confidence_threshold = confidence_threshold
        self.description = f"Expert in {expertise.name}"

    def _generate_system_prompt(self, expertise: DomainExpertise) -> str:
        """Generate a system prompt from expertise definition."""
        capabilities_str = "\n".join(f"- {cap}" for cap in expertise.capabilities)
        return f"""You are an expert in {expertise.name}.
        
        Your expertise includes:
        {capabilities_str}
        
        Description: {expertise.description}
        
        Always provide detailed explanations and show your work step by step."""

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this expert can handle the request.
        
        An expert can handle a request if:
        1. It's a valid LLM request (parent check)
        2. The query matches the expert's domain
        3. Required information is provided
        
        Args:
            request: The request to check
            
        Returns:
            True if the expert can handle this request
        """
        # First check if it's a valid LLM request
        if not super().can_handle(request):
            return False
            
        prompt = request['prompt'].lower()
        
        # Check if query matches domain keywords
        matches_domain = any(
            keyword.lower() in prompt 
            for keyword in self.expertise.keywords
        )
        
        # Check if required information is provided
        has_requirements = all(
            requirement.lower() in prompt
            for requirement in self.expertise.requirements
        )
        
        return matches_domain and has_requirements

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query the expert.
        
        Adds domain context to the request before querying.
        
        Args:
            request: Query request containing prompt and parameters
            **kwargs: Additional query parameters
            
        Returns:
            Dict containing query response
            
        Raises:
            LLMError: If request cannot be handled by this expert
        """
        if not self.can_handle(request):
            raise LLMError(
                f"Request cannot be handled by {self.expertise.name} expert"
            )

        # Add domain context to the prompt
        enhanced_prompt = f"""As an expert in {self.expertise.name}, 
        with capabilities in:
        {', '.join(self.expertise.capabilities)}

        Please address this query:
        {request['prompt']}"""

        enhanced_request = {
            **request,
            "prompt": enhanced_prompt
        }

        return await super().query(enhanced_request, **kwargs) 