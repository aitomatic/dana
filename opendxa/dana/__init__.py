"""DANA: Domain-Aware Neurosymbolic Architecture"""

from opendxa.dana.exceptions import (
    DanaError,
    InterpretError,
    ParseError,
    RuntimeError,
    StateError,
)
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    Expression,
    FunctionCall,
    Identifier,
    LiteralExpression,
    LogLevel,
    LogStatement,
    Program,
)
from opendxa.dana.runtime import ExecutionStatus, Interpreter, ResourceRegistry, RuntimeContext

__all__ = [
    # Exceptions
    "DanaError",
    "ParseError",
    "InterpretError",
    "RuntimeError",
    "StateError",
    # Runtime
    "RuntimeContext",
    "ExecutionStatus",
    "Interpreter",
    "ResourceRegistry",
    # Language
    "Program",
    "Expression",
    "Assignment",
    "LogStatement",
    "Conditional",
    "LiteralExpression",
    "Identifier",
    "BinaryExpression",
    "FunctionCall",
    "BinaryOperator",
    "LogLevel",
]

# Expose key APIs (Placeholders - to be defined)
# def run(program_source: str, initial_context: dict) -> Any:
#     pass

# def compile(program_source: str) -> Program:
#     pass

# def explain(program_source: str) -> str:
#     pass

# Import core components from submodules for easier access if desired
# from .runtime.interpreter import ProgramInterpreter
# from .runtime.context import RuntimeContext
# from .language.ast import Program
# from .transcoder.compiler import GMAInterface  # Example - adjust based on final transcoder structure

__version__ = "0.1.0"  # Example version
