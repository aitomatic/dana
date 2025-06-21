"""
Tests for Dana POET examples to ensure they execute correctly
"""

import os
from pathlib import Path

import pytest

from tests.dana.poet.helpers import PoetTestBase


@pytest.mark.poet
class TestDanaPOETExamples(PoetTestBase):
    """Test that Dana POET examples execute successfully"""

    def setup_method(self):
        """Setup for each test"""
        super().setup_method()
        # Force local mode for testing
        self.original_env = {}
        for key in ["AITOMATIC_API_URL", "AITOMATIC_API_KEY"]:
            self.original_env[key] = os.environ.get(key)

        os.environ["AITOMATIC_API_URL"] = "local"

        # Create sandbox for Dana execution
        # self.sandbox = DanaSandbox()

    def teardown_method(self):
        """Cleanup after each test"""
        # Restore environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

        # Clean up sandbox
        super().teardown_method()

    def test_basic_enhancement_example(self):
        """Test that the basic enhancement example executes successfully"""

        example_path = Path("examples/dana/poet/01_basic_enhancement.na")

        # Check if example file exists
        if not example_path.exists():
            pytest.skip(f"Example file not found: {example_path}")

        # Execute the example file directly
        execution_result = self.sandbox.run(example_path)

        # Example should execute successfully
        assert execution_result.success is True, f"Example failed with error: {execution_result.error}"
        assert execution_result.error is None

    def test_feedback_learning_example(self):
        """Test that the feedback learning example executes successfully"""

        example_path = Path("examples/dana/poet/02_feedback_learning.na")

        # Check if example file exists
        if not example_path.exists():
            pytest.skip(f"Example file not found: {example_path}")

        # Execute the example file directly
        execution_result = self.sandbox.run(example_path)

        # Example should execute successfully
        assert execution_result.success is True, f"Example failed with error: {execution_result.error}"
        assert execution_result.error is None

    def test_ml_monitoring_example(self):
        """Test that the ML monitoring example executes successfully"""

        example_path = Path("examples/dana/poet/03_ml_monitoring.na")

        # Check if example file exists
        if not example_path.exists():
            pytest.skip(f"Example file not found: {example_path}")

        # Execute the example file directly
        execution_result = self.sandbox.run(example_path)

        # Example should execute successfully
        assert execution_result.success is True, f"Example failed with error: {execution_result.error}"
        assert execution_result.error is None

    def test_poet_decorator_functionality(self):
        """Test core POET decorator functionality in isolation"""

        # Test basic decorator
        basic_code = """
@poet()
def test_basic(x: int) -> int:
    return x + 1

result = test_basic(5)
log(f"Basic result: {result}")
"""

        execution_result = self._run_dana_code(basic_code)
        assert execution_result.success is True
        assert execution_result.error is None

        # Test decorator with domain
        domain_code = """
@poet(domain="healthcare")  
def test_domain(value: float) -> bool:
    return value > 0

result = test_domain(1.5)
log(f"Domain result: {result}")
"""

        execution_result = self._run_dana_code(domain_code)
        assert execution_result.success is True
        assert execution_result.error is None

        # Test decorator with training
        training_code = """
@poet(optimize_for="speed")
def test_training(text: str) -> str:
    return text.upper()

result = test_training("hello")
log(f"Training result: {result}")
"""

        execution_result = self._run_dana_code(training_code)
        assert execution_result.success is True
        assert execution_result.error is None

    def test_feedback_functionality(self):
        """Test feedback function functionality in isolation"""

        feedback_code = """
@poet(optimize_for="accuracy")
def test_feedback_func(value: int) -> int:
    return value * 2

result = test_feedback_func(10)

# Test different feedback formats
feedback(result, "Great result!")
feedback(result, {"score": 5, "comment": "Excellent"})
feedback(result, 0.95)

log("All feedback submitted successfully")
"""

        execution_result = self._run_dana_code(feedback_code)
        assert execution_result.success is True
        assert execution_result.error is None

    def test_poet_result_properties(self):
        """Test POETResult properties and methods"""

        result_code = """
@poet()
def test_result_props(a: int, b: int) -> int:
    return a + b

result = test_result_props(3, 7)

# Test POETResult properties
execution_id = result._poet["execution_id"]
function_name = result._poet["function_name"]
enhanced = result._poet["enhanced"]
version = result._poet["version"]

log(f"Execution ID: {execution_id}")
log(f"Function name: {function_name}")
log(f"Enhanced: {enhanced}")
log(f"Version: {version}")

# Test unwrap
unwrapped = result.unwrap()
log(f"Unwrapped result: {unwrapped}")
"""

        execution_result = self._run_dana_code(result_code)
        assert execution_result.success is True
        assert execution_result.error is None

    def test_multiple_poet_functions(self):
        """Test multiple POET functions in the same execution"""

        multiple_code = """
@poet(domain="healthcare")
def health_check(heart_rate: int) -> str:
    if heart_rate < 60:
        return "low"
    elif heart_rate > 100:
        return "high"  
    else:
        return "normal"

@poet(optimize_for="risk_assessment")
def calculate_risk(age: int, cholesterol: int) -> str:
    if age > 50 and cholesterol > 200:
        return "high_risk"
    elif age > 30 or cholesterol > 150:
        return "medium_risk"
    else:
        return "low_risk"

# Test both functions
health_result = health_check(75)
risk_result = calculate_risk(45, 180)

log(f"Health check: {health_result}")
log(f"Risk assessment: {risk_result}")

# Provide feedback
feedback(health_result, "Accurate assessment")
feedback(risk_result, {"accuracy": 0.9, "note": "Good risk calculation"})
"""

        execution_result = self._run_dana_code(multiple_code)
        assert execution_result.success is True
        assert execution_result.error is None

    def test_poet_error_recovery(self):
        """Test POET error recovery and fallback behavior"""

        # Test with potentially problematic domain
        error_recovery_code = """
# Test with invalid domain - should fallback gracefully
@poet(domain="nonexistent_domain")
def test_fallback(x: int) -> int:
    return x * 3

# Should still work with fallback to original function
result = test_fallback(4)
log(f"Fallback result: {result}")

# Should still have POET metadata even if enhancement failed
execution_id = result._poet["execution_id"]
function_name = result._poet["function_name"]

log(f"Fallback execution ID: {execution_id}")
log(f"Fallback function name: {function_name}")
"""

        execution_result = self._run_dana_code(error_recovery_code)
        # Should complete successfully even with invalid domain
        assert execution_result.success is True
        assert execution_result.error is None

    def test_poet_with_complex_types(self):
        """Test POET functions with complex data types"""

        complex_types_code = """
@poet(domain="financial_services")
def analyze_portfolio(assets: list) -> dict:
    total_value = 0.0
    count = len(assets)

    for asset in assets:
        total_value = total_value + asset

    if count > 0:
        average = total_value / count
    else:
        average = 0.0

    if average > 1000:
        status = "healthy"
    else:
        status = "review"

    return {
        "total_value": total_value,
        "asset_count": count,
        "average_value": average,
        "status": status
    }

# Test with complex input/output
portfolio = [1200.0, 850.0, 2100.0, 950.0]
analysis = analyze_portfolio(portfolio)

log(f"Portfolio analysis: {analysis}")

# Test accessing result properties
total = analysis["total_value"]
status = analysis["status"]

log(f"Total portfolio value: {total}")
log(f"Portfolio status: {status}")
"""

        execution_result = self._run_dana_code(complex_types_code)
        assert execution_result.success is True
        assert execution_result.error is None

    def test_poet_configuration_parameters(self):
        """Test POET with various configuration parameters"""

        config_code = """
# Test different configuration combinations
@poet(domain="manufacturing", timeout=60.0, retries=2)
def quality_control(measurement: float, tolerance: float) -> bool:
    diff = measurement - 100.0
    if diff < 0:
        diff = -diff  # absolute value
    return diff <= tolerance

@poet(optimize_for="performance")
def performance_check(response_time: float) -> str:
    if response_time < 0.1:
        return "excellent"
    elif response_time < 1.0:
        return "good"
    else:
        return "slow"

# Test both configured functions
quality_result = quality_control(98.5, 2.0)
perf_result = performance_check(0.05)

log(f"Quality control: {quality_result}")
log(f"Performance: {perf_result}")

# Provide feedback
feedback(quality_result, "Quality check was accurate")
feedback(perf_result, {"response_accuracy": 1.0})
"""

        execution_result = self._run_dana_code(config_code)
        assert execution_result.success is True
        assert execution_result.error is None


@pytest.mark.poet
class TestDanaPOETExampleValidation:
    """Validate that Dana POET examples follow correct patterns"""

    def test_example_file_existence(self):
        """Test that all expected example files exist"""

        expected_examples = [
            "examples/dana/poet/01_basic_enhancement.na",
            "examples/dana/poet/02_feedback_learning.na",
            "examples/dana/poet/03_ml_monitoring.na",
            "examples/dana/poet/README.md",
        ]

        for example_path in expected_examples:
            path = Path(example_path)
            assert path.exists(), f"Expected example file not found: {example_path}"

    def test_example_syntax_validity(self):
        """Test that example files contain valid Dana syntax"""

        example_files = [
            "examples/dana/poet/01_basic_enhancement.na",
            "examples/dana/poet/02_feedback_learning.na",
            "examples/dana/poet/03_ml_monitoring.na",
        ]

        for example_path in example_files:
            path = Path(example_path)
            if not path.exists():
                pytest.skip(f"Example file not found: {example_path}")

            # Read file content
            with open(path) as f:
                content = f.read()

            # Basic syntax checks
            assert "@poet(" in content, f"Example should contain @poet decorator: {example_path}"
            assert "def " in content, f"Example should contain function definitions: {example_path}"
            assert "log(" in content, f"Example should contain log statements: {example_path}"

            # Check for proper Dana syntax patterns
            assert "return " in content, f"Example should contain return statements: {example_path}"

            # Ensure no Python-specific syntax that doesn't work in Dana
            assert "+=" not in content, f"Example should not use += operator: {example_path}"
            assert "abs(" not in content, f"Example should not use abs() function: {example_path}"

    def test_example_poet_patterns(self):
        """Test that examples follow correct POET usage patterns"""

        # Test basic enhancement example
        basic_path = Path("examples/dana/poet/01_basic_enhancement.na")
        if basic_path.exists():
            with open(basic_path) as f:
                content = f.read()

            # Should contain basic decorator usage
            assert "@poet()" in content
            # Should contain domain-specific usage
            assert "domain=" in content
            # Should contain training usage
            assert "optimize_for" in content

        # Test feedback learning example
        feedback_path = Path("examples/dana/poet/02_feedback_learning.na")
        if feedback_path.exists():
            with open(feedback_path) as f:
                content = f.read()

            # Should contain feedback concepts (calls or simulation)
            assert "feedback(" in content or "feedback" in content.lower()
            # Should contain training-enabled functions
            assert "optimize_for=" in content

        # Test ML monitoring example
        ml_path = Path("examples/dana/poet/03_ml_monitoring.na")
        if ml_path.exists():
            with open(ml_path) as f:
                content = f.read()

            # Should contain ML-related functions
            assert "detect" in content.lower() or "monitor" in content.lower()
            # Should contain domain usage appropriate for ML
            assert "domain=" in content
