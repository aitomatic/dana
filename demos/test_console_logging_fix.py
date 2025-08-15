#!/usr/bin/env python3
"""
Test script to verify console logging can be properly disabled.

This script demonstrates the fix for duplicate logging in TUI.
"""

# Import Dana components
from dana.common.utils.logging import DANA_LOGGER


def test_logging_control():
    """Test that console logging can be properly controlled."""
    print("=== Testing Dana Logging Control ===")

    # Test 1: Check initial state
    print(f"\n1. Initial console logging enabled: {DANA_LOGGER.is_console_logging_enabled()}")

    # Test 2: Generate some logs
    print("\n2. Generating test logs (should appear in console):")
    DANA_LOGGER.info("Test log message 1 - should appear in console")
    DANA_LOGGER.warning("Test log message 2 - should appear in console")

    # Test 3: Disable console logging
    print("\n3. Disabling console logging...")
    DANA_LOGGER.disable_console_logging()
    print(f"   Console logging enabled: {DANA_LOGGER.is_console_logging_enabled()}")

    # Test 4: Generate more logs (should NOT appear in console)
    print("\n4. Generating test logs (should NOT appear in console):")
    DANA_LOGGER.info("Test log message 3 - should NOT appear in console")
    DANA_LOGGER.warning("Test log message 4 - should NOT appear in console")

    # Test 5: Re-enable console logging
    print("\n5. Re-enabling console logging...")
    DANA_LOGGER.configure(console=True, force=True)
    print(f"   Console logging enabled: {DANA_LOGGER.is_console_logging_enabled()}")

    # Test 6: Generate more logs (should appear in console again)
    print("\n6. Generating test logs (should appear in console again):")
    DANA_LOGGER.info("Test log message 5 - should appear in console again")
    DANA_LOGGER.warning("Test log message 6 - should appear in console again")

    print("\n=== Test completed ===")


def test_environment_variable():
    """Test environment variable control."""
    print("\n=== Testing Environment Variable Control ===")

    import os

    # Test with environment variable
    print("\nSetting DANA_CONSOLE_LOGGING=false...")
    os.environ["DANA_CONSOLE_LOGGING"] = "false"

    # Force reconfiguration to pick up environment variable
    DANA_LOGGER.configure(force=True)
    print(f"Console logging enabled: {DANA_LOGGER.is_console_logging_enabled()}")

    # Generate test logs
    print("Generating test logs with env var disabled:")
    DANA_LOGGER.info("This should NOT appear in console due to env var")

    # Clean up
    if "DANA_CONSOLE_LOGGING" in os.environ:
        del os.environ["DANA_CONSOLE_LOGGING"]

    print("=== Environment variable test completed ===")


if __name__ == "__main__":
    test_logging_control()
    test_environment_variable()

    print("\n" + "=" * 50)
    print("If you see this message and the test logs above, the fix is working!")
    print("Console logging can now be properly controlled.")
    print("=" * 50)
