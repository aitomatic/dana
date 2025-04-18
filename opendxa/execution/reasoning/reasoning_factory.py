"""Factory for creating reasoning patterns."""

from typing import Optional, cast

from opendxa.base.execution.execution_types import Objective
from opendxa.execution.reasoning.reasoning import Reasoning
from opendxa.base.execution.execution_factory import ExecutionFactory

class ReasoningFactory(ExecutionFactory[Reasoning]):
    """Creates reasoning pattern instances."""
    
    # Override class variables
    graph_class = Reasoning
    
    @classmethod
    def create_reasoning(
        cls, 
        objective: Objective, 
        name: Optional[str] = None
    ) -> Reasoning:
        """Create a reasoning instance."""
        return cast(Reasoning, cls.create_basic_graph(objective, name))