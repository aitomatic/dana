"""POET-specific errors"""


class POETError(Exception):
    """Base class for POET errors"""

    pass


class POETTranspilationError(POETError):
    """Error during POET transpilation"""

    pass
