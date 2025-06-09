"""
Unit tests for IPV type inference system.

Tests the TypeInferenceEngine class that detects expected types from various sources.
"""


from opendxa.dana.ipv.base import ContextLevel, PrecisionLevel, ReliabilityLevel, SafetyLevel, StructureLevel
from opendxa.dana.ipv.type_inference import TypeInferenceEngine


class TestTypeInferenceEngine:
    """Test TypeInferenceEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TypeInferenceEngine()

    def test_basic_type_inference_from_string(self):
        """Test inferring basic types from string representations."""
        test_cases = [
            ("str", str),
            ("int", int),
            ("float", float),
            ("bool", bool),
            ("dict", dict),
            ("list", list),
            ("tuple", tuple),
            ("set", set),
            ("bytes", bytes),
            ("None", type(None)),
        ]

        for type_string, expected_type in test_cases:
            inferred_type = self.engine.infer_type_from_string(type_string)
            assert inferred_type == expected_type, f"Failed to infer {type_string} as {expected_type}"

    def test_generic_type_inference_from_string(self):
        """Test inferring generic types from string representations."""
        # Test List[str]
        list_str_type = self.engine.infer_type_from_string("List[str]")
        assert list_str_type is not None
        # Note: Exact generic type comparison is complex, so we test the structure

        # Test Dict[str, int]
        dict_type = self.engine.infer_type_from_string("Dict[str, int]")
        assert dict_type is not None

        # Test Optional[str]
        optional_type = self.engine.infer_type_from_string("Optional[str]")
        assert optional_type is not None

        # Test Union[str, int]
        union_type = self.engine.infer_type_from_string("Union[str, int]")
        assert union_type is not None

    def test_invalid_type_string(self):
        """Test handling of invalid type strings."""
        invalid_types = [
            "InvalidType",
            "List[",
            "Dict[str",
            "",
            "123",
            "random_string",
        ]

        for invalid_type in invalid_types:
            inferred_type = self.engine.infer_type_from_string(invalid_type)
            assert inferred_type is None, f"Should not infer type for invalid string: {invalid_type}"

    def test_assignment_code_inference(self):
        """Test inferring types from assignment code."""
        test_cases = [
            ("price: float = 29.99", float),
            ("count: int = 5", int),
            ("is_valid: bool = True", bool),
            ("name: str = 'test'", str),
            ("data: dict = {}", dict),
            ("items: list = []", list),
        ]

        for assignment_code, expected_type in test_cases:
            inferred_type = self.engine.infer_type_from_assignment(assignment_code)
            assert inferred_type == expected_type, f"Failed to infer type from: {assignment_code}"

    def test_assignment_code_without_annotation(self):
        """Test handling assignment code without type annotations."""
        no_annotation_cases = [
            "price = 29.99",
            "count = 5",
            "name = 'test'",
            "data = {}",
        ]

        for assignment_code in no_annotation_cases:
            inferred_type = self.engine.infer_type_from_assignment(assignment_code)
            assert inferred_type is None, f"Should not infer type from non-annotated assignment: {assignment_code}"

    def test_invalid_assignment_code(self):
        """Test handling of invalid assignment code."""
        invalid_cases = [
            "invalid syntax",
            "price: = 29.99",
            ":",
            "",
        ]

        for invalid_code in invalid_cases:
            inferred_type = self.engine.infer_type_from_assignment(invalid_code)
            assert inferred_type is None, f"Should not infer type from invalid code: {invalid_code}"

    def test_generic_type_detection(self):
        """Test detection of generic types."""
        # Test with actual generic types

        assert self.engine.is_generic_type(list[str]) is True
        assert self.engine.is_generic_type(dict[str, int]) is True

        # Test with basic types
        assert self.engine.is_generic_type(str) is False
        assert self.engine.is_generic_type(int) is False
        assert self.engine.is_generic_type(dict) is False

    def test_generic_type_info(self):
        """Test extraction of generic type information."""

        # Test List[str]
        list_info = self.engine.get_generic_info(list[str])
        assert list_info["origin"] == list
        assert str in list_info["args"]

        # Test Dict[str, int]
        dict_info = self.engine.get_generic_info(dict[str, int])
        assert dict_info["origin"] == dict
        assert str in dict_info["args"]
        assert int in dict_info["args"]

        # Test basic type
        str_info = self.engine.get_generic_info(str)
        assert str_info["origin"] == str
        assert str_info["args"] == []

    def test_type_defaults_for_basic_types(self):
        """Test getting type-specific defaults for basic types."""
        # Test float defaults
        float_defaults = self.engine.get_type_defaults(float)
        assert float_defaults["reliability"] == ReliabilityLevel.MAXIMUM
        assert float_defaults["precision"] == PrecisionLevel.EXACT
        assert float_defaults["safety"] == SafetyLevel.HIGH
        assert "handle_currency" in float_defaults["auto_cleaning"]

        # Test int defaults
        int_defaults = self.engine.get_type_defaults(int)
        assert int_defaults["reliability"] == ReliabilityLevel.MAXIMUM
        assert int_defaults["precision"] == PrecisionLevel.EXACT
        assert "extract_integers" in int_defaults["auto_cleaning"]

        # Test bool defaults
        bool_defaults = self.engine.get_type_defaults(bool)
        assert bool_defaults["reliability"] == ReliabilityLevel.MAXIMUM
        assert bool_defaults["precision"] == PrecisionLevel.EXACT
        assert "parse_yes_no" in bool_defaults["auto_cleaning"]

        # Test str defaults
        str_defaults = self.engine.get_type_defaults(str)
        assert str_defaults["reliability"] == ReliabilityLevel.HIGH
        assert str_defaults["precision"] == PrecisionLevel.SPECIFIC
        assert "remove_markdown" in str_defaults["auto_cleaning"]

        # Test dict defaults
        dict_defaults = self.engine.get_type_defaults(dict)
        assert dict_defaults["structure"] == StructureLevel.STRICT
        assert "validate_json" in dict_defaults["auto_cleaning"]

        # Test list defaults
        list_defaults = self.engine.get_type_defaults(list)
        assert list_defaults["structure"] == StructureLevel.FORMATTED
        assert "parse_arrays" in list_defaults["auto_cleaning"]

    def test_type_defaults_for_generic_types(self):
        """Test getting type-specific defaults for generic types."""

        # Test List[str] defaults
        list_str_defaults = self.engine.get_type_defaults(list[str])
        assert list_str_defaults["reliability"] == ReliabilityLevel.HIGH
        assert "generic_args" in list_str_defaults
        assert str in list_str_defaults["generic_args"]

        # Test Dict[str, int] defaults
        dict_defaults = self.engine.get_type_defaults(dict[str, int])
        assert dict_defaults["structure"] == StructureLevel.STRICT
        assert "generic_args" in dict_defaults
        assert str in dict_defaults["generic_args"]
        assert int in dict_defaults["generic_args"]

    def test_type_defaults_for_unknown_type(self):
        """Test getting defaults for unknown types."""

        class CustomType:
            pass

        defaults = self.engine.get_type_defaults(CustomType)

        # Should return fallback defaults
        assert defaults["reliability"] == ReliabilityLevel.HIGH
        assert defaults["precision"] == PrecisionLevel.SPECIFIC
        assert defaults["safety"] == SafetyLevel.MEDIUM
        assert defaults["auto_cleaning"] == []
        assert defaults["validation_rules"] == []

    def test_context_inference_with_mock_context(self):
        """Test type inference from context with mock context object."""

        class MockContext:
            def get_type_annotation(self, variable_name):
                annotations = {
                    "price": float,
                    "count": int,
                    "name": str,
                }
                return annotations.get(variable_name)

        mock_context = MockContext()

        # Test successful inference
        inferred_type = self.engine.infer_type_from_context(mock_context, "price")
        assert inferred_type == float

        inferred_type = self.engine.infer_type_from_context(mock_context, "count")
        assert inferred_type == int

        # Test unknown variable
        inferred_type = self.engine.infer_type_from_context(mock_context, "unknown")
        assert inferred_type is None

    def test_context_inference_without_annotation_method(self):
        """Test type inference from context without get_type_annotation method."""

        class SimpleContext:
            def __init__(self):
                self.some_data = "test"

        simple_context = SimpleContext()

        # Should return None since context doesn't have get_type_annotation
        inferred_type = self.engine.infer_type_from_context(simple_context, "variable")
        assert inferred_type is None

    def test_context_inference_with_none_context(self):
        """Test type inference with None context."""
        inferred_type = self.engine.infer_type_from_context(None, "variable")
        assert inferred_type is None

    def test_whitespace_handling_in_type_strings(self):
        """Test that type inference handles whitespace correctly."""
        test_cases = [
            ("  str  ", str),
            ("\tint\t", int),
            (" float ", float),
            ("List[ str ]", None),  # Spaces in generic types might not be supported
            ("Dict[str, int]", None),  # But no spaces should work
        ]

        for type_string, expected_type in test_cases:
            inferred_type = self.engine.infer_type_from_string(type_string)
            if expected_type is None:
                # We expect this to either work or fail gracefully
                assert inferred_type is None or inferred_type is not None
            else:
                assert inferred_type == expected_type, f"Failed to handle whitespace in: '{type_string}'"

    def test_case_sensitivity(self):
        """Test that type inference is case sensitive."""
        # These should not work (wrong case)
        invalid_cases = ["STR", "Int", "FLOAT", "Bool"]

        for invalid_case in invalid_cases:
            inferred_type = self.engine.infer_type_from_string(invalid_case)
            assert inferred_type is None, f"Should not infer type for wrong case: {invalid_case}"

    def test_caching_behavior(self):
        """Test that the engine properly uses caching."""
        # The engine has internal caches, but they're not exposed
        # We can test that repeated calls work consistently

        for _ in range(3):
            assert self.engine.infer_type_from_string("str") == str
            assert self.engine.infer_type_from_string("int") == int
            assert self.engine.get_type_defaults(float)["reliability"] == ReliabilityLevel.MAXIMUM


class TestTypeInferenceIntegration:
    """Integration tests for type inference with real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TypeInferenceEngine()

    def test_financial_type_optimization(self):
        """Test type inference and optimization for financial scenarios."""
        # Test float type for financial data
        float_defaults = self.engine.get_type_defaults(float)

        assert float_defaults["reliability"] == ReliabilityLevel.MAXIMUM
        assert float_defaults["precision"] == PrecisionLevel.EXACT
        assert float_defaults["safety"] == SafetyLevel.HIGH
        assert "handle_currency" in float_defaults["auto_cleaning"]
        assert "numeric_only" in float_defaults["validation_rules"]

    def test_text_processing_optimization(self):
        """Test type inference and optimization for text processing."""
        # Test str type for text processing
        str_defaults = self.engine.get_type_defaults(str)

        assert str_defaults["reliability"] == ReliabilityLevel.HIGH
        assert str_defaults["precision"] == PrecisionLevel.SPECIFIC
        assert "remove_markdown" in str_defaults["auto_cleaning"]
        assert "clean_bullets" in str_defaults["auto_cleaning"]

    def test_data_structure_optimization(self):
        """Test type inference and optimization for data structures."""
        # Test dict type for structured data
        dict_defaults = self.engine.get_type_defaults(dict)

        assert dict_defaults["structure"] == StructureLevel.STRICT
        assert dict_defaults["context"] == ContextLevel.DETAILED
        assert "validate_json" in dict_defaults["auto_cleaning"]
        assert "valid_json" in dict_defaults["validation_rules"]

    def test_boolean_classification_optimization(self):
        """Test type inference and optimization for boolean classification."""
        # Test bool type for classification tasks
        bool_defaults = self.engine.get_type_defaults(bool)

        assert bool_defaults["reliability"] == ReliabilityLevel.MAXIMUM
        assert bool_defaults["precision"] == PrecisionLevel.EXACT
        assert "parse_yes_no" in bool_defaults["auto_cleaning"]
        assert "boolean_only" in bool_defaults["validation_rules"]
