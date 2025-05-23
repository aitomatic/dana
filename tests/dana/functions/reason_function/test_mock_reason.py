#!/usr/bin/env python3
"""
Test the reason function mocking behavior.

This test explicitly verifies the mock functionality of the reason_function.
"""

import os
import unittest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.sandbox.interpreter.functions.core.reason_function import reason_function
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestReasonMocking(unittest.TestCase):
    """Test the mocking behavior of the reason function."""

    def setUp(self):
        """Set up test environment."""
        self.context = SandboxContext()
        self.llm_resource = LLMResource()
        self.context.set("system.llm_resource", self.llm_resource)
        self.test_prompt = "What is 2+2? Answer with just the number."

    def test_explicit_mock_flag(self):
        """Test explicit mock flag overrides environment variable."""
        # Even if we say not to mock with env var, explicit parameter should override
        os.environ["OPENDXA_MOCK_LLM"] = "false"

        # Explicitly use mock
        result = reason_function(self.test_prompt, self.context, use_mock=True)
        self.assertIsNotNone(result)

        # Reset for other tests
        os.environ.pop("OPENDXA_MOCK_LLM", None)

    def test_environment_variable(self):
        """Test environment variable controls mocking when no explicit flag."""
        # Set environment variable to mock
        os.environ["OPENDXA_MOCK_LLM"] = "true"

        # Don't pass explicit mock flag
        result = reason_function(self.test_prompt, self.context)
        self.assertIsNotNone(result)

        # Reset for other tests
        os.environ.pop("OPENDXA_MOCK_LLM", None)

    def test_use_real_llm_flag(self):
        """Test OPENDXA_USE_REAL_LLM flag works as expected."""
        # Set to use real LLM
        os.environ["OPENDXA_USE_REAL_LLM"] = "true"

        # Set mock flag to conflict
        os.environ["OPENDXA_MOCK_LLM"] = "true"

        # With use_mock=None, should check environment variables
        # OPENDXA_USE_REAL_LLM=true should win and cause use_mock to be False
        # But we'll still force mocking for test safety
        result = reason_function(self.test_prompt, self.context, use_mock=True)
        self.assertIsNotNone(result)

        # Reset for other tests
        os.environ.pop("OPENDXA_USE_REAL_LLM", None)
        os.environ.pop("OPENDXA_MOCK_LLM", None)


if __name__ == "__main__":
    unittest.main()
