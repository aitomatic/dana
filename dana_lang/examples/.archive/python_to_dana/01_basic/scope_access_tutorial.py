#!/usr/bin/env python3
"""
Tutorial 04: DANA Scope Access from Python

🎯 LEARNING OBJECTIVES:
- Understand DANA's 4 scope types (local, public, private, system)
- See which scopes Python can access directly
- Learn function-based access patterns for all scopes

⚡ QUICK START:
Run this to see scope access in action!

💡 WHY THIS MATTERS:
Control data visibility between DANA modules and Python code
"""

import sys
from pathlib import Path

# Add Dana to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dana.dana import dana


def step1_direct_scope_access():
    """Step 1: Test direct access to different scopes"""
    print("🔍 STEP 1: Direct Scope Access Test")
    print("=" * 40)
    print()

    # Create DANA module with all scope types
    dana_code = """
# scope_demo.na

# LOCAL SCOPE - Python CAN access these
local_name = "Dana"
local_version = 2.0

# PUBLIC SCOPE - Python CAN access these  
public:shared_status = "active"
public:global_counter = 100

# PRIVATE SCOPE - Python CANNOT access these directly
private:secret_key = "hidden_data"
private:internal_state = {"initialized": true}

# SYSTEM SCOPE - Python CANNOT access these directly
system:debug_mode = false
system:max_memory = 1024
"""

    dana_file = Path(__file__).parent / "dana" / "scope_demo.na"
    dana_file.parent.mkdir(exist_ok=True)
    dana_file.write_text(dana_code)

    print("📝 Created scope_demo.na with all 4 scope types:")
    print(dana_code)

    print("🧪 Testing Direct Access from Python:")

    dana.enable_module_imports()
    try:
        import scope_demo

        print("\n📋 Available attributes:")
        attrs = [attr for attr in dir(scope_demo) if not attr.startswith("_")]
        for attr in sorted(attrs):
            print(f"  • {attr}")

        print("\n🎯 Direct Access Results:")

        # ✅ LOCAL SCOPE - Should work
        try:
            local_name = scope_demo.local_name
            local_version = scope_demo.local_version
            print(f"  ✅ LOCAL: {local_name} v{local_version}")
        except AttributeError as e:
            print(f"  ❌ LOCAL failed: {e}")

        # ✅ PUBLIC SCOPE - Should work
        try:
            status = scope_demo.shared_status
            counter = scope_demo.global_counter
            print(f"  ✅ PUBLIC: status={status}, counter={counter}")
        except AttributeError as e:
            print(f"  ❌ PUBLIC failed: {e}")

        # ❌ PRIVATE SCOPE - Should NOT work
        try:
            secret = scope_demo.secret_key
            print(f"  ⚠️  PRIVATE accessible: {secret}")
        except AttributeError:
            print("  ✅ PRIVATE properly hidden (as expected)")

        # ❌ SYSTEM SCOPE - Should NOT work
        try:
            debug = scope_demo.debug_mode
            print(f"  ⚠️  SYSTEM accessible: {debug}")
        except AttributeError:
            print("  ✅ SYSTEM properly hidden (as expected)")

    finally:
        dana.disable_module_imports()
        dana_file.unlink()

    print()


def step2_function_based_access():
    """Step 2: Access all scopes through functions"""
    print("🔧 STEP 2: Function-Based Scope Access")
    print("=" * 40)
    print()

    # Create DANA module with accessor functions
    dana_code = """
# scope_access.na

# Different scoped variables
local_config = "app_settings"
public:shared_data = "world_state"
private:secret_token = "abc123xyz"
system:system_info = "v2.1.0"

# Accessor functions for each scope
def get_local_data() -> str:
    return local_config

def get_public_data() -> str:
    return public:shared_data

def get_private_data() -> str:
    return private:secret_token

def get_system_data() -> str:
    return system:system_info

def get_all_scopes() -> dict:
    return {
        "local": local_config,
        "public": public:shared_data,
        "private": private:secret_token,
        "system": system:system_info
    }
"""

    dana_file = Path(__file__).parent / "dana" / "scope_access.na"
    dana_file.write_text(dana_code)

    print("📝 Created scope_access.na with accessor functions")
    print(dana_code)

    print("🔧 Python accessing all scopes via functions:")
    print("""
    import scope_access
    
    local_data = scope_access.get_local_data()     # ✅ Works
    public_data = scope_access.get_public_data()   # ✅ Works  
    private_data = scope_access.get_private_data() # ✅ Works via function
    system_data = scope_access.get_system_data()   # ✅ Works via function
    """)

    print("🚀 Live Demo:")
    dana.enable_module_imports()
    try:
        import scope_access

        print(f"  📦 Local data: {scope_access.get_local_data()}")
        print(f"  🌍 Public data: {scope_access.get_public_data()}")
        print(f"  🔒 Private data: {scope_access.get_private_data()}")
        print(f"  ⚙️  System data: {scope_access.get_system_data()}")

        print("\n📊 All scopes at once:")
        all_data = scope_access.get_all_scopes()
        for scope, value in all_data.items():
            print(f"  • {scope}: {value}")

    finally:
        dana.disable_module_imports()
        dana_file.unlink()

    print()


def step3_practical_patterns():
    """Step 3: Practical scope usage patterns"""
    print("💼 STEP 3: Practical Scope Patterns")
    print("=" * 40)
    print()

    dana_code = """
# user_manager.na

# PUBLIC: Shared application state
public:active_users = 0
public:system_status = "running"

# PRIVATE: Internal user data
private:user_sessions = {}
private:admin_key = "super_secret"

# LOCAL: Configuration
max_concurrent_users = 50
session_timeout = 3600

def login_user(username: str) -> bool:
    if public:active_users >= max_concurrent_users:
        return false
    
    public:active_users = public:active_users + 1
    private:user_sessions[username] = "active"
    return true

def logout_user(username: str) -> bool:
    if username in private:user_sessions:
        public:active_users = public:active_users - 1
        private:user_sessions[username] = "inactive"
        return true
    return false

def get_public_stats() -> dict:
    return {
        "active_users": public:active_users,
        "system_status": public:system_status,
        "max_users": max_concurrent_users
    }

def admin_get_all_data(admin_password: str) -> dict:
    if admin_password != private:admin_key:
        return {"error": "unauthorized"}
    
    return {
        "public": {
            "active_users": public:active_users,
            "system_status": public:system_status
        },
        "private": private:user_sessions,
        "config": max_concurrent_users
    }
"""

    dana_file = Path(__file__).parent / "dana" / "user_manager.na"
    dana_file.write_text(dana_code)

    print("📝 Created practical user_manager.na")
    print(dana_code)

    print("🚀 Python using DANA with proper scope management:")

    dana.enable_module_imports()
    try:
        import user_manager

        # Normal operations - only access public data
        print("  👤 User operations:")
        print(f"    • Login Alice: {user_manager.login_user('Alice')}")
        print(f"    • Login Bob: {user_manager.login_user('Bob')}")
        print(f"    • Public stats: {user_manager.get_public_stats()}")

        # Admin operations - access private data with auth
        print("\n  👑 Admin operations:")
        wrong_key = user_manager.admin_get_all_data("wrong_password")
        print(f"    • Wrong password: {wrong_key}")

        correct_key = user_manager.admin_get_all_data("super_secret")
        print(f"    • Correct password: {correct_key}")

        # Direct access only works for local/public
        print(f"\n  🔍 Direct access to public:active_users: {user_manager.active_users}")
        print(f"  🔍 Direct access to max_concurrent_users: {user_manager.max_concurrent_users}")

    finally:
        dana.disable_module_imports()
        dana_file.unlink()

    print()


def scope_summary():
    """Summary of scope access patterns"""
    print("📋 SCOPE ACCESS SUMMARY")
    print("=" * 40)
    print()

    summary_table = [
        ("Scope", "Python Direct Access", "Function Access", "Use Case"),
        ("-" * 8, "-" * 19, "-" * 15, "-" * 25),
        ("local:", "✅ Yes", "✅ Yes", "Module configuration"),
        ("public:", "✅ Yes", "✅ Yes", "Shared app state"),
        ("private:", "❌ No", "✅ Yes", "Internal secrets"),
        ("system:", "❌ No", "✅ Yes", "System internals"),
    ]

    for row in summary_table:
        print(f"{row[0]:<10} {row[1]:<20} {row[2]:<16} {row[3]}")

    print()
    print("💡 Best Practices:")
    print("  • Use local: for module configuration")
    print("  • Use public: for shared application state")
    print("  • Use private: for sensitive internal data")
    print("  • Use system: for framework/system data")
    print("  • Access private/system scopes only via functions")
    print()


def main():
    """Run the tutorial"""
    print("🔍 DANA Scope Access Tutorial")
    print("=" * 50)
    print()

    step1_direct_scope_access()
    step2_function_based_access()
    step3_practical_patterns()
    scope_summary()

    print("🎯 KEY TAKEAWAYS:")
    print("  • Python can directly access local: and public: scopes")
    print("  • private: and system: scopes need function-based access")
    print("  • Use scopes to control data visibility and security")
    print("  • Functions provide controlled access to all scopes")
    print()
    print("🎯 NEXT: Try 05_dana_structs_from_python.py for data structures!")


if __name__ == "__main__":
    main()
