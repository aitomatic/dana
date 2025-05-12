"""DANA: Domain-Aware Neurosymbolic Architecture"""

from opendxa.dana.common.exceptions import (
    DanaError,
    ErrorContext,
    ErrorHandler,
    InterpretError,
    ParseError,
    SandboxError,
    StateError,
    ValidationError,
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
    Program,
)
from opendxa.dana.repl import REPL, dana_repl_app
from opendxa.dana.sandbox import ExecutionStatus, Interpreter, ResourceRegistry, SandboxContext
from opendxa.dana.transcoder import CompilerInterface, NarratorInterface, Transcoder

__all__ = [
    # Error Handling
    "DanaError",
    "ErrorContext",
    "ErrorHandler",
    "ParseError",
    "InterpretError",
    "SandboxError",
    "StateError",
    "ValidationError",
    # Runtime
    "SandboxContext",
    "ExecutionStatus",
    "Interpreter",
    "ResourceRegistry",
    # Language
    "Program",
    "Expression",
    "Assignment",
    "Conditional",
    "LiteralExpression",
    "Identifier",
    "BinaryExpression",
    "FunctionCall",
    "BinaryOperator",
    # REPL
    "REPL",
    "dana_repl_app",
    # Transcoder
    "CompilerInterface",
    "NarratorInterface",
    "Transcoder",
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
