"""Rule-based processing components."""

from typing import Dict, Any
from ...base_resource import BaseResource

class Thresholder(BaseResource):
    """Check value against threshold."""
    
    def __init__(self, threshold: float = 25.0) -> None:
        super().__init__(name=f"threshold_{threshold}")
        self.threshold = threshold
        
    async def initialize(self) -> None:
        """Initialize resource."""
        self._is_available = True
        
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Check if average exceeds threshold."""
        if "average" not in request:
            return {"error": "No average value"}
            
        is_high = request["average"] > self.threshold
        return {
            "average": request["average"],
            "threshold": self.threshold,
            "is_high": is_high
        } 