"""Visitor pattern implementation for DANA AST nodes.

This module defines the Visitor interface and concrete visitors for the DANA
language AST. The visitor pattern allows operations to be defined on the AST
without modifying the node classes themselves.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    Conditional,
    FStringExpression,
    FunctionCall,
    Identifier,
    Literal,
    LiteralExpression,
    LogLevelSetStatement,
    LogStatement,
    Program,
)


class ASTVisitor(ABC):
    """Abstract base class for AST visitors.
    
    This class defines the interface for visitors that traverse and operate on
    DANA AST nodes. Concrete visitor implementations should inherit from this
    class and implement the visit methods for each node type they want to handle.
    
    Node types that don't have a specific visit method will use the generic
    visit_node method.
    """

    @abstractmethod
    def visit_program(self, node: Program, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a Program node."""
        pass

    @abstractmethod
    def visit_assignment(self, node: Assignment, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit an Assignment node."""
        pass

    @abstractmethod
    def visit_log_statement(self, node: LogStatement, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a LogStatement node."""
        pass

    @abstractmethod
    def visit_log_level_set_statement(self, node: LogLevelSetStatement, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a LogLevelSetStatement node."""
        pass

    @abstractmethod
    def visit_conditional(self, node: Conditional, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a Conditional node."""
        pass

    @abstractmethod
    def visit_binary_expression(self, node: BinaryExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a BinaryExpression node."""
        pass

    @abstractmethod
    def visit_literal_expression(self, node: LiteralExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a LiteralExpression node."""
        pass

    @abstractmethod
    def visit_identifier(self, node: Identifier, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit an Identifier node."""
        pass

    @abstractmethod
    def visit_function_call(self, node: FunctionCall, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a FunctionCall node."""
        pass

    @abstractmethod
    def visit_literal(self, node: Literal, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit a Literal node."""
        pass

    @abstractmethod
    def visit_fstring_expression(self, node: FStringExpression, context: Optional[Dict[str, Any]] = None) -> Any:
        """Visit an FStringExpression node."""
        pass

    @abstractmethod
    def visit_node(self, node: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Generic visit method for any node type.
        
        This method is called when no specific visit method exists for a node type.
        """
        pass


class NodeVisitorMixin:
    """Mixin that provides the accept method for AST nodes.

    This mixin can be added to AST node classes to make them visitable.
    However, we're adding this pattern without modifying the existing AST classes
    to maintain backward compatibility.
    """

    def accept(self, visitor: ASTVisitor, context: Optional[Dict[str, Any]] = None) -> Any:
        """Accept a visitor and dispatch to the appropriate visit method."""
        if isinstance(self, Program):
            return visitor.visit_program(self, context)
        elif isinstance(self, Assignment):
            return visitor.visit_assignment(self, context)
        elif isinstance(self, LogStatement):
            return visitor.visit_log_statement(self, context)
        elif isinstance(self, LogLevelSetStatement):
            return visitor.visit_log_level_set_statement(self, context)
        elif isinstance(self, Conditional):
            return visitor.visit_conditional(self, context)
        elif isinstance(self, BinaryExpression):
            return visitor.visit_binary_expression(self, context)
        elif isinstance(self, LiteralExpression):
            return visitor.visit_literal_expression(self, context)
        elif isinstance(self, Identifier):
            return visitor.visit_identifier(self, context)
        elif isinstance(self, FunctionCall):
            return visitor.visit_function_call(self, context)
        elif isinstance(self, Literal):
            return visitor.visit_literal(self, context)
        elif isinstance(self, FStringExpression):
            return visitor.visit_fstring_expression(self, context)
        else:
            return visitor.visit_node(self, context)


def accept(node: Any, visitor: ASTVisitor, context: Optional[Dict[str, Any]] = None) -> Any:
    """Function to make AST nodes accept a visitor without modifying the node classes.
    
    This function allows the visitor pattern to be used without changing the
    original AST node classes, maintaining backward compatibility.
    
    Args:
        node: The AST node to visit
        visitor: The visitor to apply to the node
        context: Optional context to pass to the visitor
        
    Returns:
        The result of applying the visitor to the node
    """
    if isinstance(node, Program):
        return visitor.visit_program(node, context)
    elif isinstance(node, Assignment):
        return visitor.visit_assignment(node, context)
    elif isinstance(node, LogStatement):
        return visitor.visit_log_statement(node, context)
    elif isinstance(node, LogLevelSetStatement):
        return visitor.visit_log_level_set_statement(node, context)
    elif isinstance(node, Conditional):
        return visitor.visit_conditional(node, context)
    elif isinstance(node, BinaryExpression):
        return visitor.visit_binary_expression(node, context)
    elif isinstance(node, LiteralExpression):
        return visitor.visit_literal_expression(node, context)
    elif isinstance(node, Identifier):
        return visitor.visit_identifier(node, context)
    elif isinstance(node, FunctionCall):
        return visitor.visit_function_call(node, context)
    elif isinstance(node, Literal):
        return visitor.visit_literal(node, context)
    elif isinstance(node, FStringExpression):
        return visitor.visit_fstring_expression(node, context)
    else:
        return visitor.visit_node(node, context)