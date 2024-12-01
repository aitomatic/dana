import pytest
from dxa.experts.math import MathExpert  # Assuming MathExpert is a class in math.py

def test_math_expert_initialization():
    expert = MathExpert()
    assert expert is not None
    assert expert.name == "Math Expert"  # Example attribute check

def test_math_expert_functionality():
    expert = MathExpert()
    result = expert.solve_equation("x^2 - 4 = 0")
    assert result == [2, -2]  # Example expected result 