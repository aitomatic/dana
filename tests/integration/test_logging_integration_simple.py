"""Simplified integration tests for logging system.

These tests focus on the core integration behaviors without
complex handler setup that conflicts with DXA_LOGGER.configure().
"""

import logging

import pytest

from opendxa.common.mixins.loggable import Loggable
from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.dana.sandbox.log_manager import LogLevel, SandboxLogger


class TestLoggingIntegrationSimple:
    """Simplified logging integration tests."""

    def setup_method(self):
        """Setup for each test."""
        # Reset DXA_LOGGER state
        DXA_LOGGER._configured = False

    def teardown_method(self):
        """Cleanup after each test."""
        # Reset DXA_LOGGER
        DXA_LOGGER._configured = False
        DXA_LOGGER.configure()

    def test_dxa_logger_scope_default_behavior(self):
        """Test that DXA_LOGGER defaults to opendxa scope."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create loggers for different OpenDXA modules
        agent_logger = DXA_LOGGER.getLogger("opendxa.agent.TestAgent")
        dana_logger = DXA_LOGGER.getLogger("opendxa.dana.TestDana")

        # Check initial effective levels (child loggers inherit from opendxa parent)
        assert agent_logger.logger.getEffectiveLevel() == logging.WARNING
        assert dana_logger.logger.getEffectiveLevel() == logging.WARNING

        # Set DEBUG level - should affect both by default (opendxa scope)
        DXA_LOGGER.setLevel(logging.DEBUG)

        # Both should now be DEBUG (either direct level or effective level)
        assert agent_logger.logger.getEffectiveLevel() == logging.DEBUG
        assert dana_logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_sandbox_logger_uses_dxa_logger(self):
        """Test that SandboxLogger integrates with DXA_LOGGER."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create OpenDXA logger
        test_logger = DXA_LOGGER.getLogger("opendxa.test.Component")

        # Initial level should be WARNING
        assert test_logger.logger.getEffectiveLevel() == logging.WARNING

        # Use SandboxLogger to set DEBUG
        SandboxLogger.set_system_log_level(LogLevel.DEBUG)

        # Logger should now be DEBUG
        assert test_logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_loggable_integration_with_global_level(self):
        """Test that Loggable respects global log level changes."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create Loggable component
        class TestComponent(Loggable):
            def __init__(self):
                super().__init__(logger_name="opendxa.test.LoggableComponent")

        component = TestComponent()

        # Initial level should be WARNING
        assert component.logger.logger.getEffectiveLevel() == logging.WARNING

        # Change global level
        DXA_LOGGER.setLevel(logging.DEBUG)

        # Component should now be DEBUG
        assert component.logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_existing_vs_new_loggers(self):
        """Test that both existing and new loggers are affected by level changes."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create existing logger
        existing_logger = DXA_LOGGER.getLogger("opendxa.test.ExistingLogger")
        assert existing_logger.logger.getEffectiveLevel() == logging.WARNING

        # Change global level
        # DXA_LOGGER.setLevel(logging.INFO)

        # Existing logger should be updated
        assert existing_logger.logger.getEffectiveLevel() == logging.INFO

        # New logger should inherit the level
        new_logger = DXA_LOGGER.getLogger("opendxa.test.NewLogger")
        assert new_logger.logger.getEffectiveLevel() == logging.INFO

    def test_specific_scope_still_works(self):
        """Test that specific scope targeting still works."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create loggers in different scopes
        agent_logger = DXA_LOGGER.getLogger("opendxa.agent.SpecificAgent")
        dana_logger = DXA_LOGGER.getLogger("opendxa.dana.SpecificDana")

        # Both start at WARNING
        assert agent_logger.logger.getEffectiveLevel() == logging.WARNING
        assert dana_logger.logger.getEffectiveLevel() == logging.WARNING

        # Set DEBUG only for agent scope
        DXA_LOGGER.setLevel(logging.DEBUG, scope="opendxa.agent")

        # Only agent logger should be DEBUG
        assert agent_logger.logger.getEffectiveLevel() == logging.DEBUG
        assert dana_logger.logger.getEffectiveLevel() == logging.WARNING

    def test_non_opendxa_loggers_unaffected(self):
        """Test that non-OpenDXA loggers are not affected."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create non-OpenDXA logger
        external_logger = logging.getLogger("external.library.Logger")
        external_logger.setLevel(logging.ERROR)

        # Set OpenDXA to DEBUG
        DXA_LOGGER.setLevel(logging.DEBUG)

        # External logger should be unchanged
        assert external_logger.level == logging.ERROR

        # OpenDXA logger should be DEBUG
        opendxa_logger = DXA_LOGGER.getLogger("opendxa.test.Internal")
        assert opendxa_logger.logger.getEffectiveLevel() == logging.DEBUG

    def test_dana_repl_simulation(self):
        """Test simulation of Dana REPL log level changes."""
        # Configure DXA_LOGGER (simulates REPL startup)
        DXA_LOGGER.configure(level=logging.WARNING)

        # Create REPL-like component
        class REPLComponent(Loggable):
            def __init__(self):
                super().__init__(logger_name="opendxa.dana.exec.repl.TestREPL")

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
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.ERROR)

        # Create test component
        class TestComponent(Loggable):
            def __init__(self):
                super().__init__(logger_name="opendxa.test.LevelTest")

        component = TestComponent()

        # Set the test level via SandboxLogger
        SandboxLogger.set_system_log_level(log_level)

        # Component should have the correct effective level
        assert component.logger.logger.getEffectiveLevel() == log_level.value

    def test_logger_hierarchy_inheritance(self):
        """Test that logger hierarchy inheritance works correctly."""
        # Configure DXA_LOGGER
        DXA_LOGGER.configure(level=logging.WARNING)

        # Set level for opendxa parent
        DXA_LOGGER.setLevel(logging.DEBUG, scope="opendxa")

        # Create child loggers
        child1 = DXA_LOGGER.getLogger("opendxa.module.Child1")
        child2 = DXA_LOGGER.getLogger("opendxa.module.submodule.Child2")

        # Both should inherit DEBUG level (check effective level)
        assert child1.logger.getEffectiveLevel() == logging.DEBUG
        assert child2.logger.getEffectiveLevel() == logging.DEBUG

        # Create even deeper child
        deep_child = DXA_LOGGER.getLogger("opendxa.very.deep.nested.Child")
        assert deep_child.logger.getEffectiveLevel() == logging.DEBUG

    def test_configure_only_called_once(self):
        """Test that configure() is only called once per DXA_LOGGER instance."""
        # Verify initial state
        assert not DXA_LOGGER._configured

        # First configure call should work
        DXA_LOGGER.configure(level=logging.INFO)
        assert DXA_LOGGER._configured
        assert DXA_LOGGER.logger.level == logging.INFO

        # Second configure call should be ignored
        DXA_LOGGER.configure(level=logging.ERROR)
        assert DXA_LOGGER.logger.level == logging.INFO  # Should remain INFO

        # But setLevel should still work
        DXA_LOGGER.setLevel(logging.ERROR)
        assert DXA_LOGGER.logger.level == logging.ERROR
