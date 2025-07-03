#!/usr/bin/env python3
"""
Tutorial 06: DANA Function Pipelines Guide
==========================================

Learn how to use DANA's powerful pipeline system from Python.
Perfect for AI Engineers who need data transformation workflows.

📖 What You'll Learn:
- Create function pipelines with | operator
- Chain data transformations seamlessly
- Build reusable processing workflows
- Combine AI reasoning with data pipelines

⚡ Quick Start: Run this file to see pipelines in action!
"""

import sys
from pathlib import Path

# Add the OpenDXA path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from opendxa.dana import dana


def demo_basic_pipeline():
    """Demo 1: Simple data pipeline with transformations."""
    print("📋 Demo 1: Basic Data Pipeline")
    print("-" * 40)

    dana.enable_module_imports()
    try:
        import pipelines

        # ✅ Simple text processing pipeline
        text = "  hello WORLD from dana  "
        result = pipelines.process_text(text)
        print(f"📝 Input text: '{text}'")
        print(f"✨ Pipeline result: '{result}'")

        # ✅ Show each step of the pipeline
        print("\n🔧 Pipeline steps:")
        print(f"   1. Trim: '{text.strip()}'")
        print(f"   2. Clean: '{text.strip().lower()}'")
        print(f"   3. Title: '{text.strip().lower().title()}'")
        print(f"   4. Final: '{result}'")

    finally:
        dana.disable_module_imports()

    print("✅ Basic pipeline works perfectly!\n")


def benefits_explanation():
    """Explain why DANA pipelines are valuable for AI Engineers."""
    print("💡 Why DANA Pipelines Matter for AI Engineers")
    print("-" * 50)

    print("""
🎯 Key Benefits:

1. **Readable Code**: Data flows left-to-right
   - data | clean | analyze | format
   - Easy to understand transformation steps
   - Self-documenting data workflows

2. **Reusable Components**: Build once, use everywhere
   - Create pipeline functions
   - Combine in different ways
   - Share across projects

    """)


def quick_reference():
    """Quick reference for common pipeline patterns."""
    print("📚 Quick Reference")
    print("-" * 20)

    print("""
🔧 Common Pipeline Patterns:

# Simple data pipeline
result = data | clean | transform | format
    """)


def main():
    """Run the complete function pipelines tutorial."""
    print("🔗 DANA Function Pipelines Tutorial")
    print("=" * 50)
    print("Learn how to build data workflows with pipelines\n")

    # Run demos
    demo_basic_pipeline()
    benefits_explanation()
    quick_reference()

    print("🎉 Tutorial Complete!")
    print("\n📖 What You Learned:")
    print("  ✅ Creating data pipelines with | operator")
    print("  ✅ Chaining transformations seamlessly")

    print("\n🔗 Next Steps:")
    print("  📝 Build your own data processing pipelines")
    print("  🧠 Combine AI reasoning with data transformations")


if __name__ == "__main__":
    main()
