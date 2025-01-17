"""Classification model components."""

from typing import Dict, Any, List
from ...base_resource import BaseResource

class ClassificationModel(BaseResource):
    """Base class for classification models."""
    
    def __init__(self, name: str, classes: List[str]) -> None:
        super().__init__(name)
        self.classes = classes
        
    async def initialize(self) -> None:
        """Initialize model."""
        self._is_available = True
        
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Classify input data."""
        raise NotImplementedError("Subclasses must implement query") 