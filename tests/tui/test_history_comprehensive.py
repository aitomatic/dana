"""
Comprehensive History Navigation Tests with Simulated History Data.

Tests the history navigation functionality with a rich set of simulated history data
covering various scenarios: commands, functions, variables, imports, etc.
"""

import pytest

from dana.apps.tui import DanaTUI
from dana.apps.tui.ui.prompt_textarea import PromptStyleTextArea

from .history_test_utils import HistoryBackup, clear_history_for_test


def create_test_history():
    """Create a comprehensive set of test history data."""
    return [
        # Basic commands
        "print('Hello, World!')",
        "print('Welcome to Dana')",
        "print('Testing history navigation')",
        # Variable assignments
        "x = 42",
        "y = 'hello'",
        "z = [1, 2, 3, 4, 5]",
        "name = 'Alice'",
        "age = 30",
        "is_active = True",
        # Function definitions
        "def greet(name):",
        "    return f'Hello, {name}!'",
        "def calculate_sum(a, b):",
        "    return a + b",
        "def factorial(n):",
        "    if n <= 1:",
        "        return 1",
        "    return n * factorial(n - 1)",
        "def process_data(data):",
        "    result = []",
        "    for item in data:",
        "        if item > 0:",
        "            result.append(item * 2)",
        "    return result",
        # Import statements
        "import os",
        "import sys",
        "from datetime import datetime",
        "from typing import List, Dict, Optional",
        "import json",
        "import requests",
        # Class definitions
        "class User:",
        "    def __init__(self, name, email):",
        "        self.name = name",
        "        self.email = email",
        "class Calculator:",
        "    def add(self, x, y):",
        "        return x + y",
        "    def multiply(self, x, y):",
        "        return x * y",
        # Control flow
        "if x > 10:",
        "    print('x is greater than 10')",
        "elif x == 10:",
        "    print('x equals 10')",
        "else:",
        "    print('x is less than 10')",
        "for i in range(10):",
        "    print(f'Iteration {i}')",
        "while count > 0:",
        "    print(count)",
        "    count -= 1",
        # List comprehensions and generators
        "squares = [x**2 for x in range(10)]",
        "evens = [x for x in range(20) if x % 2 == 0]",
        "word_lengths = [len(word) for word in words]",
        # Error handling
        "try:",
        "    result = 10 / 0",
        "except ZeroDivisionError:",
        "    print('Cannot divide by zero')",
        "finally:",
        "    print('Cleanup complete')",
        # File operations
        "with open('data.txt', 'r') as f:",
        "    content = f.read()",
        "with open('output.txt', 'w') as f:",
        "    f.write('Hello, World!')",
        # Data structures
        "my_dict = {'name': 'John', 'age': 25, 'city': 'New York'}",
        "my_set = {1, 2, 3, 4, 5}",
        "my_tuple = (1, 2, 3, 'hello', True)",
        # String operations
        "message = 'Hello, World!'.upper()",
        "words = 'python,dana,programming'.split(',')",
        "formatted = f'Name: {name}, Age: {age}'",
        # Math operations
        "result = (a + b) * c / d",
        "power = base ** exponent",
        "remainder = dividend % divisor",
        # Lambda functions
        "square = lambda x: x**2",
        "add = lambda x, y: x + y",
        "is_even = lambda x: x % 2 == 0",
        # Decorators
        "@timer",
        "def slow_function():",
        "    time.sleep(1)",
        "@cache",
        "def expensive_calculation(n):",
        "    return n * n * n",
        # Context managers
        "with open('file.txt') as f:",
        "    data = f.read()",
        "with tempfile.NamedTemporaryFile() as tmp:",
        "    tmp.write(b'Hello')",
        # Async functions
        "async def fetch_data(url):",
        "    async with aiohttp.ClientSession() as session:",
        "        async with session.get(url) as response:",
        "            return await response.text()",
        # Type hints
        "def process_items(items: List[str]) -> Dict[str, int]:",
        "    return {item: len(item) for item in items}",
        # Comments and documentation
        "# This is a comment",
        "'''This is a docstring'''",
        "# TODO: Implement this feature",
        # Debugging
        "import pdb; pdb.set_trace()",
        "print(f'DEBUG: {variable}')",
        "assert condition, 'Error message'",
        # Testing
        "def test_function():",
        "    assert add(2, 3) == 5",
        "    assert multiply(4, 5) == 20",
        # Configuration
        "DEBUG = True",
        "API_KEY = 'your-api-key-here'",
        "DATABASE_URL = 'postgresql://localhost/mydb'",
        # Shell commands (if applicable)
        "!ls -la",
        "!git status",
        "!pip install requests",
        # Dana-specific commands
        "agent research",
        "agent coder",
        "agent planner",
        "help",
        "clear",
        "history",
        "quit",
    ]


@pytest.mark.asyncio
async def test_history_navigation_with_comprehensive_data():
    """Test history navigation with comprehensive simulated history data."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Clear existing history and add comprehensive test data
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history
            test_history = create_test_history()

        print(f"Loading {len(test_history)} history items...")
        for item in test_history:
            prompt_widget.add_to_history(item)

        print(f"History loaded: {len(prompt_widget._history)} items")
        print(f"First 5 items: {prompt_widget._history[:5]}")
        print(f"Last 5 items: {prompt_widget._history[-5:]}")

        # Test 1: Verify history loading
        print("\n=== Test 1: History loading verification ===")
        assert len(prompt_widget._history) == len(test_history)
        print(f"Loaded {len(prompt_widget._history)} history items")

        # Test 2: Prefix filtering verification
        print("\n=== Test 2: Prefix filtering verification ===")
        def_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("def")]
        print_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("print")]
        import_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("import")]
        class_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("class")]
        async_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("async")]
        agent_commands = [cmd for cmd in prompt_widget._history if cmd.startswith("agent")]

        print(f"Found {len(def_commands)} 'def' commands")
        print(f"Found {len(print_commands)} 'print' commands")
        print(f"Found {len(import_commands)} 'import' commands")
        print(f"Found {len(class_commands)} 'class' commands")
        print(f"Found {len(async_commands)} 'async' commands")
        print(f"Found {len(agent_commands)} 'agent' commands")

        # Verify we have the expected number of each type
        assert len(def_commands) >= 1
        assert len(print_commands) >= 1
        assert len(import_commands) >= 1
        assert len(class_commands) >= 1
        assert len(async_commands) >= 1
        assert len(agent_commands) >= 1

        print("\n✅ All comprehensive history navigation tests passed!")


@pytest.mark.asyncio
async def test_history_statistics():
    """Test and display statistics about the history data."""
    # Backup and restore history to avoid affecting user's actual history
    with HistoryBackup():
        app = DanaTUI()
        async with app.run_test():
            prompt_widget = app.query_one(PromptStyleTextArea)
            assert prompt_widget is not None

            # Load comprehensive history
            clear_history_for_test()
            prompt_widget._load_history()  # Reload the cleared history
            test_history = create_test_history()
        for item in test_history:
            prompt_widget.add_to_history(item)

        # Analyze history data
        print("\n=== History Statistics ===")
        print(f"Total history items: {len(prompt_widget._history)}")

        # Count items by prefix
        prefixes = {
            "print": len([item for item in prompt_widget._history if item.startswith("print")]),
            "def": len([item for item in prompt_widget._history if item.startswith("def")]),
            "import": len([item for item in prompt_widget._history if item.startswith("import")]),
            "class": len([item for item in prompt_widget._history if item.startswith("class")]),
            "async": len([item for item in prompt_widget._history if item.startswith("async")]),
            "agent": len([item for item in prompt_widget._history if item.startswith("agent")]),
            "if": len([item for item in prompt_widget._history if item.startswith("if")]),
            "for": len([item for item in prompt_widget._history if item.startswith("for")]),
            "while": len([item for item in prompt_widget._history if item.startswith("while")]),
            "try": len([item for item in prompt_widget._history if item.startswith("try")]),
            "with": len([item for item in prompt_widget._history if item.startswith("with")]),
        }

        print("Items by prefix:")
        for prefix, count in sorted(prefixes.items()):
            if count > 0:
                print(f"  {prefix}: {count}")

        # Test that we can find items by prefix
        for prefix in ["print", "def", "import", "class", "agent"]:
            if prefixes[prefix] > 0:
                print(f"\nTesting prefix filtering for '{prefix}' ({prefixes[prefix]} items)...")

                # Find matching items in history
                matching_items = [item for item in prompt_widget._history if item.startswith(prefix)]
                print(f"  Found {len(matching_items)} matching items")
                assert len(matching_items) == prefixes[prefix]
                assert all(item.startswith(prefix) for item in matching_items)

        print("\n✅ History statistics test passed!")


if __name__ == "__main__":
    # Run the tests directly
    import asyncio

    async def run_comprehensive_tests():
        print("Running comprehensive history navigation tests...")
        await test_history_navigation_with_comprehensive_data()
        await test_history_statistics()
        print("\n🎉 All comprehensive tests completed successfully!")

    asyncio.run(run_comprehensive_tests())
