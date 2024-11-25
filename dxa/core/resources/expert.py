"""Expert resource implementation."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dxa.core.resources.llm_resource import LLMResource, LLMError

@dataclass
class DomainExpertise:
    """Definition of a domain of expertise."""
    name: str
    description: str
    capabilities: List[str]
    keywords: List[str]
    requirements: List[str]
    example_queries: List[str]

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
            system_prompt=system_prompt
        )
        self.expertise = expertise
        self.confidence_threshold = confidence_threshold
        self.description = f"Expert in {expertise.name}"

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