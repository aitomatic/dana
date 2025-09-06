#!/usr/bin/env python3
"""
Advanced Tutorial 02: Modular Architecture with Nested Imports in Dana

Learn how to build scalable Dana applications using modular architecture.
Demonstrates nested imports, module composition, and workflow orchestration.

Prerequisites: Advanced Tutorial 01
Difficulty: ⭐⭐⭐⭐ Expert
Duration: 10-15 minutes
"""

import sys
from pathlib import Path

# Add the Dana path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dana.dana import dana


def demo_simple_import():
    """Demonstrate basic Dana module importing."""
    print("🔗 BASIC MODULE IMPORTING")
    print("=" * 40)

    dana.enable_module_imports()

    try:
        # Import a simple Dana module
        import risk_calculator  # Dana module for risk calculations

        print("✅ Successfully imported risk_calculator.na")
        print("📄 Module contains financial risk calculation functions")

        # Prepare order data as expected by the Dana function
        order_data = {"order_amount": 15000, "shipping_country": "Nigeria", "payment_method": "credit_card"}

        print("📊 Calculating risk for order:")
        print(f"   Amount: ${order_data['order_amount']:,}")
        print(f"   Country: {order_data['shipping_country']}")
        print(f"   Payment: {order_data['payment_method']}")

        # Use the imported module with correct function name and parameter
        risk_score = risk_calculator.calculate_risk_score(order_data)
        print(f"🎯 Calculated risk score: {risk_score}/100")

        # Interpret the risk level
        if risk_score >= 70:
            risk_level = "🔴 HIGH RISK"
        elif risk_score >= 40:
            risk_level = "🟡 MEDIUM RISK"
        else:
            risk_level = "🟢 LOW RISK"

        print(f"📈 Risk Assessment: {risk_level}")

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        dana.disable_module_imports()


def demo_nested_architecture():
    """Demonstrate nested module architecture."""
    print("\n🏗️  NESTED ARCHITECTURE PATTERN")
    print("=" * 40)

    # Sample order data for processing
    order_data = {
        "customer_id": "CUST_12345",
        "order_amount": 15000,
        "payment_method": "credit_card",
        "shipping_country": "Nigeria",
        "items": [{"product": "laptop", "quantity": 10, "unit_price": 1200}, {"product": "accessories", "quantity": 5, "unit_price": 600}],
    }

    print("📦 Processing complex order:")
    print(f"   💰 Amount: ${order_data['order_amount']:,}")
    print(f"   🌍 Country: {order_data['shipping_country']}")
    print(f"   📱 Payment: {order_data['payment_method']}")

    dana.enable_module_imports()

    try:
        # Import the orchestrator (which imports other modules)
        import workflow_orchestrator

        print("\n🤖 Dana workflow orchestration:")
        print("   📄 workflow_orchestrator.na (main)")
        print("   ├── 📄 fraud_detector.na")
        print("   ├── 📄 shipping_analyzer.na")
        print("   └── 📄 risk_calculator.na")

        # Process order using nested module architecture
        result = workflow_orchestrator.process_order(order_data)

        print("\n📊 Processing Results:")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Fraud Risk: {result.get('fraud_risk', 'Not assessed')}")
        print(f"   Shipping: {result.get('shipping_decision', 'Not determined')}")

        if result.get("recommendations"):
            print(f"   💡 Recommendations: {result.get('recommendations')}")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
    finally:
        dana.disable_module_imports()


def demo_architecture_benefits():
    """Explain the benefits of modular architecture."""
    print("\n🎯 MODULAR ARCHITECTURE BENEFITS")
    print("=" * 40)

    benefits = [
        "🔄 Reusability: Modules can be reused across projects",
        "🧪 Testability: Each module can be tested independently",
        "👥 Collaboration: Teams can work on different modules",
        "📈 Scalability: Add new modules without breaking existing ones",
        "🛠️  Maintainability: Easier to debug and update specific features",
    ]

    print("Why use modular Dana architecture?\n")
    for benefit in benefits:
        print(f"   {benefit}")


def main():
    """Run modular architecture demonstrations."""
    print("🚀 ADVANCED TUTORIAL 02: Modular Architecture")
    print("=" * 60)
    print("Build scalable Dana applications with nested imports")
    print()

    try:
        demo_simple_import()
        demo_nested_architecture()
        demo_architecture_benefits()

        print("\n" + "=" * 60)
        print("✅ Tutorial Complete!")
        print("\n💡 Key Learnings:")
        print("   • Use dana.enable_module_imports() for Dana module access")
        print("   • Organize complex workflows with nested module imports")
        print("   • Design modules for reusability and maintainability")
        print("   • Always disable imports when done: dana.disable_module_imports()")
        print("\n🎯 Next: Master advanced caching and optimization")

    except Exception as e:
        print(f"❌ Tutorial failed: {e}")
        raise


if __name__ == "__main__":
    main()
