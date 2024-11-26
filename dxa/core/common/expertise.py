"""Domain expertise definitions for DXA."""

from dataclasses import dataclass
from typing import List, Dict, Any
from dxa.core.resources.base_resource import BaseResource

@dataclass
class DomainExpertise:
    """Definition of a domain of expertise."""
    name: str                    # e.g., "mathematics"
    description: str            # What this expert knows
    capabilities: List[str]     # What this expert can do
    keywords: List[str]         # Trigger words/phrases
    requirements: List[str]     # What input this expert needs
    example_queries: List[str]  # Example questions this expert can answer

class ExpertResource(BaseResource):
    """A resource with specific domain expertise."""
    
    def __init__(
        self,
        resource_name: str,
        expertise: DomainExpertise,
        resource: BaseResource,
        confidence_threshold: float = 0.7
    ):
        """Initialize expert resource.
        
        Args:
            resource_name: Name of this expert resource
            expertise: Domain expertise definition
            resource: The underlying resource (e.g., LLM)
            confidence_threshold: When to use this expert (0-1)
        """
        super().__init__(
            name=resource_name,
            description=expertise.description
        )
        self.expertise = expertise
        self.resource = resource
        self.confidence_threshold = confidence_threshold

    async def query(
        self,
        request: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Query this expert resource."""
        if not self.can_handle(request):
            raise ValueError(f"Expert {self.name} cannot handle this request")
        return await self.resource.query(request, **kwargs)

    def can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if this expert can handle the request."""
        # Check if underlying resource can handle it
        if not self.resource.can_handle(request):
            return False
            
        # Check if request matches expertise
        query = request.get('prompt', '').lower()
        return any(keyword.lower() in query for keyword in self.expertise.keywords)

    async def initialize(self) -> None:
        """Initialize the expert resource."""
        await self.resource.initialize()
        self._is_available = True

    async def cleanup(self) -> None:
        """Clean up the expert resource."""
        await self.resource.cleanup()
        self._is_available = False