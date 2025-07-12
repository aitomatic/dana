"""Tests for basic Dana code execution."""

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.sandbox_context import SandboxContext


def run_dana_code(code: str):
    """Helper function to run Dana code and return the context."""
    # Remove leading/trailing whitespace and normalize line endings
    code = code.strip()
    from dana.core.lang.parser.utils.parsing_utils import ParserCache

    parser = ParserCache.get_parser("dana")
    program = parser.parse(code, do_type_check=True, do_transform=True)
    context = SandboxContext()
    interpreter = DanaInterpreter()
    interpreter.execute_program(program, context)
    return context


def test_basic_variable_assignment():
    """Test basic variable assignment in Dana."""
    code = """
private:x = 42
private:y = "hello"
private:z = True
"""
    ctx = run_dana_code(code)
    assert ctx.get("private:x") == 42
    assert ctx.get("private:y") == "hello"
    assert ctx.get("private:z") is True


def test_basic_arithmetic():
    """Test basic arithmetic operations in Dana."""
    code = """
private:a = 10
private:b = 5
private:sum = private:a + private:b
private:diff = private:a - private:b
private:prod = private:a * private:b
private:div = private:a / private:b
"""
    ctx = run_dana_code(code)
    assert ctx.get("private:sum") == 15
    assert ctx.get("private:diff") == 5
    assert ctx.get("private:prod") == 50
    assert ctx.get("private:div") == 2


def test_basic_string_operations():
    """Test basic string operations in Dana."""
    code = """
private:str1 = "Hello"
private:str2 = "World"
private:concat = private:str1 + " " + private:str2
"""
    ctx = run_dana_code(code)
    assert ctx.get("private:concat") == "Hello World"


def test_basic_boolean_operations():
    """Test basic boolean operations in Dana."""
    code = """
private:x = True
private:y = False
private:result1 = private:x and private:y
private:result2 = private:x or private:y
private:result3 = not private:x
"""
    ctx = run_dana_code(code)
    assert ctx.get("private:result1") is False
    assert ctx.get("private:result2") is True
    assert ctx.get("private:result3") is False


def test_function_definition_and_call():
    """Test function definition and calling."""
    code = """
def add(a, b):
    return a + b

private:result = add(2, 3)
"""
    ctx = run_dana_code(code)
    assert ctx.get("private:result") == 5
