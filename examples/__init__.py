"""Example implementations of DXA agents."""

from examples.math_solver import main as run_math_solver

__all__ = ['run_math_solver']

# Example usage documentation
USAGE = """
DXA (Domain-Expert Agent) Examples
================================

Available examples:
1. Math Solver (math_solver.py):
   - Interactive console-based math problem solver
   - Uses Chain of Thought reasoning
   - Uses math expert resource
   - Environment variables: OPENAI_API_KEY

Running Examples:
1. From project root:
   python examples/math_solver.py

2. After installing DXA:
   pip install -e .
   python examples/math_solver.py
""" 