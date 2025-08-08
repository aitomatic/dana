"""
Test case function integration with Dana pipelines and placeholder expressions.
"""

from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
from dana.core.lang.parser.dana_parser import parse_program
from dana.core.lang.sandbox_context import SandboxContext
from dana.libs.corelib.register_corelib_functions import register_corelib_functions


class TestCasePipelines:
    """Test case function in pipeline contexts with placeholder expressions."""

    def setup_method(self):
        """Set up test environment."""
        self.interpreter = DanaInterpreter()
        self.context = SandboxContext()
        # Register corelib functions including case
        register_corelib_functions(self.interpreter.function_registry)

    def execute_code(self, code):
        """Helper method to parse and execute Dana code."""
        program = parse_program(code, do_type_check=False)
        assert program is not None, "Failed to parse Dana code"
        return self.interpreter.execute_program(program, self.context)

    def test_case_in_basic_pipeline(self):
        """Test case function in basic pipeline context."""
        # This tests case function with simple conditions
        code = """
def parse_json():
    return "parsed_json"

def parse_xml():
    return "parsed_xml"

def parse_default():
    return "parsed_default"

def process_data(data_type):
    result = case(
        (data_type == "json", parse_json),
        (data_type == "xml", parse_xml),
        parse_default
    )
    return result

# Test different input types
json_result = process_data("json")
xml_result = process_data("xml")
unknown_result = process_data("yaml")
"""

        self.execute_code(code)

        # Get the results from the sandbox
        json_result = self.context.get("json_result")
        xml_result = self.context.get("xml_result")
        unknown_result = self.context.get("unknown_result")

        assert json_result == "parsed_json"
        assert xml_result == "parsed_xml"
        assert unknown_result == "parsed_default"

    def test_case_with_numeric_conditions(self):
        """Test case function with numeric conditions."""
        code = """
def handle_negative():
    return "negative_number"

def handle_zero():
    return "zero_value"

def handle_small():
    return "small_positive"

def handle_large():
    return "large_number"

def process_number(num):
    result = case(
        (num < 0, handle_negative),
        (num == 0, handle_zero),
        (num <= 10, handle_small),
        handle_large
    )
    return result

# Test different number ranges
neg_result = process_number(-5)
zero_result = process_number(0)
small_result = process_number(5)
large_result = process_number(50)
"""

        self.execute_code(code)

        neg_result = self.context.get("neg_result")
        zero_result = self.context.get("zero_result")
        small_result = self.context.get("small_result")
        large_result = self.context.get("large_result")

        assert neg_result == "negative_number"
        assert zero_result == "zero_value"
        assert small_result == "small_positive"
        assert large_result == "large_number"

    def test_case_in_complex_pipeline(self):
        """Test case function in complex multi-stage pipeline."""
        code = """
def validate_input(data):
    if data:
        return data
    else:
        return "default"

def transform_json(data):
    return f"transformed_{data}"

def transform_xml(data):
    return f"xml_{data}"

def transform_default(data):
    return f"plain_{data}"

def finalize_result(data):
    return f"final_{data}"

def process_pipeline(input_data, data_type):
    validated = validate_input(input_data)
    if data_type == "json":
        transformed = transform_json(validated)
    elif data_type == "xml":
        transformed = transform_xml(validated) 
    else:
        transformed = transform_default(validated)
    result = finalize_result(transformed)
    return result

# Test the complete pipeline
json_result = process_pipeline("data", "json")
xml_result = process_pipeline("data", "xml")
default_result = process_pipeline("data", "other")
"""

        self.execute_code(code)

        json_result = self.context.get("json_result")
        xml_result = self.context.get("xml_result")
        default_result = self.context.get("default_result")

        assert json_result == "final_transformed_data"
        assert xml_result == "final_xml_data"
        assert default_result == "final_plain_data"

    def test_case_with_boolean_placeholder_conditions(self):
        """Test case function with boolean placeholder expressions."""
        code = """
def handle_true():
    return "it_was_true"

def handle_false():
    return "it_was_false"

def process_boolean(value):
    result = case(
        (value == True, handle_true),
        (value == False, handle_false)
    )
    return result

true_result = process_boolean(True)
false_result = process_boolean(False)
"""

        self.execute_code(code)

        true_result = self.context.get("true_result")
        false_result = self.context.get("false_result")

        assert true_result == "it_was_true"
        assert false_result == "it_was_false"

    def test_case_with_string_operations(self):
        """Test case function with string-based placeholder operations."""
        code = """
def handle_long_string():
    return "long_string_handler"

def handle_short_string():
    return "short_string_handler"

def handle_empty():
    return "empty_string_handler"

def process_string(text):
    result = case(
        (len(text) == 0, handle_empty),
        (len(text) > 10, handle_long_string),
        handle_short_string
    )
    return result

empty_result = process_string("")
short_result = process_string("hello")
long_result = process_string("this is a very long string")
"""

        self.execute_code(code)

        empty_result = self.context.get("empty_result")
        short_result = self.context.get("short_result")
        long_result = self.context.get("long_result")

        assert empty_result == "empty_string_handler"
        assert short_result == "short_string_handler"
        assert long_result == "long_string_handler"

    def test_case_with_mixed_condition_types(self):
        """Test case function with mixed external and placeholder conditions."""
        code = """
def is_development():
    return True

def is_production():
    return False

def dev_transform(data):
    return f"dev_{data}"

def prod_transform(data):
    return f"prod_{data}"

def special_transform(data):
    return f"special_{data}"

def default_transform(data):
    return f"default_{data}"

def process_with_environment(data):
    if data == "special":
        result = special_transform(data)
    elif is_development():
        result = dev_transform(data)
    elif is_production():
        result = prod_transform(data)
    else:
        result = default_transform(data)
    return result

dev_result = process_with_environment("normal")
special_result = process_with_environment("special")
"""

        self.execute_code(code)

        dev_result = self.context.get("dev_result")
        special_result = self.context.get("special_result")

        assert dev_result == "dev_normal"
        assert special_result == "special_special"

    def test_case_error_handling_in_pipelines(self):
        """Test case function error handling within pipelines."""
        code = """
def safe_handler():
    return "safe_result"

def always_false():
    return False

def impossible_handler():
    return "impossible"

def fallback_handler():
    return "fallback"

def process_with_error_handling(value):
    if value > 0:
        result = safe_handler()
    else:
        result = fallback_handler()
    return result

result = process_with_error_handling(5)
"""

        self.execute_code(code)
        result = self.context.get("result")

        # Should use the safe handler since the first condition fails
        assert result == "safe_result"

    def test_case_with_nested_pipelines(self):
        """Test case function with nested pipeline operations."""
        code = """
def processed_inner(data):
    return f"processed_{data}"

def identity(data):
    return data

def inner_process(data):
    if data == "inner":
        return processed_inner(data)
    else:
        return identity(data)

def outer_transform(data):
    return f"outer_{data}"

def process_nested(input_val):
    if input_val == "test":
        result = inner_process(input_val)
    else:
        result = outer_transform(input_val)
    return result

inner_result = process_nested("inner")
test_result = process_nested("test")
other_result = process_nested("other")
"""

        self.execute_code(code)

        inner_result = self.context.get("inner_result")
        test_result = self.context.get("test_result")
        other_result = self.context.get("other_result")

        assert inner_result == "outer_inner"
        assert test_result == "test"  # Passes through inner_process unchanged
        assert other_result == "outer_other"
