"""
Dana ThreadPool - Runtime Thread Management

This module provides a shared thread pool for Dana-wide background tasks.
Extracted from DanaSandbox to provide better separation of concerns.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import atexit
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from dana.common.mixins.loggable import Loggable


class DanaThreadPool(Loggable):
    """
    Dana ThreadPool - Shared thread management for Dana runtime.

    Provides a singleton thread pool for background tasks across the Dana runtime.
    Automatically manages lifecycle with process exit cleanup.
    """

    # Singleton instance
    _instance: Optional["DanaThreadPool"] = None
    _lock = threading.Lock()

    def __init__(self, max_workers: int = 16, thread_name_prefix: str = "Dana-Background"):
        """
        Initialize the Dana thread pool.

        Args:
            max_workers: Maximum number of worker threads
            thread_name_prefix: Prefix for thread names
        """
        super().__init__()
        self._executor: ThreadPoolExecutor | None = None
        self._max_workers = max_workers
        self._thread_name_prefix = thread_name_prefix
        self._shutdown_called = False

        # Register cleanup on process exit
        atexit.register(self._cleanup_on_exit)

    @classmethod
    def get_instance(cls, max_workers: int = 16, thread_name_prefix: str = "Dana-Background") -> "DanaThreadPool":
        """
        Get the singleton instance of DanaThreadPool.

        Args:
            max_workers: Maximum number of worker threads (only used on first creation)
            thread_name_prefix: Prefix for thread names (only used on first creation)

        Returns:
            Singleton DanaThreadPool instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(max_workers, thread_name_prefix)
        return cls._instance

    def get_executor(self) -> ThreadPoolExecutor:
        """
        Get or create the ThreadPoolExecutor.

        Returns:
            ThreadPoolExecutor instance
        """
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix=self._thread_name_prefix)
                    self.debug(f"Created ThreadPoolExecutor with {self._max_workers} workers")

        return self._executor

    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool.

        Args:
            wait: Whether to wait for running tasks to complete
        """
        if self._shutdown_called:
            return

        self._shutdown_called = True

        if self._executor is not None:
            try:
                self.debug(f"Shutting down ThreadPoolExecutor (wait={wait})")
                self._executor.shutdown(wait=wait)
            except Exception as e:
                self.warning(f"Error shutting down ThreadPoolExecutor: {e}")
            finally:
                self._executor = None

    def _cleanup_on_exit(self):
        """Cleanup callback for process exit."""
        try:
            self.debug("Process exit: cleaning up DanaThreadPool")
            self.shutdown(wait=False)  # Don't wait during process exit
        except Exception as e:
            # Avoid exceptions during process exit
            try:
                self.warning(f"Error during process exit cleanup: {e}")
            except Exception:
                pass  # Ignore logging errors during process exit

    @classmethod
    def shutdown_all(cls):
        """
        Shutdown all thread pools - useful for testing or explicit cleanup.
        """
        if cls._instance is not None:
            cls._instance.shutdown(wait=True)
            cls._instance = None
