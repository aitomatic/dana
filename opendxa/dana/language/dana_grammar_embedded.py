"""Embedded DANA grammar definition.

This file contains the DANA language grammar definition in Lark format.
It is used as a fallback if the main grammar file (dana_grammar.lark) is not found.

To update this file after modifying dana_grammar.lark, run:
    python -c "from opendxa.dana.language.parser import GrammarParser; GrammarParser._update_embedded_grammar()"
"""

# type: ignore
GRAMMAR = r"""# type: ignore
// DANA language grammar definition

start: program

program: statement*

statement: assignment
        | conditional
        | while_loop
        | function_call
        | print_statement
        | bare_identifier
        | _NL

assignment: identifier "=" expression

conditional: "if" expression ":" _NL INDENT statement+ DEDENT ["else" ":" _NL INDENT statement+ DEDENT]

while_loop: "while" expression ":" _NL INDENT statement+ DEDENT

function_call: identifier "(" [expression ("," expression)*] ")"

print_statement: "print" "(" expression ")"

bare_identifier: identifier

expression: or_expr

or_expr: and_expr ("or" and_expr)*

and_expr: not_expr ("and" not_expr)*

not_expr: "not" not_expr
        | comparison

comparison: sum_expr (comparison_op sum_expr)*

comparison_op: "==" | "!=" | "<" | ">" | "<=" | ">="

sum_expr: product_expr (sum_op product_expr)*

sum_op: "+" | "-"

product_expr: unary_expr (product_op unary_expr)*

product_op: "*" | "/" | "%"

unary_expr: "-" unary_expr
          | primary

primary: identifier
    | literal
    | "(" expression ")"
    | function_call

identifier: [scope_prefix "."] CNAME

scope_prefix: "private" | "public" | "protected"

literal: string
       | number
       | boolean
       | null

string: STRING

number: NUMBER

boolean: "true" | "false"

null: "null"

%ignore WS
%ignore COMMENT
%declare INDENT DEDENT
"""
