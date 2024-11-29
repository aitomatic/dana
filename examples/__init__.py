"""Example implementations of DXA agents.

This module provides example implementations of different DXA agent types,
demonstrating various use cases and configurations.

Examples:
    1. Interactive Math: Interactive math problem solving
    2. Web Scraper: Automated web data extraction
    3. WebSocket Solver: Network-based problem solving
    4. Collaborative Research: Multi-agent coordination
"""

from examples.math_tutor import main as run_math_solver
from examples.web_scraper import main as run_web_scraper
from examples.websocket_solver import main as run_websocket_solver
from examples.collaborative_research import main as run_collaborative_research

__all__ = [
    'run_math_solver',
    'run_web_scraper',
    'run_websocket_solver',
    'run_collaborative_research'
]

# Example usage documentation
USAGE = """
DXA (Domain-Expert Agent) Examples
================================

Available examples:

1. Interactive Math (interactive_math.py):
   - Interactive console-based math problem solver
   - Uses Chain of Thought reasoning
   - Uses math expert resource
   - Environment variables: OPENAI_API_KEY

2. Web Scraper (automation_web.py):
   - Automated web scraping workflow
   - Step-by-step validation
   - Environment variables: OPENAI_API_KEY

3. WebSocket Solver (websocket_solver.py):
   - WebSocket-based problem solver
   - Uses OODA Loop reasoning
   - Environment variables: OPENAI_API_KEY, WEBSOCKET_URL

4. Collaborative Research (collaborative_research.py):
   - Multi-agent research coordination
   - Combines console and WebSocket agents
   - Environment variables: OPENAI_API_KEY, WEBSOCKET_URL

Running Examples:
1. From project root:
   python examples/<example_file>.py

2. After installing DXA:
   pip install -e .
   python examples/<example_file>.py

Configuration:
- All examples use configuration from dxa/common/config.py
- Configuration can be provided via YAML or JSON files
- Environment variables can override configuration

Example Usage:
    ```python
    from examples import run_collaborative_research
    
    # Required environment variables:
    # - OPENAI_API_KEY
    # - WEBSOCKET_URL
    
    await run_collaborative_research()
    ```
""" 