"""Debug script for testing the Lark parser with DANA grammar."""

import sys
from pathlib import Path
from lark import Lark, Transformer, indenter
from lark.indenter import Indenter

# Path to the grammar file
grammar_path = Path("opendxa/dana/language/dana_grammar.lark")

# Read the grammar
with open(grammar_path, "r") as f:
    grammar = f.read()

# Define an indenter for handling Python-style indentation
class DanaIndenter(Indenter):
    NL_type = '_NL'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = 'INDENT'
    DEDENT_type = 'DEDENT'
    tab_len = 8

# Create the parser with the indenter
parser = Lark(grammar, parser='lalr', start='start', postlex=DanaIndenter())

# Test code samples
basic_test_cases = [
    # Basic tests
    "x = 42",
    "user.name = \"Alice\"",
    "user.name = 'Alice'",
]

conditional_test_cases = [
    # Conditionals
    """if x > 10:
    log(x)
""",
    
    """if x > 10:
    log(x)
else:
    log("too small")
""",
]

# Run the basic tests
print("\n=== Basic Tests ===")
for i, code in enumerate(basic_test_cases):
    print(f"\n--- Test case {i+1} ---")
    print(f"Code: {code}")
    try:
        tree = parser.parse(code)
        print("Success!")
        print(f"Parse tree: {tree.pretty()}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

# Run the conditional tests
print("\n=== Conditional Tests ===")
for i, code in enumerate(conditional_test_cases):
    print(f"\n--- Test case {i+1} ---")
    print(f"Code: {code}")
    try:
        tree = parser.parse(code)
        print("Success!")
        print(f"Parse tree: {tree.pretty()}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

# Test specific cases from our test suite
print("\n=== Test Suite Cases ===")

test_suite_cases = [
    ("test_nested_assignment", "user.name = 'Alice'"),
    ("test_conditional", "if x > 10:\n    log(x)\n    y = x * 2"),
    ("test_else_clause", """
if result > 100:
    log.warn("Large factorial")
else:
    log.info("Small factorial")
"""),
]

for name, code in test_suite_cases:
    print(f"\n--- {name} ---")
    print(f"Code: {code}")
    try:
        tree = parser.parse(code)
        print("Success!")
        print(f"Parse tree: {tree.pretty()}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
