"""Simplified integration tests for logging system.

These tests focus on the core integration behaviors without
complex handler setup that conflicts with DANA_LOGGER.configure().
"""

import logging

import pytest

from dana.common.mixins.loggable import Loggable
from dana.common.utils.logging import DANA_LOGGER
from dana.core.lang.log_manager import LogLevel, SandboxLogger


class TestLoggingIntegrationSimple:
    """Simplified logging integration tests."""

    def setup_method(self):
        """Setup for each test."""
        # Reset DANA_LOGGER state
        DANA_LOGGER._configured = False

    def teardown_method(self):
        """Cleanup after each test."""
        # Reset DANA_LOGGER
        DANA_LOGGER._configured = False
        DANA_LOGGER.configure()

    def test_dana_logger_scope_default_behavior(self):
        """Test that DANA_LOGGER defaults to dana scope."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create loggers for different Dana modules
        agent_logger = DANA_LOGGER.getLogger("dana.frameworks.agent.TestAgent")
        dana_logger = DANA_LOGGER.getLogger("dana.TestDana")

        # Check initial effective levels (child loggers inherit from dana parent)
        assert agent_logger.logger.getEffectiveLevel() == logging.WARNING
        assert dana_logger.logger.getEffectiveLevel() == logging.WARNING

        # Set DEBUG level - should affect both by default (dana scope)
        DANA_LOGGER.setLevel(logging.DEBUG)

        # Both should now be DEBUG (either direct level or effective level)
        assert agent_logger.logger.getEffectiveLevel() == logging.DEBUG
        assert dana_logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_sandbox_logger_uses_dana_logger(self):
        """Test that SandboxLogger integrates with DANA_LOGGER."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create Dana logger
        test_logger = DANA_LOGGER.getLogger("dana.test.Component")

        # Initial level should be WARNING
        assert test_logger.logger.getEffectiveLevel() == logging.WARNING

        # Use SandboxLogger to set DEBUG
        SandboxLogger.set_system_log_level(LogLevel.DEBUG)

        # Logger should now be DEBUG
        assert test_logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_loggable_integration_with_global_level(self):
        """Test that Loggable respects global log level changes."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create Loggable component
        class TestComponent(Loggable):
            def __init__(self):
                super().__init__(logger_name="dana.test.LoggableComponent")

        component = TestComponent()

        # Initial level should be WARNING
        assert component.logger.logger.getEffectiveLevel() == logging.WARNING

        # Change global level
        DANA_LOGGER.setLevel(logging.DEBUG)

        # Component should now be DEBUG
        assert component.logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_existing_vs_new_loggers(self):
        """Test that both existing and new loggers are affected by level changes."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create existing logger
        existing_logger = DANA_LOGGER.getLogger("dana.test.ExistingLogger")
        assert existing_logger.logger.getEffectiveLevel() == logging.WARNING

        # Change global level
        DANA_LOGGER.setLevel(logging.INFO)

        # Existing logger should be updated
        assert existing_logger.logger.getEffectiveLevel() == logging.INFO

        # New logger should inherit the level
        new_logger = DANA_LOGGER.getLogger("dana.test.NewLogger")
        assert new_logger.logger.getEffectiveLevel() == logging.INFO

    def test_specific_scope_still_works(self):
        """Test that specific scope targeting still works."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create loggers in different scopes
        agent_logger = DANA_LOGGER.getLogger("dana.frameworks.agent.SpecificAgent")
        dana_logger = DANA_LOGGER.getLogger("dana.SpecificDana")

        # Both start at WARNING
        assert agent_logger.logger.getEffectiveLevel() == logging.WARNING
        assert dana_logger.logger.getEffectiveLevel() == logging.WARNING

        # Set DEBUG only for agent scope
        DANA_LOGGER.setLevel(logging.DEBUG, scope="dana.agent")

        # Only agent logger should be DEBUG
        assert agent_logger.logger.getEffectiveLevel() == logging.DEBUG
        assert dana_logger.logger.getEffectiveLevel() == logging.WARNING

    def test_non_dana_loggers_unaffected(self):
        """Test that non-Dana loggers are not affected."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create non-Dana logger
        external_logger = logging.getLogger("external.library.Logger")
        external_logger.setLevel(logging.ERROR)

        # Set Dana to DEBUG
        DANA_LOGGER.setLevel(logging.DEBUG)

        # External logger should be unchanged
        assert external_logger.level == logging.ERROR

        # Dana logger should be DEBUG
        dana_logger = DANA_LOGGER.getLogger("dana.test.Internal")
        assert dana_logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_dana_repl_simulation(self):
        """Test simulation of Dana REPL log level changes."""
        # Configure DANA_LOGGER (simulates REPL startup)
        DANA_LOGGER.configure(level=logging.WARNING)

        # Create REPL-like component
        class REPLComponent(Loggable):
            def __init__(self):
                super().__init__(logger_name="dana.core.lang.repl.TestREPL")

        # Create component before log level change
        repl_component = REPLComponent()
        assert repl_component.logger.logger.getEffectiveLevel() == logging.WARNING

        # Simulate user calling log_level(DEBUG) in Dana REPL
        SandboxLogger.set_system_log_level(LogLevel.DEBUG)

        # Existing component should now be DEBUG
        assert repl_component.logger.logger.getEffectiveLevel() == logging.DEBUG

        # New component created after should also be DEBUG
        new_repl_component = REPLComponent()
        assert new_repl_component.logger.logger.getEffectiveLevel() == logging.DEBUG

    @pytest.mark.parametrize("log_level", [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR])
    def test_all_sandbox_log_levels(self, log_level: LogLevel):
        """Test that all SandboxLogger levels work correctly."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.ERROR)

        # Create test component
        class TestComponent(Loggable):
            def __init__(self):
                super().__init__(logger_name="dana.test.LevelTest")

        component = TestComponent()

        # Set the test level via SandboxLogger
        SandboxLogger.set_system_log_level(log_level)

        # Component should have the correct effective level
        assert component.logger.logger.getEffectiveLevel() == log_level.value

    def test_logger_hierarchy_inheritance(self):
        """Test that logger hierarchy inheritance works correctly."""
        # Configure DANA_LOGGER
        DANA_LOGGER.configure(level=logging.WARNING)

        # Set level for dana parent
        DANA_LOGGER.setLevel(logging.DEBUG, scope="dana")

        # Create child loggers
        child1 = DANA_LOGGER.getLogger("dana.module.Child1")
        child2 = DANA_LOGGER.getLogger("dana.module.submodule.Child2")

        # Both should inherit DEBUG level (check effective level)
        assert child1.logger.getEffectiveLevel() == logging.DEBUG
        assert child2.logger.getEffectiveLevel() == logging.DEBUG

        # Create even deeper child
        deep_child = DANA_LOGGER.getLogger("dana.very.deep.nested.Child")
        assert deep_child.logger.getEffectiveLevel() == logging.DEBUG

    def test_configure_only_called_once(self):
        """Test that configure() is only called once per DANA_LOGGER instance."""
        # Verify initial state
        assert not DANA_LOGGER._configured

        # First configure call should work
        DANA_LOGGER.configure(level=logging.INFO)
        assert DANA_LOGGER._configured
        assert DANA_LOGGER.logger.level == logging.INFO

        # Second configure call should be ignored
        DANA_LOGGER.configure(level=logging.ERROR)
        assert DANA_LOGGER.logger.level == logging.INFO  # Should remain INFO

        # But setLevel should still work
        DANA_LOGGER.setLevel(logging.ERROR)
        assert DANA_LOGGER.logger.level == logging.ERROR
