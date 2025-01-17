"""Statistical processing components."""

from typing import Dict, Any, List
from ...base_resource import BaseResource

class Averager(BaseResource):
    """Calculate rolling average."""
    
    def __init__(self, window_size: int = 5) -> None:
        super().__init__(name=f"averager_{window_size}")
        self.window_size = window_size
        self._values: List[float] = []
        
    async def initialize(self) -> None:
        """Initialize resource."""
        self._values = []
        self._is_available = True
        
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate rolling average."""
        if "temperature" not in request:
            return {"error": "No temperature value"}
            
        self._values.append(request["temperature"])
        if len(self._values) > self.window_size:
            self._values.pop(0)
            
        avg = sum(self._values) / len(self._values)
        return {"average": avg} 