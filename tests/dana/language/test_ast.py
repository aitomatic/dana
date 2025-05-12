import unittest
from typing import List, Union

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    ExceptBlock,
    ForLoop,
    FunctionCall,
    FunctionDefinition,
    Identifier,
    ImportFromStatement,
    ImportStatement,
    LiteralExpression,
    Location,
    Statement,
    TryBlock,
    WhileLoop,
)


class TestAST(unittest.TestCase):
    """Test cases for the DANA AST."""

    def test_literal_expression(self):
        """Test LiteralExpression instantiation and behavior."""
        literal = LiteralExpression(42)
        self.assertEqual(literal.value, 42)
        self.assertEqual(literal.type, "int")

    def test_identifier(self):
        """Test Identifier instantiation and behavior."""
        identifier = Identifier("x")
        self.assertEqual(identifier.name, "x")

    def test_function_call(self):
        """Test FunctionCall instantiation and behavior."""
        args = {"arg1": LiteralExpression(1), "arg2": LiteralExpression(2)}
        func_call = FunctionCall("my_function", args)
        self.assertEqual(func_call.name, "my_function")
        self.assertEqual(func_call.args, args)

    def test_binary_expression(self):
        """Test BinaryExpression instantiation and behavior."""
        left = LiteralExpression(1)
        right = LiteralExpression(2)
        binary_expr = BinaryExpression(left, BinaryOperator.ADD, right)
        self.assertEqual(binary_expr.left, left)
        self.assertEqual(binary_expr.operator, BinaryOperator.ADD)
        self.assertEqual(binary_expr.right, right)

    def test_assignment(self):
        """Test Assignment instantiation and behavior."""
        target = Identifier("x")
        value = LiteralExpression(42)
        assignment = Assignment(target, value)
        self.assertEqual(assignment.target, target)
        self.assertEqual(assignment.value, value)

    def test_conditional(self):
        """Test Conditional instantiation and behavior."""
        condition = LiteralExpression(True)
        body: List[Union[Assignment, Conditional, WhileLoop, FunctionCall]] = [Assignment(Identifier("x"), LiteralExpression(1))]
        else_body: List[Union[Assignment, Conditional, WhileLoop, FunctionCall]] = [Assignment(Identifier("x"), LiteralExpression(0))]
        location = Location(line=1, column=1, source="test_file")
        conditional = Conditional(condition=condition, body=body, else_body=else_body, line_num=1, location=location)
        self.assertEqual(conditional.condition, condition)
        self.assertEqual(conditional.body, body)
        self.assertEqual(conditional.else_body, else_body)

    def test_while_loop(self):
        """Test WhileLoop instantiation and behavior."""
        condition = LiteralExpression(True)
        body: List[Union[Assignment, Conditional, WhileLoop, FunctionCall]] = [Assignment(Identifier("x"), LiteralExpression(1))]
        while_loop = WhileLoop(condition, body, 1, None)
        self.assertEqual(while_loop.condition, condition)
        self.assertEqual(while_loop.body, body)

    def test_for_loop(self):
        """Test ForLoop instantiation and behavior."""
        target = Identifier("i")
        iterable = LiteralExpression([1, 2, 3])
        body: List[Statement] = [Assignment(Identifier("x"), LiteralExpression(1))]
        for_loop = ForLoop(target, iterable, body)
        self.assertEqual(for_loop.target, target)
        self.assertEqual(for_loop.iterable, iterable)
        self.assertEqual(for_loop.body, body)

    def test_try_block(self):
        """Test TryBlock instantiation and behavior."""
        body: List[Statement] = [Assignment(Identifier("x"), LiteralExpression(1))]
        except_blocks = [ExceptBlock(body=[Assignment(Identifier("x"), LiteralExpression(0))])]
        try_block = TryBlock(body, except_blocks)
        self.assertEqual(try_block.body, body)
        self.assertEqual(try_block.except_blocks, except_blocks)

    def test_function_definition(self):
        """Test FunctionDefinition instantiation and behavior."""
        name = Identifier("my_function")
        parameters = [Identifier("x"), Identifier("y")]
        body: List[Statement] = [Assignment(Identifier("x"), LiteralExpression(1))]
        func_def = FunctionDefinition(name, parameters, body)
        self.assertEqual(func_def.name, name)
        self.assertEqual(func_def.parameters, parameters)
        self.assertEqual(func_def.body, body)

    def test_import_statement(self):
        """Test ImportStatement instantiation and behavior."""
        import_stmt = ImportStatement("math")
        self.assertEqual(import_stmt.module, "math")

    def test_import_from_statement(self):
        """Test ImportFromStatement instantiation and behavior."""
        names = [("sqrt", None), ("pi", "p")]
        import_from_stmt = ImportFromStatement("math", names)
        self.assertEqual(import_from_stmt.module, "math")
        self.assertEqual(import_from_stmt.names, names)


if __name__ == "__main__":
    unittest.main()
