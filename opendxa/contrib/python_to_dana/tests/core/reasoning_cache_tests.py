"""
Tests for ReasoningCache and caching integration with InProcessSandboxInterface
Table-driven test approach using pytest.mark.parametrize
"""

import time
from unittest.mock import Mock, patch

import pytest

from opendxa.contrib.python_to_dana.core.inprocess_sandbox import InProcessSandboxInterface
from opendxa.contrib.python_to_dana.core.reasoning_cache import ReasoningCache

# Test data for cache initialization
cache_initialization_params = [
    {
        "name": "default_parameters",
        "max_size": None,
        "ttl_seconds": None,
        "expected_max_size": 1000,
        "expected_ttl": 300.0,
    },
    {
        "name": "custom_parameters",
        "max_size": 100,
        "ttl_seconds": 60.0,
        "expected_max_size": 100,
        "expected_ttl": 60.0,
    },
    {
        "name": "large_cache",
        "max_size": 5000,
        "ttl_seconds": 3600.0,
        "expected_max_size": 5000,
        "expected_ttl": 3600.0,
    },
]

# Test data for cache key generation
cache_key_generation_params = [
    {
        "name": "same_prompts_same_keys",
        "prompt1": "What is 2+2?",
        "prompt2": "What is 2+2?",
        "options1": None,
        "options2": None,
        "should_be_equal": True,
    },
    {
        "name": "different_prompts_different_keys",
        "prompt1": "What is 2+2?",
        "prompt2": "What is 3+3?",
        "options1": None,
        "options2": None,
        "should_be_equal": False,
    },
    {
        "name": "case_insensitive_prompts",
        "prompt1": "What is 2+2?",
        "prompt2": "WHAT IS 2+2?",
        "options1": None,
        "options2": None,
        "should_be_equal": True,
    },
    {
        "name": "options_affect_key",
        "prompt1": "What is 2+2?",
        "prompt2": "What is 2+2?",
        "options1": None,
        "options2": {"temperature": 0.5},
        "should_be_equal": False,
    },
    {
        "name": "same_options_different_order",
        "prompt1": "What is 2+2?",
        "prompt2": "What is 2+2?",
        "options1": {"temperature": 0.5, "max_tokens": 100},
        "options2": {"max_tokens": 100, "temperature": 0.5},
        "should_be_equal": True,
    },
]

# Test data for basic cache operations
basic_cache_operations_params = [
    {
        "name": "cache_miss_initially",
        "prompt": "test prompt",
        "options": None,
        "result": None,
        "operation": "get",
        "expected": None,
    },
    {
        "name": "successful_put_and_get",
        "prompt": "test prompt",
        "options": None,
        "result": "test result",
        "operation": "put_then_get",
        "expected": "test result",
    },
    {
        "name": "dont_cache_none_result",
        "prompt": "empty prompt",
        "options": None,
        "result": None,
        "operation": "put",
        "expected": False,
    },
    {
        "name": "dont_cache_empty_string",
        "prompt": "empty prompt",
        "options": None,
        "result": "",
        "operation": "put",
        "expected": False,
    },
    {
        "name": "dont_cache_whitespace_only",
        "prompt": "empty prompt",
        "options": None,
        "result": "   ",
        "operation": "put",
        "expected": False,
    },
]

# Test data for cache statistics
cache_statistics_params = [
    {
        "name": "initial_empty_stats",
        "operations": [],
        "expected_hit_count": 0,
        "expected_miss_count": 0,
        "expected_hit_rate": 0.0,
        "expected_cache_size": 0,
    },
    {
        "name": "miss_only_stats",
        "operations": [("get", "test prompt", None)],
        "expected_hit_count": 0,
        "expected_miss_count": 1,
        "expected_hit_rate": 0.0,
        "expected_cache_size": 0,
    },
    {
        "name": "put_and_hit_stats",
        "operations": [("put", "test prompt", "test result"), ("get", "test prompt", None)],
        "expected_hit_count": 1,
        "expected_miss_count": 0,
        "expected_hit_rate": 1.0,
        "expected_cache_size": 1,
    },
    {
        "name": "mixed_hit_miss_stats",
        "operations": [
            ("get", "test prompt", None),  # miss
            ("put", "test prompt", "test result"),
            ("get", "test prompt", None),  # hit
        ],
        "expected_hit_count": 1,
        "expected_miss_count": 1,
        "expected_hit_rate": 0.5,
        "expected_cache_size": 1,
    },
]

# Test data for sandbox initialization
sandbox_initialization_params = [
    {
        "name": "default_cache_enabled",
        "enable_cache": None,
        "cache_max_size": None,
        "cache_ttl_seconds": None,
        "expected_cache_enabled": True,
        "expected_cache_exists": True,
    },
    {
        "name": "explicitly_disabled",
        "enable_cache": False,
        "cache_max_size": None,
        "cache_ttl_seconds": None,
        "expected_cache_enabled": False,
        "expected_cache_exists": False,
    },
    {
        "name": "custom_cache_settings",
        "enable_cache": True,
        "cache_max_size": 500,
        "cache_ttl_seconds": 600.0,
        "expected_cache_enabled": True,
        "expected_cache_exists": True,
        "expected_max_size": 500,
        "expected_ttl": 600.0,
    },
]

# Test data for cache with options behavior
cache_with_options_params = [
    {
        "name": "different_temperatures",
        "calls": [
            ("test", {"temperature": 0.5}),
            ("test", {"temperature": 0.7}),
        ],
        "expected_call_count": 2,  # Should not hit cache
    },
    {
        "name": "same_options_should_hit_cache",
        "calls": [
            ("test", {"temperature": 0.5}),
            ("test", {"temperature": 0.5}),
        ],
        "expected_call_count": 1,  # Should hit cache on second call
    },
    {
        "name": "no_options_vs_with_options",
        "calls": [
            ("test", None),
            ("test", {"temperature": 0.5}),
        ],
        "expected_call_count": 2,  # Different cache entries
    },
]


class TestReasoningCache:
    """Test the ReasoningCache class using table-driven approach."""

    @pytest.mark.parametrize("test_case", cache_initialization_params, ids=lambda x: x["name"])
    def test_cache_initialization(self, test_case):
        """Test cache initialization with different parameters."""
        # Arrange & Act
        if test_case["max_size"] is None and test_case["ttl_seconds"] is None:
            cache = ReasoningCache()
        else:
            kwargs = {}
            if test_case["max_size"] is not None:
                kwargs["max_size"] = test_case["max_size"]
            if test_case["ttl_seconds"] is not None:
                kwargs["ttl_seconds"] = test_case["ttl_seconds"]
            cache = ReasoningCache(**kwargs)

        # Assert
        assert cache.max_size == test_case["expected_max_size"]
        assert cache.ttl_seconds == test_case["expected_ttl"]

    @pytest.mark.parametrize("test_case", cache_key_generation_params, ids=lambda x: x["name"])
    def test_cache_key_generation(self, test_case):
        """Test cache key generation for consistency."""
        # Arrange
        cache = ReasoningCache()

        # Act
        key1 = cache._generate_cache_key(test_case["prompt1"], test_case["options1"])
        key2 = cache._generate_cache_key(test_case["prompt2"], test_case["options2"])

        # Assert
        if test_case["should_be_equal"]:
            assert key1 == key2
        else:
            assert key1 != key2

    @pytest.mark.parametrize("test_case", basic_cache_operations_params, ids=lambda x: x["name"])
    def test_basic_cache_operations(self, test_case):
        """Test basic cache get/put operations."""
        # Arrange
        cache = ReasoningCache(ttl_seconds=1.0)

        # Act & Assert
        if test_case["operation"] == "get":
            result = cache.get(test_case["prompt"], test_case["options"])
            assert result == test_case["expected"]

        elif test_case["operation"] == "put":
            result = cache.put(test_case["prompt"], test_case["options"], test_case["result"])
            assert result == test_case["expected"]

        elif test_case["operation"] == "put_then_get":
            success = cache.put(test_case["prompt"], test_case["options"], test_case["result"])
            assert success
            result = cache.get(test_case["prompt"], test_case["options"])
            assert result == test_case["expected"]

    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        # Arrange
        cache = ReasoningCache(ttl_seconds=0.1)  # Very short TTL

        # Act
        cache.put("test prompt", None, "test result")
        result_before = cache.get("test prompt")

        # Wait for expiration
        time.sleep(0.2)
        result_after = cache.get("test prompt")

        # Assert
        assert result_before == "test result"
        assert result_after is None

    def test_cache_eviction(self):
        """Test cache eviction when max size is reached."""
        # Arrange
        cache = ReasoningCache(max_size=3)

        # Act - Fill cache to capacity
        cache.put("prompt1", None, "result1")
        cache.put("prompt2", None, "result2")
        cache.put("prompt3", None, "result3")

        # Verify all cached
        result1 = cache.get("prompt1")
        result2 = cache.get("prompt2")
        result3 = cache.get("prompt3")

        # Add one more - should trigger eviction
        cache.put("prompt4", None, "result4")

        # Assert
        assert result1 == "result1"
        assert result2 == "result2"
        assert result3 == "result3"

        stats = cache.get_stats()
        assert stats["cache_size"] <= 3

        # New item should be cached
        assert cache.get("prompt4") == "result4"

    def test_cache_access_count_tracking(self):
        """Test that access counts are tracked for LRU eviction."""
        # Arrange
        cache = ReasoningCache(max_size=2)

        # Act
        cache.put("prompt1", None, "result1")
        cache.put("prompt2", None, "result2")

        # Access first item multiple times to increase its access count
        for _ in range(5):
            cache.get("prompt1")

        # Access second item once
        cache.get("prompt2")

        # Add third item - should evict prompt2 (lower access count)
        cache.put("prompt3", None, "result3")

        # Assert
        # prompt1 should still be there (higher access count)
        assert cache.get("prompt1") == "result1"
        # prompt3 should be there (just added)
        assert cache.get("prompt3") == "result3"
        # prompt2 might be evicted (depends on implementation)

    @pytest.mark.parametrize("test_case", cache_statistics_params, ids=lambda x: x["name"])
    def test_cache_statistics(self, test_case):
        """Test cache statistics tracking."""
        # Arrange
        cache = ReasoningCache()

        # Act
        for operation in test_case["operations"]:
            op_type, prompt, value = operation
            if op_type == "get":
                cache.get(prompt)
            elif op_type == "put":
                cache.put(prompt, None, value)

        stats = cache.get_stats()

        # Assert
        assert stats["hit_count"] == test_case["expected_hit_count"]
        assert stats["miss_count"] == test_case["expected_miss_count"]
        assert stats["hit_rate"] == test_case["expected_hit_rate"]
        assert stats["cache_size"] == test_case["expected_cache_size"]

    def test_cache_clear(self):
        """Test cache clearing."""
        # Arrange
        cache = ReasoningCache()
        cache.put("prompt1", None, "result1")
        cache.put("prompt2", None, "result2")
        cache.get("prompt1")  # Create some stats

        # Verify there's something to clear
        stats_before = cache.get_stats()
        assert stats_before["cache_size"] > 0
        assert stats_before["hit_count"] > 0

        # Act
        cache.clear()

        # Assert
        stats_after = cache.get_stats()
        assert stats_after["hit_count"] == 0
        assert stats_after["miss_count"] == 0
        assert stats_after["cache_size"] == 0

        # Verify cache is actually empty
        assert cache.get("prompt1") is None
        assert cache.get("prompt2") is None

    def test_cache_info_string(self):
        """Test cache info string generation."""
        # Arrange
        cache = ReasoningCache()

        # Act - Test empty cache
        info_empty = cache.get_cache_info()

        # Add some data
        cache.put("test", None, "result")
        cache.get("test")
        cache.get("missing")  # Miss

        info_with_data = cache.get_cache_info()

        # Assert
        assert "ReasoningCache" in info_empty
        assert "size=0" in info_empty

        assert "size=1" in info_with_data
        assert "hits=1" in info_with_data
        assert "misses=1" in info_with_data


class TestInProcessSandboxCacheIntegration:
    """Test caching integration with InProcessSandboxInterface using table-driven approach."""

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    @pytest.mark.parametrize("test_case", sandbox_initialization_params, ids=lambda x: x["name"])
    def test_sandbox_cache_initialization(self, mock_sandbox_class, test_case):
        """Test sandbox initialization with caching options."""
        # Arrange & Act
        kwargs = {}
        if test_case["enable_cache"] is not None:
            kwargs["enable_cache"] = test_case["enable_cache"]
        if test_case["cache_max_size"] is not None:
            kwargs["cache_max_size"] = test_case["cache_max_size"]
        if test_case["cache_ttl_seconds"] is not None:
            kwargs["cache_ttl_seconds"] = test_case["cache_ttl_seconds"]

        sandbox = InProcessSandboxInterface(**kwargs)

        # Assert
        assert sandbox.cache_enabled == test_case["expected_cache_enabled"]

        if test_case["expected_cache_exists"]:
            assert sandbox._cache is not None
            if "expected_max_size" in test_case:
                assert sandbox._cache.max_size == test_case["expected_max_size"]
            if "expected_ttl" in test_case:
                assert sandbox._cache.ttl_seconds == test_case["expected_ttl"]
        else:
            assert sandbox._cache is None

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_sandbox_reason_with_cache_hit(self, mock_sandbox_class):
        """Test reasoning with cache hit."""
        # Arrange
        mock_sandbox = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "2+2 equals 4"
        mock_sandbox.eval.return_value = mock_result
        mock_sandbox_class.return_value = mock_sandbox

        sandbox = InProcessSandboxInterface(debug=True)

        # Act
        result1 = sandbox.reason("What is 2+2?")
        result2 = sandbox.reason("What is 2+2?")  # Should hit cache
        sandbox.reason("What is 3+3?")  # Should miss cache

        # Assert
        assert result1 == "2+2 equals 4"
        assert result2 == "2+2 equals 4"
        assert mock_sandbox.eval.call_count == 2  # Only called twice (cache hit on second call)

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_sandbox_reason_without_cache(self, mock_sandbox_class):
        """Test reasoning without caching."""
        # Arrange
        mock_sandbox = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "2+2 equals 4"
        mock_sandbox.eval.return_value = mock_result
        mock_sandbox_class.return_value = mock_sandbox

        sandbox = InProcessSandboxInterface(enable_cache=False)

        # Act
        result1 = sandbox.reason("What is 2+2?")
        result2 = sandbox.reason("What is 2+2?")

        # Assert
        assert result1 == "2+2 equals 4"
        assert result2 == "2+2 equals 4"
        assert mock_sandbox.eval.call_count == 2  # Called again (no caching)

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    @pytest.mark.parametrize("test_case", cache_with_options_params, ids=lambda x: x["name"])
    def test_sandbox_cache_with_options(self, mock_sandbox_class, test_case):
        """Test caching with different options."""
        # Arrange
        mock_sandbox = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "response"
        mock_sandbox.eval.return_value = mock_result
        mock_sandbox_class.return_value = mock_sandbox

        sandbox = InProcessSandboxInterface()

        # Act
        for prompt, options in test_case["calls"]:
            sandbox.reason(prompt, options)

        # Assert
        assert mock_sandbox.eval.call_count == test_case["expected_call_count"]

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_sandbox_cache_stats_and_management(self, mock_sandbox_class):
        """Test cache statistics and management methods."""
        # Arrange
        mock_sandbox = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "response"
        mock_sandbox.eval.return_value = mock_result
        mock_sandbox_class.return_value = mock_sandbox

        sandbox = InProcessSandboxInterface()

        # Act & Assert - Initially no stats
        stats = sandbox.get_cache_stats()
        assert stats is not None
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0

        # Make a call
        sandbox.reason("test prompt")
        stats = sandbox.get_cache_stats()
        assert stats is not None
        assert stats["miss_count"] == 1
        assert stats["cache_size"] == 1

        # Hit cache
        sandbox.reason("test prompt")
        stats = sandbox.get_cache_stats()
        assert stats is not None
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1

        # Test cache info string
        info = sandbox.get_cache_info()
        assert "ReasoningCache" in info

        # Clear cache
        sandbox.clear_cache()
        stats = sandbox.get_cache_stats()
        assert stats is not None
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0
        assert stats["cache_size"] == 0

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_sandbox_cache_disabled_methods(self, mock_sandbox_class):
        """Test cache methods when caching is disabled."""
        # Arrange
        sandbox = InProcessSandboxInterface(enable_cache=False)

        # Act & Assert
        # Cache stats should return None
        assert sandbox.get_cache_stats() is None

        # Cache info should indicate disabled
        info = sandbox.get_cache_info()
        assert "disabled" in info.lower()

        # Clear cache should not raise error
        sandbox.clear_cache()  # Should not raise

    @patch("opendxa.contrib.python_to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_sandbox_close_clears_cache(self, mock_sandbox_class):
        """Test that closing sandbox clears the cache."""
        # Arrange
        mock_sandbox = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "response"
        mock_sandbox.eval.return_value = mock_result
        mock_sandbox_class.return_value = mock_sandbox

        sandbox = InProcessSandboxInterface()

        # Act
        sandbox.reason("test prompt")
        stats_before = sandbox.get_cache_stats()

        sandbox.close()
        stats_after = sandbox.get_cache_stats()

        # Assert
        assert stats_before is not None
        assert stats_before["cache_size"] == 1

        assert stats_after is not None
        assert stats_after["cache_size"] == 0
