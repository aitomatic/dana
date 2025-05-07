"""Modular execution components for the DANA interpreter.

This package contains the specialized components for executing DANA programs:
- Expression evaluation
- Statement execution
- Context management
- LLM integration
- Error handling
"""

from opendxa.dana.runtime.executor.base_executor import BaseExecutor
from opendxa.dana.runtime.executor.context_manager import ContextManager
from opendxa.dana.runtime.executor.expression_evaluator import ExpressionEvaluator
from opendxa.dana.runtime.executor.statement_executor import StatementExecutor
from opendxa.dana.runtime.executor.llm_integration import LLMIntegration