"""Custom exceptions for the DANA module."""

class DANAError(Exception):
    """Base class for exceptions in the DANA module."""
    pass

class LanguageError(DANAError):
    """Base class for errors related to program language (parsing, validation)."""
    pass

class ProgramParsingError(LanguageError):
    """Raised when a program string cannot be parsed into an AST."""
    pass

class ProgramValidationError(LanguageError):
    """Raised when a parsed program AST fails validation checks."""
    pass

class DANARuntimeError(DANAError):
    """Base class for errors occurring during program execution."""
    pass

class ProgramExecutionError(DANARuntimeError):
    """Raised for general errors during program execution by the interpreter."""
    pass

class ResourceNotFoundError(DANARuntimeError, KeyError):
    """Raised when a required resource (tool, LLM) is not found in the context."""
    pass

class InvalidStateKeyError(DANARuntimeError, ValueError):
    """Raised when an invalid key is used for context state access (format or scope)."""
    pass

class SandboxViolationError(DANARuntimeError):
    """Raised if an operation violates configured sandbox constraints."""
    pass

class TranscoderError(DANAError):
    """Base class for errors during NL <-> Program conversion."""
    pass

class CompilationError(TranscoderError):
    """Raised when the compiler (GMA) fails to generate a valid program."""
    pass

class NarrationError(TranscoderError):
    """Raised when the narrator fails to explain a program."""
    pass

# Base exceptions for DANA

class DanaError(Exception):
    """Base class for all DANA-related errors."""
    pass

class ParseError(DanaError):
    """Error during DANA program parsing."""
    pass

class StateError(DanaError):
    """Error related to RuntimeContext state access."""
    pass

class InterpretError(DanaError):
    """Error during DANA program interpretation/execution."""
    pass

class KBError(DanaError):
    """Error related to Knowledge Base access or loading."""
    pass 