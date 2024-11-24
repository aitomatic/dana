"""Example implementations of DXA agents."""

from examples.math_solver import main as run_math_solver
from examples.collaborative_research import main as run_collaborative_research
from examples.websocket_solver import main as run_websocket_solver

from dxa import (
    ConsoleAgent,
    WebSocketAgent,
    ChainOfThoughtReasoning,
    OODALoopReasoning,
    AgentState,
    StateManager
)

__all__ = [
    'run_math_solver',
    'run_collaborative_research',
    'run_websocket_solver',
    'ConsoleAgent',
    'WebSocketAgent',
    'ChainOfThoughtReasoning',
    'OODALoopReasoning',
    'AgentState',
    'StateManager'
]

# Example usage documentation
USAGE = """
DXA (Domain-Expert Agent) Examples
================================

Available examples:
1. Math Solver (math_solver.py):
   - Interactive console-based math problem solver
   - Uses Chain of Thought reasoning (ChainOfThoughtReasoning)
   - Uses ConsoleAgent for interaction
   - Environment variables: OPENAI_API_KEY

2. Collaborative Research (collaborative_research.py):
   - Multiple agents working together on research tasks
   - Uses both ConsoleAgent and WebSocketAgent
   - Uses both ChainOfThoughtReasoning and OODALoopReasoning
   - Environment variables: OPENAI_API_KEY, WEBSOCKET_URL

3. WebSocket Solver (websocket_solver.py):
   - WebSocket-based problem solver
   - Uses WebSocketAgent with OODALoopReasoning
   - Environment variables: OPENAI_API_KEY, WEBSOCKET_URL

Each example demonstrates different DXA capabilities:
- State management (StateManager)
- Agent lifecycle (AgentState)
- Different reasoning patterns
- Different I/O methods
"""
