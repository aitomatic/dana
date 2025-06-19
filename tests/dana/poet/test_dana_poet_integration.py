"""
Tests for POET integration with Dana language
"""

import os
import tempfile

from tests.dana.poet.helpers import PoetTestBase


class TestDanaPOETIntegration(PoetTestBase):
    """Test POET decorator functionality within Dana language execution"""

    def setup_method(self):
        """Setup for each test"""
        super().setup_method()
        # Use temporary directory for POET artifacts
        self.temp_dir = tempfile.mkdtemp()
        self.original_env = {}

        # Save and set environment variables for local mode
        for key in ["AITOMATIC_API_URL", "AITOMATIC_API_KEY"]:
            self.original_env[key] = os.environ.get(key)

        # Force local mode for testing
        os.environ["AITOMATIC_API_URL"] = "local"

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

    def test_dana_poet_basic_decorator(self):
        """Test basic @poet decorator in Dana code"""

        dana_code = """
# Basic POET decorator test
@poet(domain="test")
def simple_add(a: int, b: int) -> int:
    return a + b

# Execute the function
result = simple_add(2, 3)
log(f"Result: {result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

        # Check that POET-enhanced function was created
        context = execution_result.final_context
        assert context is not None
        simple_add_func = context.get("local.simple_add")
        assert simple_add_func is not None
        assert hasattr(simple_add_func, "__name__")

    def test_dana_poet_domain_decorator(self):
        """Test @poet decorator with domain parameter"""

        dana_code = """
# POET decorator with domain
@poet(domain="healthcare")
def analyze_vitals(heart_rate: int, temperature: float) -> dict:
    is_normal = heart_rate >= 60 and heart_rate <= 100 and temperature <= 99.5
    return {"is_normal": is_normal, "heart_rate": heart_rate, "temperature": temperature}

# Execute the function
result = analyze_vitals(75, 98.6)
log(f"Analysis result: {result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

    def test_dana_poet_training_decorator(self):
        """Test @poet decorator with training enabled"""

        dana_code = """
# POET decorator with domain
@poet(domain="text_classification")
def classify_text(text: str) -> str:
    text_lower = text.lower()
    if "good" in text_lower or "great" in text_lower:
        return "positive"
    elif "bad" in text_lower or "terrible" in text_lower:
        return "negative"
    else:
        return "neutral"

# Execute the function
result = classify_text("This is a great example")
log(f"Classification: {result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

    def test_dana_poet_with_feedback(self):
        """Test POET with feedback function in Dana"""

        dana_code = """
# POET function with domain
@poet(domain="prediction")
def predict_value(input_data: float) -> float:
    # Simple prediction logic
    return input_data * 1.5

# Execute function
result = predict_value(10.0)
log(f"Prediction result: {result}")

# Provide feedback
feedback(result, "The prediction was very accurate!")
log("Feedback submitted successfully")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

    def test_dana_poet_multiple_functions(self):
        """Test multiple POET functions in same Dana execution"""

        dana_code = """
# Multiple POET functions
@poet(domain="healthcare")
def check_blood_pressure(systolic: int, diastolic: int) -> str:
    if systolic >= 140 or diastolic >= 90:
        return "high"
    elif systolic <= 90 or diastolic <= 60:
        return "low"  
    else:
        return "normal"

@poet(domain="healthcare")
def calculate_bmi(weight: float, height: float) -> float:
    # BMI = weight(kg) / height(m)^2
    height_m = height / 100  # Convert cm to m
    return weight / (height_m * height_m)

# Test both functions
bp_result = check_blood_pressure(120, 80)
bmi_result = calculate_bmi(70.0, 175.0)

log(f"Blood pressure: {bp_result}")
log(f"BMI: {bmi_result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

    def test_dana_poet_error_handling(self):
        """Test POET error handling in Dana"""

        dana_code = """
# Test invalid domain (should still work with fallback)
@poet(domain="nonexistent_domain")  
def test_function(x: int) -> int:
    return x * 2

# This should still execute (fallback to original function)
result = test_function(5)
log(f"Result with invalid domain: {result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Should complete successfully even with invalid domain
        # (POET should fallback to original function)
        assert execution_result.success is True
        assert execution_result.error is None

    def test_dana_poet_parameter_validation(self):
        """Test POET parameter validation in Dana"""

        # Test invalid parameter name
        dana_code_invalid = """
@poet(invalid_param="test")
def test_function(x: int) -> int:
    return x * 2
"""

        # This should fail during execution
        execution_result = self._run_dana_code(dana_code_invalid)

        # Should fail due to invalid parameter
        assert execution_result.success is False
        assert "Unknown parameter" in str(execution_result.error)

    def test_dana_poet_with_complex_data_types(self):
        """Test POET with complex data types in Dana"""

        dana_code = """
# POET function with complex return type
@poet(domain="financial_services")
def analyze_portfolio(portfolio: list) -> dict:
    total_value = 0.0
    asset_count = len(portfolio)
    
    for asset in portfolio:
        total_value = total_value + asset
    
    if asset_count > 0:
        avg_value = total_value / asset_count
    else:
        avg_value = 0.0

    if avg_value > 1000:
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    return {
        "total_value": total_value,
        "asset_count": asset_count,
        "average_value": avg_value,
        "risk_level": risk_level
    }

# Test with sample portfolio
sample_portfolio = [1500.0, 2300.0, 850.0, 3200.0]
analysis = analyze_portfolio(sample_portfolio)

log(f"Portfolio analysis: {analysis}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

    def test_dana_poet_configuration_parameters(self):
        """Test various POET configuration parameters in Dana"""

        dana_code = """
# Test different configuration parameters
@poet(domain="manufacturing", timeout=45.0, retries=5)
def quality_check(measurement: float, tolerance: float) -> bool:
    return abs(measurement - 100.0) <= tolerance

# Test with custom timeout and retries
result = quality_check(98.5, 2.0)
log(f"Quality check result: {result}")

@poet(domain="performance")
def performance_metric(processing_time: float, error_rate: float) -> str:
    if processing_time < 1.0 and error_rate < 0.01:
        return "excellent"
    elif processing_time < 5.0 and error_rate < 0.05:
        return "good"
    else:
        return "needs_improvement"

# Test performance function
perf_result = performance_metric(0.5, 0.005)
log(f"Performance: {perf_result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None


class TestDanaPOETBuiltinFunctions(PoetTestBase):
    """Test POET built-in functions in Dana language"""

    def setup_method(self):
        """Setup for each test"""
        super().setup_method()

    def teardown_method(self):
        """Cleanup after each test"""
        super().teardown_method()

    def test_feedback_builtin_function(self):
        """Test feedback built-in function in Dana"""

        dana_code = """
# Create a POET function that returns a trackable result
@poet(domain="prediction")
def sample_prediction(value: float) -> float:
    return value * 2.0

# Execute and get result
result = sample_prediction(5.0)
log(f"Prediction: {result}")

# Test feedback with different formats
feedback(result, "Excellent prediction!")
feedback(result, {"rating": 5, "comment": "Very accurate"})  
feedback(result, 0.95)

log("All feedback submitted successfully")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Check execution completed successfully
        assert execution_result.success is True
        assert execution_result.error is None

    def test_poet_builtin_function(self):
        """Test poet built-in function (if available) in Dana"""

        # Note: This tests the poet() function if it exists as a built-in
        # Currently, POET is primarily a decorator, but this tests extensibility

        dana_code = """
# Test if poet function exists as built-in
log("Testing POET built-in function availability")

# Basic function without decorator
def basic_add(a: int, b: int) -> int:
    return a + b

# Test basic function
normal_result = basic_add(3, 4)
log(f"Normal function result: {normal_result}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Should complete successfully
        assert execution_result.success is True
        assert execution_result.error is None


class TestDanaPOETErrorScenarios(PoetTestBase):
    """Test POET error scenarios in Dana language"""

    def setup_method(self):
        """Setup for each test"""
        super().setup_method()

    def teardown_method(self):
        """Cleanup after each test"""
        super().teardown_method()

    def test_invalid_poet_parameters(self):
        """Test various invalid POET parameter scenarios"""

        # Test cases for different invalid parameters
        invalid_test_cases = [
            # Invalid parameter name
            """
@poet(invalid_parameter="test")
def test_func(): pass
""",
            # Invalid domain type
            """
@poet(domain=123)
def test_func(): pass
""",
            # Invalid timeout type
            """
@poet(timeout="not_a_number")
def test_func(): pass
""",
            # Invalid retries type
            """
@poet(retries="not_a_number")
def test_func(): pass
""",
            # Negative retries
            """
@poet(retries=-1)
def test_func(): pass
""",
        ]

        for i, invalid_code in enumerate(invalid_test_cases):
            execution_result = self._run_dana_code(invalid_code)

            # All these should result in errors
            assert execution_result.success is False, f"Test case {i} should have failed"
            assert execution_result.error is not None, f"Test case {i} should have an error message"

    def test_feedback_with_invalid_result(self):
        """Test feedback function with invalid result parameter"""

        dana_code = """
# Try to provide feedback on non-POET result
normal_value = 42
feedback(normal_value, "This should fail")
"""

        # Execute Dana code - this should fail
        execution_result = self._run_dana_code(dana_code)

        # Should fail because normal_value is not a POETResult
        assert execution_result.success is False
        assert execution_result.error is not None

    def test_poet_with_syntax_errors(self):
        """Test POET decorator with syntax errors in function"""

        dana_code = """
# POET decorator on function with syntax error
@poet(domain="test")
def broken_function(x: int) -> int:
    return x +  # Incomplete expression
"""

        # Execute Dana code - should fail due to syntax error
        execution_result = self._run_dana_code(dana_code)

        # Should fail due to syntax error
        assert execution_result.success is False
        assert execution_result.error is not None


class TestDanaPOETLifecycle(PoetTestBase):
    """Test POET lifecycle management in Dana"""

    def setup_method(self):
        """Setup for each test"""
        super().setup_method()

    def teardown_method(self):
        """Cleanup after each test"""
        super().teardown_method()

    def test_poet_automatic_lifecycle(self):
        """Test POET automatic lifecycle management"""

        dana_code = """
# Test that POET works without explicit setup
@poet(domain="test")
def lifecycle_test(value: int) -> int:
    return value * 3

# Should work automatically
result = lifecycle_test(10)
log(f"Lifecycle test result: {result}")

# Verify the result has POET metadata
execution_id = result._poet["execution_id"]
function_name = result._poet["function_name"]
enhanced = result._poet["enhanced"]

log(f"Execution ID: {execution_id}")
log(f"Function name: {function_name}")
log(f"Enhanced: {enhanced}")
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Should complete successfully with automatic lifecycle
        assert execution_result.success is True
        assert execution_result.error is None

    def test_multiple_poet_executions(self):
        """Test multiple POET function executions in sequence"""

        dana_code = """
# Multiple POET functions called in sequence
@poet(domain="llm_optimization")
def process_text(text: str) -> str:
    return text.upper()

@poet(domain="sentiment")
def analyze_sentiment(text: str) -> str:
    if "good" in text.lower():
        return "positive"
    else:
        return "neutral"

# Execute multiple times
result1 = process_text("hello world")
result2 = analyze_sentiment("This is good")
result3 = process_text("another test")

log(f"Text processing: {result1}")
log(f"Sentiment: {result2}")
log(f"More processing: {result3}")

# Provide feedback on different results
feedback(result1, "Text processing worked well")
feedback(result2, {"sentiment_accuracy": 0.9})
"""

        # Execute Dana code
        execution_result = self._run_dana_code(dana_code)

        # Should handle multiple executions successfully
        assert execution_result.success is True
        assert execution_result.error is None
