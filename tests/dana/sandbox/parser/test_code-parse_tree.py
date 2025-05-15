#
# Copyright © 2025 Aitomatic, Inc.
#
# This source code is licensed under the license found in the LICENSE file in the root directory of this source tree
#
import pytest
from lark import Tree

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


@pytest.fixture(scope="module")
def dana_parser():
    return DanaParser()


def find_first(tree, data_name):
    """Recursively find the first subtree with the given data name."""
    if isinstance(tree, Tree):
        if tree.data == data_name:
            return tree
        for child in tree.children:
            result = find_first(child, data_name)
            if result:
                return result
    return None


def find_value_in_tree(tree, value):
    # Recursively search for a string value in the tree
    if isinstance(tree, str) and tree == value:
        return True
    if isinstance(tree, Tree):
        for child in tree.children:
            if find_value_in_tree(child, value):
                return True
    return False


# 1. Assignment and targets


def test_assignment(dana_parser):
    tree = dana_parser.parse("x = 42\n", do_transform=False)
    assignment = find_first(tree, "assignment")
    assert assignment is not None
    target = assignment.children[0]
    assert target.data == "target"
    atom = target.children[0]
    assert atom.data == "atom"
    inner = atom.children[0]
    assert inner.data in ("variable", "scoped_var", "simple_name", "dotted_access")


def test_assignment_indexing(dana_parser):
    tree = dana_parser.parse("arr[0] = 5\n", do_transform=False)
    assignment = find_first(tree, "assignment")
    assert assignment is not None
    target = assignment.children[0]
    assert target.data == "target"
    atom = target.children[0]
    assert atom.data == "atom"
    # The first child of atom should be variable, and the next child should be a trailer (indexing)
    assert atom.children[0].data == "variable"
    assert atom.children[1].data == "trailer"


def test_assignment_targets(dana_parser):
    # Simple assignment
    tree = dana_parser.parse("x = 1\n", do_transform=False)
    assignment = find_first(tree, "assignment")
    assert assignment is not None
    target = assignment.children[0]
    assert target.data == "target"
    atom = target.children[0]
    assert atom.data == "atom"
    inner = atom.children[0]
    assert inner.data in ("variable", "scoped_var", "simple_name", "dotted_access")
    # Scoped assignment
    tree2 = dana_parser.parse("private:x = 2\n", do_transform=False)
    assignment2 = find_first(tree2, "assignment")
    assert assignment2 is not None
    target2 = assignment2.children[0]
    assert target2.data == "target"
    atom2 = target2.children[0]
    assert atom2.data == "atom"
    inner2 = atom2.children[0]
    assert inner2.data == "variable"
    scoped_var_node = inner2.children[0]
    assert scoped_var_node.data == "scoped_var"
    # Check the structure of the scoped_var node
    scope_node = scoped_var_node.children[0]
    assert isinstance(scope_node, Tree)
    assert scope_node.data == "scope_prefix"
    # Ideally, scope_node.children should not be empty and should contain a Token with value 'private'
    assert len(scope_node.children) > 0, "scope_prefix node should have children representing the scope keyword"
    assert getattr(scope_node.children[0], "type", None) in {"PRIVATE", "PUBLIC", "LOCAL", "SYSTEM"}
    assert scope_node.children[0].value == "private"
    # Dotted access assignment
    tree3 = dana_parser.parse("foo.bar.baz = 3\n", do_transform=False)
    assignment3 = find_first(tree3, "assignment")
    assert assignment3 is not None
    target3 = assignment3.children[0]
    assert target3.data == "target"
    atom3 = target3.children[0]
    assert atom3.data == "atom"
    inner3 = atom3.children[0]
    assert inner3.data == "variable"
    dotted_access_node = inner3.children[0]
    assert dotted_access_node.data == "dotted_access"
    # Indexing assignment
    tree4 = dana_parser.parse("arr[0] = 4\n", do_transform=False)
    assignment4 = find_first(tree4, "assignment")
    assert assignment4 is not None
    target4 = assignment4.children[0]
    assert target4.data == "target"
    atom4 = target4.children[0]
    assert atom4.data == "atom"
    # The first child of atom should be variable, and the next child should be a trailer (indexing)
    assert atom4.children[0].data == "variable"
    assert atom4.children[1].data == "trailer"


# 2. Literals and strings


def test_string_and_literals(dana_parser):
    tree = dana_parser.parse('s = "hello"\n', do_transform=False)
    assignment = find_first(tree, "assignment")
    assert assignment is not None
    expr = assignment.children[1]
    atom = find_first(expr, "atom")
    assert atom is not None
    string_node = find_first(atom, "any_string")
    assert string_node is not None
    assert any(child.type == "REGULAR_STRING" for child in string_node.children if hasattr(child, "type"))

    tree2 = dana_parser.parse('s = r"rawstring"\n', do_transform=False)
    assignment2 = find_first(tree2, "assignment")
    assert assignment2 is not None
    expr2 = assignment2.children[1]
    atom2 = find_first(expr2, "atom")
    assert atom2 is not None
    string_node2 = find_first(atom2, "any_string")
    assert string_node2 is not None
    raw_string_node = find_first(string_node2, "raw_string")
    assert raw_string_node is not None
    assert any(child.type == "REGULAR_STRING" for child in raw_string_node.children if hasattr(child, "type"))

    tree3 = dana_parser.parse('s = """multi\nline\nstring"""\n', do_transform=False)
    assignment3 = find_first(tree3, "assignment")
    assert assignment3 is not None
    expr3 = assignment3.children[1]
    atom3 = find_first(expr3, "atom")
    assert atom3 is not None
    multiline_string = find_first(atom3, "multiline_string")
    assert multiline_string is not None

    tree4 = dana_parser.parse("a = True\nb = False\nc = None\n", do_transform=False)
    assignments = [sub for sub in tree4.iter_subtrees() if sub.data == "assignment"]
    assert len(assignments) == 3
    expected_types = ["TRUE", "FALSE", "NONE"]
    for i in range(3):
        expr = assignments[i].children[1]
        atom = find_first(expr, "atom")
        assert atom is not None
        assert len(atom.children) == 1
        assert getattr(atom.children[0], "type", None) == expected_types[i]

    tree5 = dana_parser.parse('s = f"Hello, {name}!"\n', do_transform=False)
    assignment5 = find_first(tree5, "assignment")
    assert assignment5 is not None
    expr5 = assignment5.children[1]
    atom5 = find_first(expr5, "atom")
    assert atom5 is not None
    string_node5 = find_first(atom5, "any_string")
    assert string_node5 is not None
    fstring_node = find_first(string_node5, "f_string")
    assert fstring_node is not None
    assert any(child.type == "REGULAR_STRING" for child in fstring_node.children if hasattr(child, "type"))


def test_fstring_assignment(dana_parser):
    tree = dana_parser.parse('s = f"Hello, {name}!"\n', do_transform=False)
    assignment = find_first(tree, "assignment")
    assert assignment is not None
    expr = assignment.children[1]
    atom = find_first(expr, "atom")
    assert atom is not None
    string_node = find_first(atom, "f_string")
    assert string_node is not None
    fstring_found = any(
        (hasattr(child, "type") and child.type == "REGULAR_STRING" and child.value.startswith('"'))
        or (
            isinstance(child, Tree)
            and child.data == "string"
            and any(
                getattr(grandchild, "type", None) == "REGULAR_STRING" and getattr(grandchild, "value", "").startswith('"')
                for grandchild in child.children
            )
        )
        for child in string_node.children
    )
    assert fstring_found


def test_fstring_only_text_and_only_expr(dana_parser):
    tree = dana_parser.parse('s = f"hello"\ns = f"{x}"', do_transform=False)
    assert find_first(tree, "f_string") is not None


def test_bool_and_none_variants(dana_parser):
    # All variants for TRUE
    for variant in ["True", "true", "TRUE"]:
        tree = dana_parser.parse(f"a = {variant}\n", do_transform=False)
        assignment = find_first(tree, "assignment")
        assert assignment is not None
        expr = assignment.children[1]
        atom = find_first(expr, "atom")
        assert atom is not None
        assert len(atom.children) == 1
        assert getattr(atom.children[0], "type", None) == "TRUE"
    # All variants for FALSE
    for variant in ["False", "false", "FALSE"]:
        tree = dana_parser.parse(f"a = {variant}\n", do_transform=False)
        assignment = find_first(tree, "assignment")
        assert assignment is not None
        expr = assignment.children[1]
        atom = find_first(expr, "atom")
        assert atom is not None
        assert len(atom.children) == 1
        assert getattr(atom.children[0], "type", None) == "FALSE"
    # All variants for NONE
    for variant in ["None", "none", "NONE", "null", "NULL"]:
        tree = dana_parser.parse(f"a = {variant}\n", do_transform=False)
        assignment = find_first(tree, "assignment")
        assert assignment is not None
        expr = assignment.children[1]
        atom = find_first(expr, "atom")
        assert atom is not None
        assert len(atom.children) == 1
        assert getattr(atom.children[0], "type", None) == "NONE"


# 3. Collections


def test_list_and_dict(dana_parser):
    tree = dana_parser.parse('l = [1, 2]\nd = {"a": 1, "b": 2}\n', do_transform=False)
    assert find_first(tree, "list") is not None
    assert find_first(tree, "dict") is not None


def test_tuple(dana_parser):
    tree = dana_parser.parse("t = (1, 2)\nempty = ()\n", do_transform=False)
    assert find_first(tree, "tuple") is not None


def test_empty_collections(dana_parser):
    tree = dana_parser.parse("a = []\nb = {}\nc = ()", do_transform=False)
    assert find_first(tree, "list") is not None
    assert find_first(tree, "dict") is not None
    assert find_first(tree, "tuple") is not None


def test_single_item_collections(dana_parser):
    tree = dana_parser.parse('a = [1]\nb = {"a": 1}\nc = (1,)', do_transform=False)
    assert find_first(tree, "list") is not None
    assert find_first(tree, "dict") is not None
    assert find_first(tree, "tuple") is not None


# 4. Expressions


def test_arithmetic(dana_parser):
    tree = dana_parser.parse("x = 1 + 2 * 3\n", do_transform=False)
    assignment = find_first(tree, "assignment")
    assert assignment is not None
    assert find_first(assignment, "sum_expr") is not None
    assert find_first(assignment, "term") is not None


def test_operator_precedence(dana_parser):
    tree = dana_parser.parse("x = 1 + 2 * 3 > 4 and 5 < 6 or not 7\n", do_transform=False)
    assert find_first(tree, "or_expr") is not None
    assert find_first(tree, "and_expr") is not None
    assert find_first(tree, "not_expr") is not None
    assert find_first(tree, "comparison") is not None
    assert find_first(tree, "sum_expr") is not None
    assert find_first(tree, "term") is not None
    assert find_first(tree, "factor") is not None


def test_chained_comparisons_and_logicals(dana_parser):
    tree = dana_parser.parse("a < b < c", do_transform=False)
    assert find_first(tree, "comparison") is not None
    tree2 = dana_parser.parse("a and b and c", do_transform=False)
    assert find_first(tree2, "and_expr") is not None


# 5. Control flow


def test_if_while_for_function(dana_parser):
    code = """if x > 0:\n    y = 1\nelse:\n    y = -1\nwhile x < 10:\n    x = x + 1\nfor i in [1,2]:\n    y = i\ndef foo(a, b):\n    return a + b\n"""
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "if_stmt") is not None
    assert find_first(tree, "while_stmt") is not None
    assert find_first(tree, "for_stmt") is not None
    assert find_first(tree, "function_def") is not None


def test_if_elif_else(dana_parser):
    code1 = "if x > 0:\n    y = 1\n"
    tree1 = dana_parser.parse(code1, do_transform=False)
    assert find_first(tree1, "if_stmt") is not None
    code2 = "if x > 0:\n    y = 1\nelse:\n    y = -1\n"
    tree2 = dana_parser.parse(code2, do_transform=False)
    assert find_first(tree2, "if_stmt") is not None
    code3 = "if x > 0:\n    y = 1\nelif x < 0:\n    y = -1\n"
    tree3 = dana_parser.parse(code3, do_transform=False)
    assert find_first(tree3, "if_stmt") is not None
    assert find_first(tree3, "elif_stmt") is not None
    code4 = "if x > 0:\n    y = 1\nelif x < 0:\n    y = -1\nelse:\n    y = 0\n"
    tree4 = dana_parser.parse(code4, do_transform=False)
    assert find_first(tree4, "if_stmt") is not None
    assert find_first(tree4, "elif_stmt") is not None


def test_minimal_if_block(dana_parser):
    tree = dana_parser.parse("if x:\n    pass", do_transform=False)
    assert find_first(tree, "if_stmt") is not None
    assert find_first(tree, "pass_stmt") is not None


def test_minimal_function_and_try(dana_parser):
    tree = dana_parser.parse("def f():\n    pass", do_transform=False)
    assert find_first(tree, "function_def") is not None
    tree2 = dana_parser.parse("try:\n    pass\nexcept:\n    pass", do_transform=False)
    assert find_first(tree2, "try_stmt") is not None
    assert find_first(tree2, "pass_stmt") is not None


def test_block_with_extra_blank_lines(dana_parser):
    code = """if x > 0:\n\n    y = 1\n\nelse:\n\n    y = -1\n"""
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "if_stmt") is not None


def test_missing_trailing_newline(dana_parser):
    code = "if x > 0:\n    y = 1"
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "if_stmt") is not None


def test_nested_blocks_and_complex_program(dana_parser):
    code = """def outer():\n    def inner():\n        if x:\n            try:\n                risky()\n            except:\n                pass\n    return inner\n"""
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "function_def") is not None
    assert find_first(tree, "if_stmt") is not None
    assert find_first(tree, "try_stmt") is not None
    assert find_first(tree, "pass_stmt") is not None


# 6. Functions and calls


def test_function_call_and_expr_stmt(dana_parser):
    code = "def foo(x):\n    return x\nfoo(42)\n"
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "function_def") is not None
    assert find_first(tree, "expr_stmt") is not None


def test_nested_function_calls_and_attrs(dana_parser):
    tree = dana_parser.parse("foo(bar(1), baz(2))", do_transform=False)
    assert find_first(tree, "trailer") is not None
    tree2 = dana_parser.parse("a.b.c.d", do_transform=False)
    assert find_first(tree2, "dotted_access") is not None


# 7. Import and scope


def test_import_statements(dana_parser):
    tree = dana_parser.parse("import foo.bar\n", do_transform=False)
    import_stmt = find_first(tree, "import_stmt")
    assert import_stmt is not None
    module_path = find_first(import_stmt, "module_path")
    assert module_path is not None
    tree2 = dana_parser.parse("from foo.bar import baz\n", do_transform=False)
    import_stmt2 = find_first(tree2, "import_stmt")
    assert import_stmt2 is not None
    module_path2 = find_first(import_stmt2, "module_path")
    assert module_path2 is not None


def test_scope_and_indexing(dana_parser):
    code = "private:x = 1\nlocal:y = arr[0]\n"
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "scoped_var") is not None
    trailer = find_first(tree, "trailer")
    assert trailer is not None
    assert any(child.data == "expr" for child in trailer.children if isinstance(child, Tree))


# 8. Try/except/finally


def test_try_except(dana_parser):
    code = """try:\n    risky()\nexcept:\n    handle()\n"""
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "try_stmt") is not None


def test_try_except_finally(dana_parser):
    code1 = "try:\n    risky()\nexcept:\n    handle()\n"
    tree1 = dana_parser.parse(code1, do_transform=False)
    assert find_first(tree1, "try_stmt") is not None
    code2 = "try:\n    risky()\nexcept:\n    handle()\nfinally:\n    cleanup()\n"
    tree2 = dana_parser.parse(code2, do_transform=False)
    assert find_first(tree2, "try_stmt") is not None


# 9. Pass, return, break, continue


def test_pass_import_return_break_continue(dana_parser):
    code = "pass\nimport math\nreturn\nbreak\ncontinue\n"
    tree = dana_parser.parse(code, do_transform=False)
    assert find_first(tree, "pass_stmt") is not None
    assert find_first(tree, "import_stmt") is not None
    assert find_first(tree, "return_stmt") is not None
    assert find_first(tree, "break_stmt") is not None
    assert find_first(tree, "continue_stmt") is not None


# 10. Property access and trailer


def test_property_access_and_trailer(dana_parser):
    tree = dana_parser.parse("foo.bar.baz = 1\n", do_transform=False)
    dotted = find_first(tree, "dotted_access")
    assert dotted is not None
    tree2 = dana_parser.parse("foo.bar.baz()\n", do_transform=False)
    trailer = find_first(tree2, "trailer")
    assert trailer is not None
    tree3 = dana_parser.parse("foo.bar.baz.qux(42)\n", do_transform=False)
    dotted3 = find_first(tree3, "dotted_access")
    assert dotted3 is not None or find_first(tree3, "trailer") is not None


# 11. Miscellaneous


def test_bare_identifier_and_expr_stmt(dana_parser):
    tree = dana_parser.parse("foo\n", do_transform=False)
    assert find_first(tree, "expr_stmt") is not None


def test_multiple_statements_with_blanks(dana_parser):
    tree = dana_parser.parse("x = 1\n\ny = 2\n", do_transform=False)
    assert find_first(tree, "assignment") is not None


# def test_program_with_only_comments_and_whitespace(dana_parser):
#     tree = dana_parser.parse('# just a comment\n\n   \n')
#     # Should parse to an empty program or similar
#     assert tree is not None

# 12. Negative/boundary/error cases


def test_incomplete_assignment_raises(dana_parser):
    with pytest.raises(Exception):  # noqa: B017
        dana_parser.parse("x =", do_transform=False)


def test_unmatched_parentheses_raises(dana_parser):
    with pytest.raises(Exception):  # noqa: B017
        dana_parser.parse("x = (1 + 2", do_transform=False)


def test_invalid_keyword_raises(dana_parser):
    with pytest.raises(Exception):  # noqa: B017
        dana_parser.parse("frobnicate x", do_transform=False)
