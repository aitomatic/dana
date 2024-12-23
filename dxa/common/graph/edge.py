"""Base edge definition for directed graphs."""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Edge:
    """Base class for graph edges."""
    source: str
    target: str
    condition: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source, self.target))
        
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if edge condition matches given context."""
        if not self.condition:
            return True
            
        # Simple condition check - just verify key exists with expected value
        key, value = self.condition.split('==')
        key = key.strip()
        value = value.strip(' "\'')
        
        return context.get(key) == value