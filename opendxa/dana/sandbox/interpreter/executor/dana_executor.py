"""
DanaExecutor: Central dispatcher for DANA AST execution.

This class mirrors the role of DanaTransformer on the parser side, providing a single entry point for executing AST nodes. It delegates to specialized executors (statements, expressions, etc.) and is easily extensible for future features.
"""

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.executor.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.sandbox.interpreter.executor.llm_integration import LLMIntegration
from opendxa.dana.sandbox.interpreter.executor.statement_executor import StatementExecutor
from opendxa.dana.sandbox.parser.ast import Expression, Statement
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class DanaExecutor:
    """
    Central dispatcher for DANA AST execution.

    Usage:
        executor = DanaExecutor(context)
        result = executor.execute(node)  # node can be any AST node
    """

    def __init__(self, context: SandboxContext):
        self.context = context
        self.context_manager = ContextManager(self.context)
        self.expression_evaluator = ExpressionEvaluator(self.context_manager)
        self.llm_integration = LLMIntegration(self.context_manager)
        self.statement_executor = StatementExecutor(self.context_manager, self.expression_evaluator, self.llm_integration)
        # Add more specialized executors here as needed

    def execute(self, node, *args, **kwargs):
        """
        Dispatch execution to the appropriate executor based on node type.
        """
        # Statement nodes
        if isinstance(node, Statement):
            method = getattr(self.statement_executor, f"execute_{type(node).__name__.lower()}", None)
            if method:
                return method(node, *args, **kwargs)
            # Fallback to generic statement executor
            return self.statement_executor.execute(node, *args, **kwargs)
        # Expression nodes
        elif isinstance(node, Expression):
            method = getattr(self.expression_evaluator, f"evaluate_{type(node).__name__.lower()}", None)
            if method:
                return method(node, *args, **kwargs)
            # Fallback to generic expression evaluator
            return self.expression_evaluator.evaluate(node, *args, **kwargs)
        # Add more node type dispatches as needed
        raise SandboxError(f"No executor found for node type: {type(node).__name__}")

    def __getattr__(self, name):
        """
        Delegate attribute access to sub-executors for convenience.
        """
        for executor in [self.statement_executor, self.expression_evaluator]:
            if hasattr(executor, name):
                return getattr(executor, name)
        raise AttributeError(f"'DanaExecutor' has no attribute '{name}'")


# Example usage (in Interpreter):
# context = SandboxContext()
# dana_executor = DanaExecutor(context)
# result = dana_executor.execute(ast_node)
