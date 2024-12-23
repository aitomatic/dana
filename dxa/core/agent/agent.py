"""Agent implementation with progressive configuration.

Core Components:
    - LLM: Required language model for reasoning
    - Reasoning: Strategy for approaching tasks
    - Resources: Optional tools and capabilities
    - IO: Optional interaction handlers

Example:
    ```python
    agent = Agent("researcher", llm=LLMResource(...))\\
        .with_reasoning("cot")\\
        .with_resources({"search": SearchResource()})\\
        .with_capabilities({"research": ResearchCapability()})
    
    result = await agent.run("Research quantum computing")
    ```

See dxa/agent/README.md for detailed design documentation.
"""

from typing import Dict, Union, Optional, Any
from ..workflow import BaseFlow
from ..types import Objective
from ..planning import BasePlanner, PlannerFactory 
from ..reasoning import BaseReasoner, ReasonerFactory
from ..capability import BaseCapability
from ..resource import BaseResource, LLMResource
from ..io import BaseIO, IOFactory
from ..state import AgentState
from .agent_runtime import AgentRuntime
from ...common.utils.config import load_agent_config

class Agent:
    """Main agent interface with built-in execution management."""
    
    def __init__(self, workflow=None, resources=None):
        self.workflow = workflow
        self.resources = resources or {}
        
    def ask(self, question: str) -> str:
        """Simple Q&A interface for direct LLM interaction."""
        if "llm" not in self.resources:
            raise ValueError("LLM resource required for ask()")
            
        return self.resources["llm"].generate(question)
        
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute full workflow with given context."""
        if not self.workflow:
            raise ValueError("Workflow required for execute()")
        # ... workflow execution logic ...