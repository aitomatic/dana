"""Embedded DANA grammar definition.

This file contains the DANA language grammar definition in Lark format.
It is used as a fallback if the main grammar file (dana_grammar.lark) is not found.

To update this file after modifying dana_grammar.lark, run:
    python -c "from opendxa.dana.language.parser import GrammarParser; GrammarParser._update_embedded_grammar()"
"""

# type: ignore
GRAMMAR = r"""# type: ignore
// DANA language grammar definition

start: statement*

statement: assignment
        | log_statement
        | conditional
        | while_loop
        | reason_statement
        | log_level_set_statement
        | function_call
        | print_statement
        | identifier          // Allow bare identifiers as statements
        | COMMENT
        | _NL              // Skip empty lines

assignment: identifier "=" expression

log_statement: "log" ["." level] "(" expression ["," named_args] ")"
level: DEBUG | INFO | WARN | ERROR
DEBUG: "debug" | "DEBUG"
INFO: "info" | "INFO"
WARN: "warn" | "WARN"
ERROR: "error" | "ERROR"

conditional: if_part [else_part]
if_part: "if" expression ":" _NL INDENT statement+ DEDENT
else_part: "else" ":" _NL INDENT statement+ DEDENT

while_loop: "while" expression ":" _NL INDENT statement+ DEDENT

reason_statement: [identifier "="] "reason" "(" expression ["," named_args] ")"
context_arg: identifier | "[" identifier_list "]"
options: key_value ("," key_value)*
key_value: CNAME "=" (STRING | NUMBER | BOOL)

log_level_set_statement: "log" "." "setLevel" "(" (STRING | level) ")"

print_statement: "print" "(" expression ")"

function_call: identifier "(" [arg_list] ")"
arg_list: (positional_args [","]) | (positional_args "," named_args) | named_args
positional_args: expression ("," expression)*
named_args: named_arg ("," named_arg)*
named_arg: CNAME "=" expression

// Expression grammar with operator precedence
expression: or_expr

or_expr: and_expr ("or" and_expr)*
and_expr: comparison ("and" comparison)*
comparison: sum_expr (comp_op sum_expr)*
comp_op: EQ | NEQ | LT | GT | LTE | GTE
EQ: "=="
NEQ: "!="
LT: "<"
GT: ">"
LTE: "<="
GTE: ">="
sum_expr: product (add_op product)*
add_op: PLUS | MINUS
PLUS: "+"
MINUS: "-"
product: atom (mul_op atom)*
mul_op: MULT | DIV | MOD
MULT: "*"
DIV: "/"
MOD: "%"

atom: identifier
    | literal
    | "(" expression ")"
    | function_call
    | array_literal
    | TRUE
    | FALSE

identifier: CNAME ("." CNAME)*
identifier_list: identifier ("," identifier)*

literal: STRING | NUMBER | BOOL | "null" | f_string

array_literal: "[" [array_items] "]"
array_items: expression ("," expression)*

// Boolean literals
TRUE: "True"
FALSE: "False"

// Improved f-string support to handle interpolation
f_string: "f" F_STRING_VALUE
F_STRING_VALUE: /"[^"]*"/ | /'[^']*'/ | /"""[\s\S]*?"""/ | /'''[\s\S]*?'''/

// Terminals
STRING: DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING | TRIPLE_DOUBLE_QUOTE_STRING | TRIPLE_SINGLE_QUOTE_STRING
DOUBLE_QUOTE_STRING: /"[^"]*"/
SINGLE_QUOTE_STRING: /'[^']*'/
TRIPLE_DOUBLE_QUOTE_STRING: /"""[\s\S]*?"""/
TRIPLE_SINGLE_QUOTE_STRING: /'''[\s\S]*?'''/
NUMBER: /-?[0-9]+(\.[0-9]+)?/
BOOL: "true" | "false"
CNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
COMMENT: /#[^\n]*/

// Whitespace and indentation
_NL: /\r?\n[\t ]*/
WS: /[ \t]+/
_WS: /[ \t]+/

%ignore WS
%ignore COMMENT
%declare INDENT DEDENT
"""
