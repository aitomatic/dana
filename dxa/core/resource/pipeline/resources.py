"""Simple pipeline resource implementations for examples."""

from typing import Dict, Any
from ..base_resource import BaseResource

class SensorReader(BaseResource):
    """Simple sensor reader."""
    
    def __init__(self, name: str = "sensor_reader"):
        super().__init__(name)
    
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate reading sensor."""
        return {"temperature": 25.0}

class Analyzer(BaseResource):
    """Simple analyzer."""
    
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temperature."""
        return {"temperature": request["temperature"], "status": "normal"}

class Reporter(BaseResource):
    """Simple reporter."""
    
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Report status."""
        return request 