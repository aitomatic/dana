#!/usr/bin/env python3
"""
Tutorial 05: DANA Data Structures Guide
========================================

Learn how to work with DANA's struct system from Python.
Perfect for AI Engineers who need structured data in their applications.

📖 What You'll Learn:
- Create and use DANA structs from Python
- Access struct fields with dot notation
- Build complex data models
- Type safety benefits

⚡ Quick Start: Run this file to see structs in action!
"""

import sys
from pathlib import Path

# Add the Dana path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dana.dana import dana


def demo_basic_structs():
    """Demo 1: Basic struct creation and field access."""
    print("📋 Demo 1: Basic Struct Operations")
    print("-" * 40)

    dana.enable_module_imports()
    try:
        import data_structures

        # ✅ Create a simple Point struct
        point = data_structures.create_point(10, 20)
        print(f"📍 Created point: {point}")
        print(f"   X coordinate: {point.x}")
        print(f"   Y coordinate: {point.y}")

        # ✅ Calculate distance between points
        origin = data_structures.create_point(0, 0)
        distance = data_structures.calculate_distance(origin, point)
        print(f"   Distance from origin: {distance}")

    finally:
        dana.disable_module_imports()

    print("✅ Basic structs with methods work great!\n")


def demo_complex_structs():
    """Demo 2: Complex structs with multiple field types."""
    print("📋 Demo 2: Complex Data Structures")
    print("-" * 40)

    dana.enable_module_imports()
    try:
        import data_structures

        # ✅ Create a UserProfile with mixed field types
        user = data_structures.create_user_profile(name="Alice Johnson", age=28, email="alice@example.com")

        print("👤 User Profile:")
        print(f"   Name: {user.name}")
        print(f"   Age: {user.age}")
        print(f"   Email: {user.email}")
        print(f"   Active: {user.active}")
        print(f"   Tags: {user.tags}")

        # ✅ AI-powered analysis of the struct
        analysis = data_structures.analyze_user_profile(user)
        print("\n🧠 AI Analysis:")
        print(f"   Data: {analysis.data}")
        print(f"   Confidence: {analysis.confidence}")
        print(f"   Recommendations: {analysis.recommendations}")

    finally:
        dana.disable_module_imports()

    print("✅ Complex structs with methods handle real-world data!\n")


def benefits_explanation():
    """Explain why DANA structs are valuable for AI Engineers."""
    print("💡 Why DANA Structs Matter for AI Engineers")
    print("-" * 50)

    print("""
🎯 Key Benefits:

1. **Type Safety**: Catch errors at runtime
   - Fields have defined types (str, int, bool, etc.)
   - No more mysterious data structure bugs

2. **Dot Notation**: Clean field access
   - user.name instead of user["name"]
   - Less prone to typos

3. **Object-Oriented Methods**: Structs with behavior
   - Define methods directly in struct definitions
   - Method chaining for fluent APIs
   - Immutable operations that return new instances

4. **AI Integration**: Structured data + reasoning
   - Pass structs directly to dana.reason()
   - AI understands structured context better
   - Clean input/output for AI workflows

5. **Python Compatibility**: Seamless integration
   - Import DANA structs into Python
   - Use like regular Python objects
   - Call struct methods from Python code
    """)


def quick_reference():
    """Quick reference for common struct operations."""
    print("📚 Quick Reference")
    print("-" * 20)

    print("""
🔧 Common Patterns:

# Import DANA module with structs
dana.enable_module_imports()
import my_structs

# Create struct instance
user = my_structs.create_user("Alice", 25)

# Access fields
name = user.name
age = user.age

# Call struct methods
first_name = user.get_first_name()
display_info = user.get_display_info()
updated_user = user.add_tag("premium")

# Use in AI reasoning
analysis = dana.reason(f"Analyze user profile: {user}")

# Clean up
dana.disable_module_imports()
    """)


def main():
    """Run the complete data structures tutorial."""
    print("🏗️ DANA Data Structures Tutorial")
    print("=" * 50)
    print("Learn how to use DANA structs from Python\n")

    # Run demos
    demo_basic_structs()
    demo_complex_structs()
    benefits_explanation()
    quick_reference()

    print("🎉 Tutorial Complete!")
    print("\n📖 What You Learned:")
    print("  ✅ Creating DANA structs from Python")
    print("  ✅ Accessing fields with dot notation")
    print("  ✅ Defining and calling struct methods")
    print("  ✅ Method chaining and immutable operations")
    print("  ✅ Using structs in AI reasoning")
    print("  ✅ Building complex data models")

    print("\n🔗 Next Steps:")
    print("  📝 Try creating your own struct definitions with methods")
    print("  🔗 Experiment with method chaining patterns")
    print("  🧠 Use structs with dana.reason() for AI analysis")
    print("  📚 Check out Tutorial 06: Function Pipelines")


if __name__ == "__main__":
    main()
