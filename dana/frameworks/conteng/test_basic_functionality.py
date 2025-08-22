#!/usr/bin/env python3
"""
Basic functionality test for Context Engineering framework

This is a minimal test harness to verify the core components work together.
Run with: python test_basic_functionality.py
"""

import sys
import traceback


def test_imports():
    """Test that all core modules can be imported"""
    print("Testing imports...")

    try:
        from dana.frameworks.conteng import (
            ContextTemplate,
            ContextInstance,
            ContextSpec,
            ContextArchitect,
            RuntimeContextOptimizer,
            DomainRegistry,
            KnowledgeAsset,
            ConEngIntegration,
            SimpleTokenizer,
            FinancialTokenizer,
        )

        print("✓ All core imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_tokenizer():
    """Test tokenizer functionality"""
    print("\nTesting tokenizer...")

    try:
        from dana.frameworks.conteng.tokenizer import SimpleTokenizer, FinancialTokenizer, count_tokens

        # Test basic tokenizer
        tokenizer = SimpleTokenizer()
        text = "Hello world, this is a test with 123 numbers!"
        tokens = tokenizer.count_tokens(text)
        print(f"✓ Basic tokenizer: '{text}' -> {tokens} tokens")

        # Test financial tokenizer
        fin_tokenizer = FinancialTokenizer()
        fin_text = "Calculate the VaR using Monte Carlo simulation for the portfolio"
        fin_tokens = fin_tokenizer.count_tokens(fin_text)
        print(f"✓ Financial tokenizer: '{fin_text}' -> {fin_tokens} tokens")

        # Test convenience functions
        tokens_conv = count_tokens("Test convenience function", "default")
        print(f"✓ Convenience function: {tokens_conv} tokens")

        return True
    except Exception as e:
        print(f"✗ Tokenizer test failed: {e}")
        traceback.print_exc()
        return False


def test_registry():
    """Test domain registry functionality"""
    print("\nTesting registry...")

    try:
        from dana.frameworks.conteng.registry import DomainRegistry, KnowledgeAsset

        # Create registry
        registry = DomainRegistry()

        # Create knowledge asset
        asset = KnowledgeAsset(
            domain="test",
            name="test_asset",
            version="1.0",
            tasks=["testing"],
            content="This is test knowledge content for validation.",
            source="test_harness",
            trust_score=0.9,
            age_days=1,
        )

        # Register asset
        registry.register_knowledge_asset(asset)
        print("✓ Knowledge asset registered")

        # Query assets
        assets = registry.get_knowledge_assets(domain="test")
        print(f"✓ Retrieved {len(assets)} assets from test domain")

        return len(assets) > 0
    except Exception as e:
        print(f"✗ Registry test failed: {e}")
        traceback.print_exc()
        return False


def test_templates():
    """Test context template creation"""
    print("\nTesting templates...")

    try:
        from dana.frameworks.conteng.templates import ContextTemplate, KnowledgeSelector, TokenBudget

        # Create token budget
        budget = TokenBudget(total=2000)
        budget.set_tokenizer("default")
        print(f"✓ Token budget created: {budget.total} total tokens")

        # Create knowledge selector
        selector = KnowledgeSelector(domain="test", trust_threshold=0.7, max_assets=5)
        print("✓ Knowledge selector created")

        # Create template
        template = ContextTemplate(
            name="test_template",
            version="1.0",
            domain="test",
            task="testing context engineering",
            knowledge_selector=selector,
            token_budget=budget,
            instructions_template="You are a test assistant for context engineering validation.",
        )

        print(f"✓ Template created: {template.name} (signature: {template.signature})")
        return True
    except Exception as e:
        print(f"✗ Template test failed: {e}")
        traceback.print_exc()
        return False


def test_architect():
    """Test context architect functionality"""
    print("\nTesting architect...")

    try:
        from dana.frameworks.conteng.registry import DomainRegistry
        from dana.frameworks.conteng.architect import ContextArchitect

        # Create registry with test data
        registry = DomainRegistry()

        # Create architect
        architect = ContextArchitect(registry)

        # Test cache stats
        stats = architect.get_cache_stats()
        print(f"✓ Architect created, cache has {stats['total_entries']} entries")

        return True
    except Exception as e:
        print(f"✗ Architect test failed: {e}")
        traceback.print_exc()
        return False


def test_finance_domain():
    """Test finance domain pack"""
    print("\nTesting finance domain pack...")

    try:
        from dana.frameworks.conteng.domain_packs.finance import FinanceDomainPack, FinanceContextConfig, FinanceSpecialization

        # Create domain pack
        finance_pack = FinanceDomainPack()
        print("✓ Finance domain pack created")

        # Create config
        config = FinanceContextConfig(
            specialization=FinanceSpecialization.RISK_MANAGEMENT,
            regulatory_framework="US",
            risk_tolerance="moderate",
            compliance_level="enhanced",
            market_focus=["equity", "fixed_income"],
        )
        print("✓ Finance config created")

        # Get context template
        template = finance_pack.get_context_template("plan", config)
        print(f"✓ Finance template created: {template.name}")

        return True
    except Exception as e:
        print(f"✗ Finance domain test failed: {e}")
        traceback.print_exc()
        return False


def test_integration():
    """Test integration functionality"""
    print("\nTesting integration...")

    try:
        from dana.frameworks.conteng.integration import ConEngIntegration, AgentContextConfig

        # Create integration
        integration = ConEngIntegration()
        print("✓ Integration created")

        # Test enable/disable
        integration.disable()
        integration.enable()
        print("✓ Enable/disable works")

        # Create agent config
        AgentContextConfig(agent_type="TestAgent", domain="test", specialization="testing")
        print("✓ Agent config created")

        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("Dana Context Engineering - Basic Functionality Test")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Tokenizer", test_tokenizer),
        ("Registry", test_registry),
        ("Templates", test_templates),
        ("Architect", test_architect),
        ("Finance Domain", test_finance_domain),
        ("Integration", test_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} test crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 50)
    print("Test Results:")
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:15} {status}")
        if result:
            passed += 1

    print(f"\nPassed: {passed}/{len(results)} tests")

    if passed == len(results):
        print("🎉 All tests passed! Context Engineering framework is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
