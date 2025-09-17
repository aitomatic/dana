#!/usr/bin/env python3
"""
Tutorial 03: Importing DANA Modules from Python

🎯 LEARNING OBJECTIVES:
- Enable DANA module imports in Python
- Import and use DANA functions from .na files
- Understand the import/disable pattern

⚡ QUICK START:
Run this to see Python importing DANA code!

💡 WHY THIS MATTERS:
Write business logic in DANA, use from Python seamlessly
"""

import sys
from pathlib import Path

# Add Dana to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dana.dana import dana


def step1_basic_import():
    """Step 1: Import a simple DANA module"""
    print("📦 STEP 1: Basic DANA Module Import")
    print("=" * 40)
    print()

    # First, create a simple DANA module in memory for demo
    dana_code = """
# simple_math.na
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b

def greeting(name: str) -> str:
    return f"Hello from DANA, {name}!"
"""

    # Write the DANA file temporarily
    dana_file = Path(__file__).parent / "dana" / "simple_math.na"
    dana_file.parent.mkdir(exist_ok=True)
    dana_file.write_text(dana_code)

    print("📝 Created simple_math.na:")
    print(dana_code)

    print("🔧 Python Code:")
    print("""
    dana.enable_module_imports()  # Enable DANA imports
    import simple_math            # Import .na file (no extension!)
    
    result = simple_math.add(5, 3)     # Use DANA function
    greeting = simple_math.greeting("Alice")
    
    dana.disable_module_imports() # Clean up
    """)

    # Actually run it
    print("🚀 Live Demo:")
    dana.enable_module_imports()
    try:
        import simple_math

        result = simple_math.add(5, 3)
        greeting = simple_math.greeting("Alice")
        product = simple_math.multiply(4, 7)

        print(f"  • simple_math.add(5, 3) = {result}")
        print(f"  • simple_math.greeting('Alice') = {greeting}")
        print(f"  • simple_math.multiply(4, 7) = {product}")

    finally:
        dana.disable_module_imports()
        dana_file.unlink()

    print()


def step2_variables_and_state():
    """Step 2: Access DANA module variables"""
    print("📊 STEP 2: Accessing DANA Variables")
    print("=" * 40)
    print()

    # Create DANA module with variables
    dana_code = """
# config.na
app_name = "DataProcessor"
version = "1.0.0"
max_users = 100

def get_info() -> str:
    return f"{app_name} v{version} (max {max_users} users)"

def is_valid_user_count(count: int) -> bool:
    return count <= max_users
"""

    dana_file = Path(__file__).parent / "dana" / "config.na"
    dana_file.write_text(dana_code)

    print("📝 Created config.na with variables and functions")
    print(dana_code)

    print("🔧 Python accessing DANA variables:")
    print("""
    import config
    
    name = config.app_name      # Access DANA variable
    version = config.version    # Access DANA variable
    info = config.get_info()    # Call DANA function
    """)

    print("🚀 Live Demo:")
    dana.enable_module_imports()
    try:
        import config

        print(f"  • App Name: {config.app_name}")
        print(f"  • Version: {config.version}")
        print(f"  • Max Users: {config.max_users}")
        print(f"  • Info: {config.get_info()}")
        print(f"  • Valid for 50 users? {config.is_valid_user_count(50)}")
        print(f"  • Valid for 150 users? {config.is_valid_user_count(150)}")

    finally:
        dana.disable_module_imports()
        dana_file.unlink()

    print()


def step3_best_practices():
    """Step 3: Best practices and patterns"""
    print("⭐ STEP 3: Best Practices")
    print("=" * 40)
    print()

    print("✅ Always use try/finally pattern:")
    print("""
    dana.enable_module_imports()
    try:
        import my_dana_module
        result = my_dana_module.my_function()
    finally:
        dana.disable_module_imports()  # Always clean up!
    """)
    print()

    print("✅ Import DANA modules without .na extension:")
    print("  • File: math_utils.na")
    print("  • Import: import math_utils")
    print()

    print("✅ DANA modules can use AI reasoning:")
    print("  • reason() function available in DANA")
    print("  • Call AI logic from Python via DANA")
    print()

    print("❌ Common mistakes:")
    print("  • Forgetting dana.disable_module_imports()")
    print("  • Adding .na extension in import")
    print("  • Not using try/finally pattern")
    print()


def practical_example():
    """Show a practical business example"""
    print("💼 PRACTICAL EXAMPLE: Business Calculator")
    print("=" * 40)
    print()

    # Create practical DANA module
    dana_code = """
# business_calc.na
tax_rate = 0.08
discount_threshold = 1000

def calculate_total(subtotal: float, discount_percent: float) -> dict:
    discount_amount = 0.0
    if subtotal >= discount_threshold:
        discount_amount = subtotal * (discount_percent / 100)
    
    discounted = subtotal - discount_amount
    tax_amount = discounted * tax_rate
    total = discounted + tax_amount
    
    return {
        "subtotal": subtotal,
        "discount": discount_amount,
        "tax": tax_amount,
        "total": total
    }

def analyze_purchase(total: float) -> str:
    if total > 500:
        return "high-value purchase"
    elif total > 100:
        return "medium purchase"  
    else:
        return "small purchase"
"""

    dana_file = Path(__file__).parent / "dana" / "business_calc.na"
    dana_file.write_text(dana_code)

    print("📝 Created business_calc.na for practical calculations")
    print(dana_code)

    print("🚀 Python using DANA business logic:")

    dana.enable_module_imports()
    try:
        import business_calc

        # Calculate some orders
        orders = [{"amount": 1200, "discount": 10}, {"amount": 85, "discount": 0}, {"amount": 750, "discount": 5}]

        for i, order in enumerate(orders, 1):
            result = business_calc.calculate_total(order["amount"], order["discount"])
            category = business_calc.analyze_purchase(result["total"])

            print(f"  Order {i}: ${order['amount']} → ${result['total']:.2f} ({category})")

    finally:
        dana.disable_module_imports()
        dana_file.unlink()

    print()


def main():
    """Run the tutorial"""
    print("📚 DANA Module Import Tutorial")
    print("=" * 50)
    print()

    step1_basic_import()
    step2_variables_and_state()
    step3_best_practices()
    practical_example()

    print("🎯 SUMMARY:")
    print("  • dana.enable_module_imports() to start")
    print("  • import dana_module (no .na extension)")
    print("  • dana.disable_module_imports() to clean up")
    print("  • Always use try/finally pattern")
    print()
    print("🎯 NEXT: Try 04_scope_access_tutorial.py for data structures!")


if __name__ == "__main__":
    main()
