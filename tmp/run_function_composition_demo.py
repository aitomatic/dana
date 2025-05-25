#!/usr/bin/env python3
"""
Dana Function Composition Demo Runner

This script executes the Dana function composition demo written in native Dana syntax.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.common.exceptions import DanaError
from opendxa.dana.exec.repl.repl import REPL


def run_dana_demo():
    """Run the Dana function composition demo."""
    print("🚀 Running Dana Function Composition Demo")
    print("=" * 50)

    # Read the Dana demo file
    demo_file = Path(__file__).parent / "function_composition_demo_simple.na"

    if not demo_file.exists():
        print(f"❌ Demo file not found: {demo_file}")
        return

    try:
        # Read the Dana code
        with open(demo_file) as f:
            program_source = f.read()

        print(f"📝 Loaded program source ({len(program_source)} bytes)")

        # Create REPL with LLM resource (optional)
        try:
            llm_resource = LLMResource()
            repl = REPL(llm_resource=llm_resource)
            print("🔧 Created REPL with LLM resource")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize LLM resource: {e}")
            repl = REPL()
            print("🔧 Created REPL without LLM resource")

        # Execute the program using REPL
        print("🚀 Executing program...")
        print("-" * 50)

        result = repl.execute(program_source)

        print("-" * 50)
        print("✅ Program executed successfully")

        # Show final result if available
        if result is not None:
            print(f"\n📊 Final result: {result}")

        print("\n🎉 Function Composition Demo completed successfully!")

    except DanaError as e:
        print(f"❌ Dana Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error executing Dana demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = run_dana_demo()
    sys.exit(exit_code)
