"""
Common translation patterns for Dana transcoder.

This module contains templates and examples for common natural language to Dana translations.
"""

# Common patterns for natural language to Dana translation
TRANSLATION_PATTERNS = {
    "arithmetic": {
        "examples": [
            ("calculate 10 plus 5", "private:result = 10 + 5\nprint(f'Result: {private:result}')"),
            ("add 42 and 17", "private:sum = 42 + 17\nprint(f'Sum: {private:sum}')"),
            ("multiply 8 by 9", "private:product = 8 * 9\nprint(f'Product: {private:product}')"),
            ("divide 100 by 4", "private:quotient = 100 / 4\nprint(f'Quotient: {private:quotient}')"),
        ]
    },
    "variables": {
        "examples": [
            ("set variable x to 42", "private:x = 42"),
            ("create a variable called count with value 0", "private:count = 0"),
            ("store the name John in a variable", "private:name = 'John'"),
        ]
    },
    "conditionals": {
        "examples": [
            ("if x is greater than 10 then print success", "if private:x > 10:\n    print('success')"),
            ("if temperature exceeds 100 then log alert", "if private:temperature > 100:\n    log.warn('Temperature alert!')"),
        ]
    },
    "logging": {
        "examples": [
            ("log hello world", "log.info('hello world')"),
            ("log an error message", "log.error('An error occurred')"),
            ("warn about high temperature", "log.warn('High temperature detected')"),
            ("debug the current state", "log.debug('Current state logged')"),
            ("log information", "log.info('Information logged')"),
        ]
    },
    "printing": {
        "examples": [
            ("print hello world", "print('hello world')"),
            ("display the value of x", "print(f'x = {private:x}')"),
            ("show the result", "print(f'Result: {private:result}')"),
        ]
    },
}


def get_pattern_examples(pattern_type: str) -> list:
    """Get examples for a specific pattern type."""
    return TRANSLATION_PATTERNS.get(pattern_type, {}).get("examples", [])


def get_all_examples() -> list:
    """Get all translation examples."""
    all_examples = []
    for pattern in TRANSLATION_PATTERNS.values():
        all_examples.extend(pattern["examples"])
    return all_examples
