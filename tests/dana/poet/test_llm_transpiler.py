"""
Tests for POET Dana-to-Dana enhancement system.

This module tests the POET enhancement functionality for Dana code.
"""

from pathlib import Path

import pytest

from opendxa.dana.poet.enhancer import POETEnhancer
from opendxa.dana.poet.types import POETConfig


class TestPOETEnhancement:
    """Test POET Dana-to-Dana enhancement functionality."""

    def setup_method(self):
        """Clean up any existing test files"""
        dana_dir = Path("dana")
        if dana_dir.exists():
            for file in dana_dir.glob("*_enhanced.na"):
                file.unlink()

    def teardown_method(self):
        """Clean up after tests"""
        dana_dir = Path("dana")
        if dana_dir.exists():
            for file in dana_dir.glob("*_enhanced.na"):
                file.unlink()

    def test_basic_enhancement(self):
        """Test basic POET enhancement of Dana code."""
        enhancer = POETEnhancer()

        dana_code = """
def calculate_compound_interest(principal: float, rate: float, years: int) -> float:
    return principal * (1 + rate) ** years
"""

        config = POETConfig(domain="financial", optimize_for="accuracy")
        enhanced_code = enhancer.enhance(dana_code, config)

        # Should return enhanced code
        assert isinstance(enhanced_code, str)
        assert len(enhanced_code) > len(dana_code)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhancement_with_different_domains(self):
        """Test enhancement with different domain configurations."""
        enhancer = POETEnhancer()

        dana_code = """
def calculate_fee(amount: float, rate: float) -> float:
    return amount * rate
"""

        domains = ["financial", "api", "ml_monitoring"]

        for domain in domains:
            config = POETConfig(domain=domain)
            enhanced_code = enhancer.enhance(dana_code, config)

            assert isinstance(enhanced_code, str)
            assert "# POET-enhanced Dana code" in enhanced_code
            assert dana_code.strip() in enhanced_code

    def test_enhancement_with_complex_structures(self):
        """Test enhancement with complex Dana code structures."""
        enhancer = POETEnhancer()

        dana_code = """
struct POETState:
    inputs: dict
    perceive_result: dict
    operate_result: dict
    enforce_result: dict
    errors: list

def perceive(amount: float, rate: float, state: POETState) -> POETState:
    if amount <= 0:
        state.errors.append("Amount must be positive")
    if rate < 0 or rate > 1:
        state.errors.append("Rate must be between 0 and 1")
    state.perceive_result = {"valid": len(state.errors) == 0}
    return state

def operate(amount: float, rate: float, state: POETState) -> POETState:
    if state.perceive_result["valid"]:
        result = amount * rate
        state.operate_result = {"success": true, "value": result}
    return state

def enforce(state: POETState) -> POETState:
    state.enforce_result = {
        "valid": state.operate_result.get("success", false),
        "final_value": state.operate_result.get("value", null)
    }
    return state
"""

        config = POETConfig(domain="financial")
        enhanced_code = enhancer.enhance(dana_code, config)

        # Should handle complex code without errors
        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhancement_error_handling(self):
        """Test error handling for invalid Dana code."""
        enhancer = POETEnhancer()

        invalid_dana_code = """
def invalid_function(x: int) -> int {
    return x + 1
}
"""

        config = POETConfig(domain="test")

        # Should raise error for invalid Dana code
        with pytest.raises(RuntimeError, match="Invalid Dana code"):
            enhancer.enhance(invalid_dana_code, config)

    def test_enhancement_consistency(self):
        """Test that enhancement is consistent for the same input."""
        enhancer = POETEnhancer()

        dana_code = """
def discount_calculation(price: float, discount_percent: float) -> float:
    return price * (1 - discount_percent / 100)
"""

        config = POETConfig(domain="financial", retries=3)

        # Enhance the same code multiple times
        enhanced1 = enhancer.enhance(dana_code, config)
        enhanced2 = enhancer.enhance(dana_code, config)

        # Should be consistent
        assert enhanced1 == enhanced2
        assert isinstance(enhanced1, str)
        assert "# POET-enhanced Dana code" in enhanced1

    def test_enhancement_with_training_enabled(self):
        """Test enhancement with training enabled."""
        enhancer = POETEnhancer()

        dana_code = """
def loan_payment_calculation(principal: float, rate: float, months: int) -> float:
    monthly_rate = rate / 12
    return principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
"""

        config = POETConfig(domain="financial", optimize_for="accuracy", enable_training=True)

        enhanced_code = enhancer.enhance(dana_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhancement_with_monitoring_enabled(self):
        """Test enhancement with monitoring enabled."""
        enhancer = POETEnhancer()

        dana_code = """
def data_validation(input_data: dict) -> bool:
    return len(input_data) > 0
"""

        config = POETConfig(domain="ml_monitoring", enable_monitoring=True)

        enhanced_code = enhancer.enhance(dana_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code

    def test_enhancement_with_timeout_configuration(self):
        """Test enhancement with timeout configuration."""
        enhancer = POETEnhancer()

        dana_code = """
def api_call(endpoint: string, data: dict) -> dict:
    return {"status": "success", "data": data}
"""

        config = POETConfig(domain="api", timeout=30.0, retries=2)

        enhanced_code = enhancer.enhance(dana_code, config)

        assert isinstance(enhanced_code, str)
        assert "# POET-enhanced Dana code" in enhanced_code
        assert dana_code.strip() in enhanced_code
