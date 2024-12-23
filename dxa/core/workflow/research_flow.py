"""Research workflow implementation."""

from dxa.common.graph import Node, create_sequence
from .Workflow import Workflow

class ResearchWorkflow(Workflow):
    """Basic research workflow pattern."""
    
    def __init__(self):
        super().__init__()
        
        # Define research steps
        steps = [
            Node("gather", "TASK", "Gather information"),
            Node("analyze", "TASK", "Analyze information"), 
            Node("synthesize", "TASK", "Synthesize findings")
        ]
        
        # Create sequential flow
        workflow = create_sequence(steps)
        
        # Add to self
        self.nodes = workflow.nodes
        self.edges = workflow.edges
        self._build_adjacency_lists()