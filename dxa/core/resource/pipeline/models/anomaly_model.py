"""Anomaly detection model components."""

from typing import Dict, Any
from ...base_resource import BaseResource

class AnomalyModel(BaseResource):
    """Base class for anomaly detection models."""
    
    def __init__(self, name: str, threshold: float = 2.0) -> None:
        super().__init__(name)
        self.threshold = threshold
        
    async def initialize(self) -> None:
        """Initialize model."""
        self._is_available = True
        
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in data."""
        raise NotImplementedError("Subclasses must implement query") 