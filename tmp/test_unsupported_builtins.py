#!/usr/bin/env python3

from opendxa.dana.common.exceptions import SandboxError
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_unsupported_builtins():
    """Test that unsupported built-in functions raise appropriate errors."""
    ctx = SandboxContext()
    interpreter = DanaInterpreter()

    # Test cases for different unsupported functions
    test_cases = [
        ("eval", 'result = eval("1 + 1")', "arbitrary code execution"),
        ("open", 'file = open("test.txt")', "file system access"),
        ("print", 'print("hello")', "system modification"),
        ("globals", "g = globals()", "security risk"),
        ("exec", 'exec("x = 1")', "arbitrary code execution"),
        ("input", 'name = input("Enter name: ")', "security risk"),
    ]

    for func_name, code, expected_reason in test_cases:
        print(f"\nTesting unsupported function: {func_name}")
        print(f"Code: {code}")

        try:
            result = interpreter._eval(code, context=ctx)
            print(f"❌ ERROR: Function {func_name} should have been blocked!")
        except SandboxError as e:
            error_msg = str(e)
            print("✅ Correctly blocked with error:")
            print(f"   {error_msg[:100]}...")

            # Verify the error contains expected information
            if func_name in error_msg and "not supported" in error_msg:
                print("✅ Error message contains function name and restriction notice")
            else:
                print("⚠️  Error message format could be improved")
        except Exception as e:
            print(f"⚠️  Unexpected error type: {type(e).__name__}: {e}")


def test_security_report():
    """Test the security reporting functionality."""
    from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import PythonicFunctionFactory

    print("\n" + "=" * 60)
    print("SECURITY REPORT")
    print("=" * 60)

    factory = PythonicFunctionFactory()
    report = factory.get_security_report()

    print(f"Supported functions: {report['supported_functions']}")
    print(f"Unsupported functions: {report['unsupported_functions']}")
    print(f"Security-critical restrictions: {len(report['security_critical'])}")

    print("\nUnsupported functions by reason:")
    for reason, functions in report["unsupported_by_reason"].items():
        print(f"  {reason.replace('_', ' ').title()}: {len(functions)} functions")
        print(f"    Examples: {', '.join(functions[:3])}{'...' if len(functions) > 3 else ''}")


def test_function_queries():
    """Test the function query methods."""
    from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import PythonicFunctionFactory, UnsupportedReason

    print("\n" + "=" * 60)
    print("FUNCTION QUERY TESTS")
    print("=" * 60)

    factory = PythonicFunctionFactory()

    # Test supported function check
    print(f"len() is supported: {factory.is_supported('len')}")
    print(f"eval() is supported: {factory.is_supported('eval')}")
    print(f"eval() is unsupported: {factory.is_unsupported('eval')}")

    # Test getting functions by security reason
    security_risks = factory.get_functions_by_reason(UnsupportedReason.SECURITY_RISK)
    print(f"Functions blocked for security risks: {len(security_risks)}")
    print(f"Examples: {', '.join(security_risks[:5])}")

    # Test getting unsupported function info
    try:
        eval_info = factory.get_unsupported_info("eval")
        print("\neval() restriction info:")
        print(f"  Reason: {eval_info['reason'].value}")
        print(f"  Message: {eval_info['message']}")
        print(f"  Alternative: {eval_info['alternative'][:50]}...")
    except Exception as e:
        print(f"Error getting eval info: {e}")


if __name__ == "__main__":
    test_unsupported_builtins()
    test_security_report()
    test_function_queries()
