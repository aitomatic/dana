class BaseFlow(ABC):
    """Base class for flow control."""
    
    def __init__(self):
        self.steps = []
    
    def add_step(self, step: Any) -> None:
        """Add step to flow."""
        self.steps.append(step)
    
    def get_next_step(self) -> Optional[Any]:
        """Get next step in flow."""
        if not self.steps:
            return None
        return self.steps[0]
    
    def mark_complete(self, step: Any) -> None:
        """Mark step as complete."""
        if step in self.steps:
            self.steps.remove(step) 