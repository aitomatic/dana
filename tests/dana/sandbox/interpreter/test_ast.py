def test_division_from_source():
    from opendxa.dana.sandbox.interpreter.interpreter import Interpreter
    from opendxa.dana.sandbox.parser.dana_parser import DanaParser
    from opendxa.dana.sandbox.sandbox_context import SandboxContext

    parser = DanaParser()
    parse_tree = parser.parser.parse("private:x = 6 / 2\n")
    ast = parser.transform(parse_tree)
    interpreter = Interpreter(SandboxContext())
    result = interpreter.execute_program(ast, suppress_exceptions=False)
    assert interpreter.context.get("private.x") == 3.0


def test_parse_simple_division_expression():
    from opendxa.dana.sandbox.parser.dana_parser import DanaParser

    parser = DanaParser()
    parse_tree = parser.parser.parse("6 / 2\n")
