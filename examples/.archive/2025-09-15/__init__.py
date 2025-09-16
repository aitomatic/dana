"""Example implementations of DXA agents.

This module provides example implementations of different DXA agent types,
demonstrating various use cases and configurations.

Examples:
    1. Math Tutor: Interactive math problem solving
    2. Web Scraper: Automated web data extraction
    3. WebSocket Solver: Network-based problem solving
    4. Collaborative Research: Multi-agent coordination
"""

__all__ = []

# Example usage documentation
USAGE = """
DXA (Domain-Expert Agent) Examples
================================

Available examples:

1. Math Tutor (math_tutor.py):
   - Interactive console-based math problem solver
   - Uses Chain of Thought reasoning
   - Interactive agent implementation
   - Environment variables: OPENAI_API_KEY

2. Web Scraper (web_scraper.py):
   - Work automation agent for web scraping
   - Step-by-step workflow execution
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

Example Usage:
    ```python
    from examples import create_math_tutor, run_collaborative_research

    # Create a math tutor agent
    tutor = create_math_tutor()

    # Run collaborative research example
    # Requires OPENAI_API_KEY and WEBSOCKET_URL
    await run_collaborative_research()
    ```
"""
