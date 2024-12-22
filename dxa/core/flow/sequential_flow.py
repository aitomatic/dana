class SequentialFlow(BaseFlow):
    def get_next_step(self) -> Optional[Any]:
        """Get next step in sequence."""
        return super().get_next_step() 