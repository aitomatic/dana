"""Constants for Dana's type system."""

# Basic type names that are recognized throughout the Dana type system
BASIC_TYPE_NAMES = {"int", "float", "str", "bool", "list", "dict", "tuple", "set", "any", "null", "None"}

# Type mapping from Python types to Dana type names
PYTHON_TO_DANA_TYPE_MAPPING = {
    int: "int",
    float: "float",
    str: "str",
    bool: "bool",
    list: "list",
    dict: "dict",
    tuple: "tuple",
    set: "set",
    type(None): "null",
}

# Type names that are commonly used in type hints and validation
COMMON_TYPE_NAMES = {"int", "float", "str", "bool", "list", "dict", "tuple", "set", "any"}
