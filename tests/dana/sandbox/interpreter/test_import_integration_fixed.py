"""Working integration tests for import statements in larger Dana programs.

This test suite covers Steps 5.1 and 5.2 with WORKING function names:
- Imports within complex Dana programs
- Multiple imports with interdependencies
- Mixed Python and Dana import scenarios
"""

import os
from pathlib import Path

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.runtime.modules.core import initialize_module_system, reset_module_system


class TestImportIntegrationWorking:
    """Working integration tests for imports in larger programs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sandbox = DanaSandbox()

        # Set the module search path to include our test modules
        test_modules_path = Path(__file__).parent / "test_modules"
        self.test_modules_path = str(test_modules_path.resolve())

        # Add the test modules path to DANAPATH for testing
        os.environ.setdefault("DANAPATH", "")
        if self.test_modules_path not in os.environ["DANAPATH"]:
            os.environ["DANAPATH"] = f"{self.test_modules_path}{os.pathsep}{os.environ['DANAPATH']}"

        # Reset and reinitialize the module system to pick up the updated search paths
        reset_module_system()
        initialize_module_system()

    def test_large_program_with_multiple_dana_imports(self):
        """Test a larger Dana program that uses multiple imported modules together."""
        # Import modules
        import_result1 = self.sandbox.eval("import simple_math")
        import_result2 = self.sandbox.eval("import string_utils")
        import_result3 = self.sandbox.eval("from data_types import create_point")

        assert import_result1.success is True
        assert import_result2.success is True
        assert import_result3.success is True

        # Mathematical calculations
        base_result = self.sandbox.eval("base_value = simple_math.add(10, 5)")
        assert base_result.success is True

        squared_result = self.sandbox.eval("squared = simple_math.square(base_value)")
        assert squared_result.success is True

        area_result = self.sandbox.eval("area = simple_math.multiply(squared, simple_math.PI)")
        assert area_result.success is True

        # String processing using ACTUAL available functions
        text_result = self.sandbox.eval('text = "integration test example"')
        assert text_result.success is True

        processed_result = self.sandbox.eval("processed = string_utils.to_upper(text)")
        assert processed_result.success is True

        word_count_result = self.sandbox.eval("word_count = string_utils.word_count(processed)")
        assert word_count_result.success is True

        # Data structure creation
        point_result = self.sandbox.eval("point = create_point(area, word_count)")
        assert point_result.success is True

        # Complex computation combining all imports
        result_add = self.sandbox.eval("result = simple_math.add(point.x, point.y)")
        assert result_add.success is True

        # Verification - get final values
        base_check = self.sandbox.eval("base_value")
        assert base_check.success is True
        assert base_check.result == 15  # 10 + 5

        squared_check = self.sandbox.eval("squared")
        assert squared_check.success is True
        assert squared_check.result == 225  # 15^2

        processed_check = self.sandbox.eval("processed")
        assert processed_check.success is True
        assert processed_check.result == "INTEGRATION TEST EXAMPLE"

    def test_mixed_python_dana_imports_working(self):
        """Test mixing Python and Dana module imports with working functions."""
        # Python imports
        math_result = self.sandbox.eval("import math.py")
        assert math_result.success is True

        # Dana imports
        simple_math_result = self.sandbox.eval("import simple_math")
        assert simple_math_result.success is True

        # Python operations
        pi_python_result = self.sandbox.eval("pi_python = math.pi")
        assert pi_python_result.success is True

        sin_result = self.sandbox.eval("sin_value = math.sin(math.pi / 2)")
        assert sin_result.success is True

        # Dana operations
        pi_dana_result = self.sandbox.eval("pi_dana = simple_math.PI")
        assert pi_dana_result.success is True

        dana_squared_result = self.sandbox.eval("dana_squared = simple_math.square(10)")
        assert dana_squared_result.success is True

        # Verify results
        pi_python_check = self.sandbox.eval("pi_python")
        assert pi_python_check.success is True
        assert abs(pi_python_check.result - 3.14159) < 0.001

        sin_check = self.sandbox.eval("sin_value")
        assert sin_check.success is True
        assert sin_check.result == 1.0

        pi_dana_check = self.sandbox.eval("pi_dana")
        assert pi_dana_check.success is True
        assert abs(pi_dana_check.result - 3.14159) < 0.001

        dana_squared_check = self.sandbox.eval("dana_squared")
        assert dana_squared_check.success is True
        assert dana_squared_check.result == 100

    def test_sequential_imports_and_usage_working(self):
        """Test using imports in sequential operations with working functions."""
        # Sequential imports
        result1 = self.sandbox.eval("import simple_math")
        result2 = self.sandbox.eval("import string_utils")
        assert result1.success is True
        assert result2.success is True

        # Sequential operations using imports with WORKING functions
        operations = [
            ("x = 10", None),
            ("y = 5", None),
            ("sum_result = simple_math.add(x, y)", None),
            ("squared = simple_math.square(sum_result)", None),
            ('text = "hello world"', None),
            ("upper_text = string_utils.to_upper(text)", None),
            ("word_count = string_utils.word_count(upper_text)", None),
            ("final = simple_math.multiply(squared, word_count)", None),
        ]

        for op, _ in operations:
            result = self.sandbox.eval(op)
            assert result.success is True

        # Verify results
        verifications = [
            ("sum_result", 15),  # 10 + 5
            ("squared", 225),  # 15^2
            ("upper_text", "HELLO WORLD"),
            ("word_count", 2),  # "HELLO WORLD" has 2 words
            ("final", 450),  # 225 * 2
        ]

        for var, expected in verifications:
            check = self.sandbox.eval(var)
            assert check.success is True
            assert check.result == expected

    def test_multiple_from_imports_working(self):
        """Test using multiple from-import statements with working functions."""
        # Multiple from-imports
        imports = [
            "from simple_math import add",
            "from simple_math import multiply",
            "from simple_math import square",
            "from string_utils import to_upper",
            "from string_utils import word_count",
        ]

        for import_stmt in imports:
            result = self.sandbox.eval(import_stmt)
            assert result.success is True

        # Use all imported functions
        operations = [
            ("a = add(10, 15)", 25),
            ("b = multiply(a, 2)", 50),
            ("c = square(5)", 25),
            ('d = to_upper("test string")', "TEST STRING"),
            ("e = word_count(d)", 2),  # "TEST STRING" has 2 words
            ("final_result = add(b, c)", 75),
        ]

        for op, expected in operations:
            result = self.sandbox.eval(op)
            assert result.success is True

            # Verify the assigned variable
            var_name = op.split(" = ")[0]
            check = self.sandbox.eval(var_name)
            assert check.success is True
            assert check.result == expected

    def test_package_imports_working(self):
        """Test package imports in integration scenarios with working functions."""
        # Package imports using ACTUAL available functions
        result1 = self.sandbox.eval("from utils import factorial")  # This is available
        assert result1.success is True

        result2 = self.sandbox.eval("import utils")
        assert result2.success is True

        # Use package functions that actually exist
        operations = [
            ("factorial_result = factorial(5)", 120),
            ("package_info = utils.get_package_info()", "utils v1.0.0"),
            ("package_version = utils.PACKAGE_VERSION", "1.0.0"),
        ]

        for op, expected in operations:
            result = self.sandbox.eval(op)
            assert result.success is True

            var_name = op.split(" = ")[0]
            check = self.sandbox.eval(var_name)
            assert check.success is True
            assert check.result == expected

    def test_submodule_imports_working(self):
        """Test submodule imports with working functions."""
        # Submodule imports using actual available functions
        result1 = self.sandbox.eval("from utils.text import title_case")
        assert result1.success is True

        result2 = self.sandbox.eval("from utils.numbers import factorial")
        assert result2.success is True

        # Use submodule functions
        operations = [
            ('title_result = title_case("hello world")', "Hello World"),
            ("factorial_result = factorial(4)", 24),
        ]

        for op, expected in operations:
            result = self.sandbox.eval(op)
            assert result.success is True

            var_name = op.split(" = ")[0]
            check = self.sandbox.eval(var_name)
            assert check.success is True
            assert check.result == expected

    def test_import_alias_working(self):
        """Test import aliases with working functions."""
        # Import with aliases
        aliases = [
            "import simple_math as math",
            "import string_utils as str_util",
            "from data_types import create_point as point",
        ]

        for alias_stmt in aliases:
            result = self.sandbox.eval(alias_stmt)
            assert result.success is True

        # Use aliased imports with working functions
        operations = [
            ("val1 = math.add(10, 20)", 30),
            ("val2 = math.square(val1)", 900),
            ('text = str_util.to_upper("alias test")', "ALIAS TEST"),
            ("word_count = str_util.word_count(text)", 2),
        ]

        for op, expected in operations:
            result = self.sandbox.eval(op)
            assert result.success is True

            var_name = op.split(" = ")[0]
            check = self.sandbox.eval(var_name)
            assert check.success is True
            assert check.result == expected

        # Test point creation with alias
        point_op = self.sandbox.eval("point_obj = point(val2, word_count)")
        assert point_op.success is True

    def test_error_handling_in_complex_imports(self):
        """Test error handling when imports are used in complex scenarios."""
        # Test valid import and usage
        import_result = self.sandbox.eval("import simple_math")
        assert import_result.success is True

        valid_result = self.sandbox.eval("result1 = simple_math.add(5, 10)")
        assert valid_result.success is True

        # Test invalid function call
        invalid_result = self.sandbox.eval("result2 = simple_math.nonexistent_function(5)")
        assert invalid_result.success is False

        # Test invalid import
        invalid_import = self.sandbox.eval("import nonexistent_module")
        assert invalid_import.success is False

        # Verify the valid result still works
        check = self.sandbox.eval("result1")
        assert check.success is True
        assert check.result == 15

    def test_real_world_data_processing_scenario(self):
        """Test a realistic data processing scenario using multiple imports."""
        # Setup imports for data processing
        setup_imports = [
            "import simple_math",
            "import string_utils",
            "from data_types import create_point",
            "from utils.text import title_case",
            "from utils.numbers import factorial",
        ]

        for import_stmt in setup_imports:
            result = self.sandbox.eval(import_stmt)
            assert result.success is True

        # Simulate processing data entries
        operations = [
            # Entry 1 processing
            ('name1 = "john doe"', None),
            ("age1 = 25", None),
            ("formatted_name1 = title_case(name1)", "John Doe"),
            ("squared_age1 = simple_math.square(age1)", 625),
            ("name_words1 = string_utils.word_count(formatted_name1)", 2),
            # Entry 2 processing
            ('name2 = "jane smith"', None),
            ("age2 = 30", None),
            ("formatted_name2 = title_case(name2)", "Jane Smith"),
            ("squared_age2 = simple_math.square(age2)", 900),
            ("name_words2 = string_utils.word_count(formatted_name2)", 2),
            # Aggregate calculations
            ("total_age_squared = simple_math.add(squared_age1, squared_age2)", 1525),
            ("average_name_words = simple_math.add(name_words1, name_words2)", 4),
            ("factorial_result = factorial(4)", 24),
            ("final_score = simple_math.multiply(total_age_squared, factorial_result)", 36600),
        ]

        for op, expected in operations:
            result = self.sandbox.eval(op)
            assert result.success is True

            if expected is not None:
                var_name = op.split(" = ")[0]
                check = self.sandbox.eval(var_name)
                assert check.success is True
                assert check.result == expected

        # Verify final computation
        final_check = self.sandbox.eval("final_score")
        assert final_check.success is True
        assert final_check.result == 36600  # (625 + 900) * 24 = 1525 * 24
