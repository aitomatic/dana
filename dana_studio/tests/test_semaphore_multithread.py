#!/usr/bin/env python3
"""Test to verify per-event-loop semaphore works across multiple threads.

This test verifies that the LLMQueryExecutor semaphore implementation
correctly handles multiple threads, each creating their own event loops.
This is critical for TaskManager worker threads that use safe_asyncio_run().
"""

import asyncio
import threading
import unittest
from threading import Thread

from dana.lang.common.sys_resource.llm.llm_query_executor import (
    LLMQueryExecutor,
)


class TestSemaphoreMultiThread(unittest.TestCase):
    """Test semaphore behavior across multiple threads."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset semaphore state before each test
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            LLMQueryExecutor._semaphores_by_loop = {}
        LLMQueryExecutor._max_concurrent_requests = 3

    def tearDown(self):
        """Clean up after each test."""
        # Reset semaphore state after each test
        if hasattr(LLMQueryExecutor, "_semaphores_by_loop"):
            LLMQueryExecutor._semaphores_by_loop = {}
        LLMQueryExecutor._max_concurrent_requests = 3

    def test_semaphore_works_across_multiple_threads(self):
        """CRITICAL: Test semaphore works across multiple threads.

        This test simulates the TaskManager scenario where worker threads
        create new event loops via safe_asyncio_run() (uses asyncio.run()).
        """
        results = []
        errors = []
        errors_lock = threading.Lock()

        def worker_thread(thread_id: int):
            """Worker thread that creates its own event loop."""

            async def test_async():
                # Get semaphore - should work even in new event loop
                semaphore = LLMQueryExecutor._get_global_semaphore()
                loop_id = id(asyncio.get_running_loop())
                return {
                    "thread_id": thread_id,
                    "loop_id": loop_id,
                    "semaphore_value": semaphore._value,
                }

            try:
                # Create new event loop (simulates safe_asyncio_run)
                result = asyncio.run(test_async())
                results.append(result)
            except Exception as e:
                with errors_lock:
                    errors.append((thread_id, str(e), type(e).__name__))

        # Create 5 threads, each with its own event loop
        threads = [Thread(target=worker_thread, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)  # Timeout to prevent hanging

        # Verify no "bound to different event loop" errors
        bound_errors = [e for e in errors if "bound to a different event loop" in str(e[1])]
        self.assertEqual(
            len(bound_errors),
            0,
            f"Found 'bound to different event loop' errors: {bound_errors}",
        )

        # Verify all threads succeeded
        self.assertEqual(
            len(results),
            5,
            f"Expected 5 results, got {len(results)}. Errors: {errors}",
        )

        # Verify each thread got its own semaphore (different loop IDs)
        loop_ids = [r["loop_id"] for r in results]
        self.assertEqual(
            len(set(loop_ids)),
            5,
            "Each thread should have its own event loop",
        )

        # Verify all semaphores have the same limit
        semaphore_values = [r["semaphore_value"] for r in results]
        self.assertTrue(
            all(v == 3 for v in semaphore_values),
            f"All semaphores should have limit 3, got: {semaphore_values}",
        )

        # Verify semaphores are stored in the dictionary
        expected_count = 5
        actual_count = len(LLMQueryExecutor._semaphores_by_loop)
        msg = f"Should have {expected_count} semaphores (one per loop)"
        self.assertEqual(actual_count, expected_count, msg)

    def test_semaphore_per_loop_isolation(self):
        """Test different event loops get different semaphore instances."""
        loop_ids = []
        semaphores = []

        def worker_thread(thread_id: int):
            async def test_async():
                semaphore = LLMQueryExecutor._get_global_semaphore()
                loop_id = id(asyncio.get_running_loop())
                loop_ids.append(loop_id)
                semaphores.append(semaphore)
                return semaphore

            asyncio.run(test_async())

        # Create 3 threads
        threads = [Thread(target=worker_thread, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        # Verify each thread got a different semaphore instance
        unique_semaphores = len(set(id(s) for s in semaphores))
        self.assertEqual(
            unique_semaphores,
            3,
            "Each loop should get its own semaphore instance",
        )

        # Verify semaphores are stored correctly
        for loop_id, semaphore in zip(loop_ids, semaphores, strict=True):
            self.assertIn(loop_id, LLMQueryExecutor._semaphores_by_loop)
            stored = LLMQueryExecutor._semaphores_by_loop[loop_id]
            self.assertIs(stored, semaphore)


if __name__ == "__main__":
    unittest.main()
