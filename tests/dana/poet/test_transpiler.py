"""
Unit tests for POET transpiler implementation.

Tests the real P→O→E phase generation for mathematical operations domain.
"""

import ast

import pytest

from opendxa.dana.poet.errors import POETTranspilationError
from opendxa.dana.poet.transpiler import PoetTranspiler
from opendxa.dana.poet.types import POETConfig


class TestPoetTranspiler:
    """Test POET transpiler functionality."""
    
    @pytest.fixture
    def transpiler(self):
        """Create a transpiler instance."""
        return PoetTranspiler()
    
    @pytest.fixture
    def safe_divide_code(self):
        """Sample function with POET decorator."""
        return '''
@poet(domain="mathematical_operations", retries=2)
def safe_divide(a: float, b: float) -> float:
    """Safely divide two numbers."""
    return a / b
'''
    
    def test_transpiler_instantiation(self, transpiler):
        """Test that transpiler can be instantiated with domain registry."""
        assert transpiler is not None
        assert transpiler.domain_registry is not None
        assert transpiler.domain_registry.has_domain("mathematical_operations")
        assert transpiler.domain_registry.has_domain("computation")
    
    def test_validate_function_code_success(self, transpiler, safe_divide_code):
        """Test successful validation of POET decorated function."""
        func_name, code = transpiler._validate_function_code(safe_divide_code)
        assert func_name == "safe_divide"
        assert "@poet" in code
    
    def test_validate_function_code_missing_decorator(self, transpiler):
        """Test validation fails without @poet decorator."""
        code = '''
def safe_divide(a: float, b: float) -> float:
    return a / b
'''
        with pytest.raises(POETTranspilationError, match="Missing @poet decorator"):
            transpiler._validate_function_code(code)
    
    def test_validate_function_code_no_function(self, transpiler):
        """Test validation fails without function definition."""
        code = '''
@poet(domain="test")
x = 5
'''
        with pytest.raises(POETTranspilationError, match="No function definition found"):
            transpiler._validate_function_code(code)
    
    def test_validate_function_code_syntax_error(self, transpiler):
        """Test validation fails with syntax error."""
        code = '''
@poet(domain="test")
def bad_func(
'''
        with pytest.raises(POETTranspilationError, match="Invalid Python code"):
            transpiler._validate_function_code(code)
    
    def test_transpile_mathematical_operations(self, transpiler, safe_divide_code):
        """Test full transpilation for mathematical operations domain."""
        config = POETConfig(
            domain="mathematical_operations",
            retries=2,
            timeout=30.0,
            enable_monitoring=True
        )
        
        result = transpiler.transpile(safe_divide_code, config)
        
        # Check result structure
        assert "enhanced_code" in result
        assert "metadata" in result
        assert result["language"] == "dana"
        
        # Check metadata
        metadata = result["metadata"]
        assert metadata["function_name"] == "safe_divide"
        assert metadata["domain"] == "mathematical_operations"
        assert metadata["retries"] == 2
        
        # Check enhanced code contains P→O→E phases
        enhanced = result["enhanced_code"]
        assert "PERCEIVE PHASE" in enhanced
        assert "OPERATE PHASE" in enhanced
        assert "ENFORCE PHASE" in enhanced
        
        # Check for mathematical domain specifics
        assert "Division by zero" in enhanced or "cannot be zero" in enhanced
        assert "isinstance" in enhanced  # Type checking
        assert "math.isnan" in enhanced  # NaN checking
        assert "math.isinf" in enhanced  # Infinity checking
        assert "retry" in enhanced.lower()  # Retry logic
    
    def test_transpile_with_training(self, transpiler):
        """Test transpilation with training enabled."""
        code = '''
@poet(domain="computation", optimize_for="accuracy")
def calculate(x: float) -> float:
    return x * 2
'''
        config = POETConfig(
            domain="computation",
            optimize_for="accuracy",
            enable_training=True
        )
        
        result = transpiler.transpile(code, config)
        
        assert "train_code" in result
        assert result["train_code"] is not None
        assert "train_calculate" in result["train_code"]
        assert "feedback_data" in result["train_code"]
    
    def test_extract_function_info(self, transpiler):
        """Test function information extraction."""
        code = '''
@poet(domain="test")
def test_func(x: int, y: float = 1.0) -> str:
    """Test function."""
    return str(x + y)
'''
        tree = ast.parse(code)
        func_def = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
        config = POETConfig(domain="test")
        
        func_info = transpiler._extract_function_info(func_def, code, config)
        
        assert func_info.name == "test_func"
        assert func_info.domain == "test"
        assert func_info.retries == 3  # Default
        assert func_info.annotations["x"] == "int"
        assert func_info.annotations["y"] == "float"
        assert func_info.annotations["return"] == "str"
        assert func_info.docstring == "Test function."
    
    def test_transpile_different_domains(self, transpiler):
        """Test transpilation works with different domains."""
        code_template = '''
@poet(domain="{domain}")
def test_func(x: float) -> float:
    return x * 2
'''
        
        for domain in ["computation", "mathematical_operations"]:
            config = POETConfig(domain=domain)
            code = code_template.format(domain=domain)
            
            result = transpiler.transpile(code, config)
            
            assert result["metadata"]["domain"] == domain
            assert "enhanced_code" in result
            assert len(result["enhanced_code"]) > 100  # Non-trivial enhancement
    
    def test_parameter_extraction(self, transpiler):
        """Test parameter name extraction from signature."""
        test_cases = [
            ("a: float, b: float", ["a", "b"]),
            ("x: int, y: int = 5", ["x", "y"]),
            ("name: str, *args, **kwargs", ["name"]),
            ("", []),
        ]
        
        for params_str, expected in test_cases:
            result = transpiler._extract_param_names(params_str)
            assert result == expected
    
    def test_division_by_zero_detection(self, transpiler, safe_divide_code):
        """Test that division by zero is properly detected in Perceive phase."""
        config = POETConfig(domain="mathematical_operations")
        result = transpiler.transpile(safe_divide_code, config)
        
        enhanced = result["enhanced_code"]
        
        # Should have division by zero check for parameter 'b'
        assert "'b' == param_name" in enhanced or "parameter 'b' cannot be zero" in enhanced
        
        # Should be in the Perceive phase specifically
        perceive_start = enhanced.find("PERCEIVE PHASE")
        operate_start = enhanced.find("OPERATE PHASE")
        div_check = enhanced.find("Division by zero")
        
        assert perceive_start < div_check < operate_start, "Division check should be in Perceive phase"