from opendxa.dana.sandbox.dana_sandbox import DanaSandbox

sandbox = DanaSandbox()

# Test 1: Simple scoped assignment and access
code1 = """
private:test_var = "hello"
result1 = private:test_var
"""

print("Test 1: Simple scoped variable access")
result1 = sandbox.eval(code1)
print(f"Success: {result1.success}")
if result1.success and result1.final_context:
    print(f"Result: {result1.final_context.get('local.result1')}")
else:
    print(f"Error: {result1.error}")

print("\n" + "=" * 50)

# Test 2: Access variable that should be in private scope from local scope
code2 = """
private:test_var = "hello"
# This should fail because test_var is in private scope, not local
try_access = test_var
"""

print("Test 2: Cross-scope variable access")
result2 = sandbox.eval(code2)
print(f"Success: {result2.success}")
if not result2.success:
    print(f"Error (expected): {result2.error}")

print("\n" + "=" * 50)

# Test 3: Check what the with statement is doing - simplified version
code3 = """
from opendxa.dana.sandbox.interpreter.test_with_statement_execution import MockMCPResource

private:mcp_client = MockMCPResource("test")
# Try to access attribute
result3 = private:mcp_client.name
"""

print("Test 3: Simplified attribute access test")
result3 = sandbox.eval(code3)
print(f"Success: {result3.success}")
if result3.success and result3.final_context:
    print(f"Result: {result3.final_context.get('local.result3')}")
else:
    print(f"Error: {result3.error}")

# Let's check what scopes exist
print("\n" + "=" * 50)
print("Checking available scopes and variables:")
if result1.final_context:
    # Let's inspect the context more directly
    try:
        print("Private scope variables:", [k for k in dir(result1.final_context) if "private" in k.lower()])
        print("Local variables available:", result1.final_context.get_all_local())
    except Exception as e:
        print(f"Error inspecting context: {e}")
