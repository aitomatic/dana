"""
Tests for LLM-powered POET transpiler
"""

import pytest
from pathlib import Path
import shutil
from unittest.mock import Mock, patch

from opendxa.dana.poet import poet
from opendxa.dana.poet.transpiler_llm import POETTranspilerLLM
from opendxa.dana.poet.types import POETConfig


class TestLLMTranspiler:
    """Test LLM-powered code generation"""

    def setup_method(self):
        """Clean up any existing .dana directories"""
        poet_dir = Path(".dana/poet")
        if poet_dir.exists():
            shutil.rmtree(poet_dir.parent)

    def teardown_method(self):
        """Clean up after tests"""
        poet_dir = Path(".dana/poet")
        if poet_dir.exists():
            shutil.rmtree(poet_dir.parent)

    def test_llm_transpiler_context_extraction(self):
        """Test that LLM transpiler extracts rich context"""
        transpiler = POETTranspilerLLM()

        def calculate_compound_interest(principal: float, rate: float, years: int) -> float:
            """Calculate compound interest for investment."""
            return principal * (1 + rate) ** years

        config = POETConfig(domain="financial", optimize_for="accuracy")

        # Mock the LLM to test prompt building
        with patch.object(transpiler, "llm") as mock_llm:
            mock_response = {"choices": [{"message": {"content": "# Generated Dana code would go here"}}]}
            mock_llm.query_sync.return_value = mock_response

            result = transpiler.transpile(calculate_compound_interest, config)

            # Verify LLM was called
            assert mock_llm.query_sync.called

            # Check the prompt includes function details
            call_args = mock_llm.query_sync.call_args[0][0]
            messages = call_args["messages"]
            user_prompt = messages[1]["content"]

            assert "calculate_compound_interest" in user_prompt
            assert "Calculate compound interest for investment" in user_prompt
            assert "financial" in user_prompt
            assert "principal: float, rate: float, years: int" in user_prompt

    def test_llm_domain_specific_prompts(self):
        """Test that different domains get different prompts"""
        transpiler = POETTranspilerLLM()
        
        # Financial domain - check for general domain analysis
        financial_prompt = transpiler._get_domain_instructions("financial")
        assert "Analyze the function's purpose" in financial_prompt
        assert "bulletproof" in financial_prompt
        
        # ML monitoring domain
        ml_prompt = transpiler._get_domain_instructions("ml_monitoring")
        assert "drift" in ml_prompt
        assert "statistical tests" in ml_prompt
        
        # API domain - check for general domain analysis
        api_prompt = transpiler._get_domain_instructions("api")
        assert "Analyze the function's purpose" in api_prompt
        assert "bulletproof" in api_prompt

    @patch("opendxa.dana.poet.transpiler_llm.LLMResource")
    def test_poet_decorator_with_llm(self, mock_llm_class):
        """Test POET decorator using LLM generation"""
        # Mock the LLM to return valid Dana code
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm

        dana_code = """
struct POETState {
    inputs: dict
    perceive_result: dict
    operate_result: dict
    enforce_result: dict
    errors: list[string]
}

def perceive(amount: float, rate: float, state: POETState) -> POETState {
    if amount <= 0 {
        state.errors.append("Amount must be positive")
    }
    if rate < 0 or rate > 1 {
        state.errors.append("Rate must be between 0 and 1")
    }
    state.perceive_result = {"valid": len(state.errors) == 0}
    return state
}

def operate(amount: float, rate: float, state: POETState) -> POETState {
    if state.perceive_result["valid"] {
        result = amount * rate
        state.operate_result = {"success": true, "value": result}
    }
    return state
}

def enforce(state: POETState) -> POETState {
    state.enforce_result = {
        "valid": state.operate_result.get("success", false),
        "final_value": state.operate_result.get("value", null)
    }
    return state
}

def enhanced_calculate_fee(amount: float, rate: float) -> float {
    state = POETState(
        inputs={"amount": amount, "rate": rate},
        perceive_result={},
        operate_result={},
        enforce_result={},
        errors=[]
    )
    
    state = perceive(amount, rate, state)
    state = operate(amount, rate, state)
    state = enforce(state)
    
    if not state.enforce_result["valid"] {
        raise ValueError(f"POET validation failed: {state.errors}")
    }
    
    return state.enforce_result["final_value"]
}
"""

        mock_llm.query_sync.return_value = {"choices": [{"message": {"content": dana_code}}]}

        @poet(domain="financial", use_llm=True)
        def calculate_fee(amount: float, rate: float) -> float:
            """Calculate transaction fee."""
            return amount * rate

        # Check that enhanced file was created
        enhanced_path = Path(".dana/poet/calculate_fee.na")
        assert enhanced_path.exists()

        # Verify LLM was called
        assert mock_llm.query_sync.called

        # Check generated content
        content = enhanced_path.read_text()
        assert "perceive" in content
        assert "Amount must be positive" in content
        assert "Rate must be between 0 and 1" in content

    def test_llm_understands_business_logic(self):
        """Test that LLM understands implicit business rules"""
        transpiler = POETTranspilerLLM()

        # Create a mock that simulates intelligent LLM understanding
        with patch.object(transpiler, "llm") as mock_llm:
            # Simulate LLM understanding this is a discount calculation
            mock_llm.query_sync.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": """
def perceive(price: float, discount_percent: float, state: POETState) -> POETState {
    # LLM understands this is a discount calculation
    if price <= 0 {
        state.errors.append("Price must be positive")
    }
    if discount_percent < 0 {
        state.errors.append("Discount cannot be negative")
    }
    if discount_percent > 100 {
        state.errors.append("Discount cannot exceed 100%")
    }
    if discount_percent > 50 {
        state.warnings.append("Large discount applied - may need approval")
    }
    return state
}
"""
                        }
                    }
                ]
            }

            def calculate_discount(price: float, discount_percent: float) -> float:
                """Apply discount to price."""
                return price * (1 - discount_percent / 100)

            config = POETConfig(domain="financial")
            result = transpiler.transpile(calculate_discount, config)

            # LLM should understand percentage constraints
            assert "cannot exceed 100%" in result
            assert "Large discount" in result

    def test_llm_fallback_on_error(self):
        """Test fallback to template transpiler on LLM error"""

        @poet(domain="computation", use_llm=True, fallback_strategy="original")
        def divide(a: float, b: float) -> float:
            return a / b

        # Even if LLM fails, function should still work
        result = divide(10, 2)
        assert result == 5.0

    def test_different_domains_generate_different_code(self):
        """Test that same function gets different enhancements per domain"""
        transpiler = POETTranspilerLLM()

        def fetch_data(key: str) -> dict:
            """Fetch data by key."""
            return {"key": key, "data": "value"}

        # Mock different responses for different domains
        with patch.object(transpiler, "llm") as mock_llm:
            # API domain should add caching
            api_config = POETConfig(domain="api")
            mock_llm.query_sync.return_value = {"choices": [{"message": {"content": "# Code with caching logic"}}]}
            api_result = transpiler.transpile(fetch_data, api_config)

            # Database domain should add connection pooling
            db_config = POETConfig(domain="database")
            mock_llm.query_sync.return_value = {"choices": [{"message": {"content": "# Code with connection pooling"}}]}
            db_result = transpiler.transpile(fetch_data, db_config)

            # Results should be different
            assert api_result != db_result


class TestLLMGenerationQuality:
    """Test the quality of LLM-generated enhancements"""

    @pytest.mark.skipif(
        not Path(".env").exists() or "OPENAI_API_KEY" not in open(".env").read(), reason="Requires API keys for live LLM testing"
    )
    def test_live_llm_generation(self):
        """Test with actual LLM (requires API key)"""

        @poet(domain="financial", use_llm=True)
        def calculate_loan_payment(principal: float, rate: float, months: int) -> float:
            """Calculate monthly loan payment using amortization formula."""
            monthly_rate = rate / 12 / 100
            return principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)

        # Check generated file
        enhanced_path = Path(".dana/poet/calculate_loan_payment.na")
        assert enhanced_path.exists()

        content = enhanced_path.read_text()

        # LLM should understand this is a loan calculation
        assert "principal must be positive" in content.lower() or "principal <= 0" in content
        assert "months" in content.lower()
        assert "rate" in content.lower()

        # Should have all phases
        assert "def perceive" in content
        assert "def operate" in content
        assert "def enforce" in content
        assert "def enhanced_calculate_loan_payment" in content
