"""
Unit tests for the Notifiable protocol and Notifier classes.
"""

from unittest.mock import Mock, patch

import pytest

from dana.common.protocols import DictParams, Notifiable, Notifier


class TestNotifiable:
    """Test Notifiable abstract base class."""

    def test_notifiable_is_abstract(self):
        """Test that Notifiable cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Notifiable()

    def test_notifiable_implementation(self):
        """Test that a concrete Notifiable implementation works."""

        class ConcreteNotifiable(Notifiable):
            def __init__(self):
                self.notifications = []

            def notify(self, notifier: object, message: DictParams) -> None:
                self.notifications.append((notifier, message))

        notifiable = ConcreteNotifiable()
        test_message = {"type": "test", "content": "hello"}
        test_notifier = Mock()

        notifiable.notify(test_notifier, test_message)

        assert len(notifiable.notifications) == 1
        assert notifiable.notifications[0] == (test_notifier, test_message)

    def test_notifiable_with_different_message_types(self):
        """Test Notifiable with different message types."""

        class TestNotifiable(Notifiable):
            def __init__(self):
                self.messages = []

            def notify(self, notifier: object, message: DictParams) -> None:
                self.messages.append(message)

        notifiable = TestNotifiable()
        notifier = Mock()

        # Test with different message structures
        messages = [
            {"type": "info", "content": "Information message"},
            {"type": "error", "code": 500, "message": "Server error"},
            {"type": "success", "data": {"result": "completed"}},
            {"type": "warning", "level": "medium", "text": "Warning message"},
        ]

        for message in messages:
            notifiable.notify(notifier, message)

        assert len(notifiable.messages) == 4
        assert notifiable.messages == messages


class TestNotifier:
    """Test Notifier class functionality."""

    def test_notifier_initialization(self):
        """Test Notifier initialization."""
        notifier = Notifier()
        assert hasattr(notifier, "_notifiables")
        assert notifier._notifiables == []

    def test_notifier_with_kwargs(self):
        """Test Notifier initialization with kwargs."""
        notifier = Notifier(custom_param="test", another_param=123)
        assert hasattr(notifier, "_notifiables")
        assert hasattr(notifier, "_kwargs")
        assert notifier._kwargs == {"custom_param": "test", "another_param": 123}

    def test_add_notifier(self):
        """Test adding notifiable objects."""
        notifier = Notifier()
        mock_notifiable1 = Mock(spec=Notifiable)
        mock_notifiable2 = Mock(spec=Notifiable)

        notifier.add_notifier(mock_notifiable1)
        assert len(notifier._notifiables) == 1
        assert mock_notifiable1 in notifier._notifiables

        notifier.add_notifier(mock_notifiable2)
        assert len(notifier._notifiables) == 2
        assert mock_notifiable2 in notifier._notifiables

    def test_add_notifier_none(self):
        """Test adding None notifier (should be ignored)."""
        notifier = Notifier()
        notifier.add_notifier(None)
        assert len(notifier._notifiables) == 0

    def test_with_notifiable_method_chaining(self):
        """Test with_notifiable method chaining."""
        notifier = Notifier()
        mock_notifiable1 = Mock(spec=Notifiable)
        mock_notifiable2 = Mock(spec=Notifiable)

        result = notifier.with_notifiable(mock_notifiable1, mock_notifiable2)

        # Should return self for chaining
        assert result is notifier
        assert len(notifier._notifiables) == 2
        assert mock_notifiable1 in notifier._notifiables
        assert mock_notifiable2 in notifier._notifiables

    def test_remove_notifiable_success(self):
        """Test successful removal of notifiable."""
        notifier = Notifier()
        mock_notifiable1 = Mock(spec=Notifiable)
        mock_notifiable2 = Mock(spec=Notifiable)

        notifier.add_notifier(mock_notifiable1)
        notifier.add_notifier(mock_notifiable2)

        result = notifier.remove_notifiable(mock_notifiable1)

        assert result is True
        assert len(notifier._notifiables) == 1
        assert mock_notifiable1 not in notifier._notifiables
        assert mock_notifiable2 in notifier._notifiables

    def test_remove_notifiable_not_found(self):
        """Test removal of non-existent notifiable."""
        notifier = Notifier()
        mock_notifiable = Mock(spec=Notifiable)

        result = notifier.remove_notifiable(mock_notifiable)

        assert result is False
        assert len(notifier._notifiables) == 0

    def test_send_notification_success(self):
        """Test successful notification sending."""
        notifier = Notifier()
        mock_notifiable1 = Mock(spec=Notifiable)
        mock_notifiable2 = Mock(spec=Notifiable)

        notifier.add_notifier(mock_notifiable1)
        notifier.add_notifier(mock_notifiable2)

        test_message = {"type": "test", "content": "hello"}
        notifier.broadcast(test_message)

        # Both notifiables should receive the notification
        mock_notifiable1.notify.assert_called_once_with(notifier, test_message)
        mock_notifiable2.notify.assert_called_once_with(notifier, test_message)

    def test_send_notification_with_none_notifiables(self):
        """Test notification sending with None notifiables (should be skipped)."""
        notifier = Notifier()
        mock_notifiable = Mock(spec=Notifiable)

        notifier.add_notifier(None)
        notifier.add_notifier(mock_notifiable)

        test_message = {"type": "test", "content": "hello"}
        notifier.broadcast(test_message)

        # Only the valid notifiable should receive the notification
        mock_notifiable.notify.assert_called_once_with(notifier, test_message)

    def test_send_notification_error_handling(self):
        """Test error handling in notification sending."""
        notifier = Notifier()
        mock_notifiable1 = Mock(spec=Notifiable)
        mock_notifiable2 = Mock(spec=Notifiable)

        # Make first notifiable raise an exception
        mock_notifiable1.notify.side_effect = Exception("Test error")

        notifier.add_notifier(mock_notifiable1)
        notifier.add_notifier(mock_notifiable2)

        test_message = {"type": "test", "content": "hello"}

        # Should not raise exception, should continue with other notifiables
        notifier.broadcast(test_message)

        # First notifiable should have been called (and failed)
        mock_notifiable1.notify.assert_called_once_with(notifier, test_message)
        # Second notifiable should still be called
        mock_notifiable2.notify.assert_called_once_with(notifier, test_message)

    @patch("dana_agent.common.protocols.notifiable.logger")
    def test_send_notification_logs_errors(self, mock_logger):
        """Test that notification errors are logged."""
        notifier = Notifier()
        mock_notifiable = Mock(spec=Notifiable)
        mock_notifiable.notify.side_effect = Exception("Test error")

        notifier.add_notifier(mock_notifiable)
        test_message = {"type": "test", "content": "hello"}

        notifier.broadcast(test_message)

        # Should log the error
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "Error sending notification" in error_call
        assert "Test error" in error_call

    def test_send_notification_empty_notifiables(self):
        """Test notification sending with no notifiables."""
        notifier = Notifier()
        test_message = {"type": "test", "content": "hello"}

        # Should not raise any exception
        notifier.broadcast(test_message)


class TestNotifierIntegration:
    """Test Notifier integration with real Notifiable implementations."""

    def test_notifier_with_concrete_notifiable(self):
        """Test Notifier with concrete Notifiable implementation."""

        class TestNotifiable(Notifiable):
            def __init__(self, name: str):
                self.name = name
                self.received_messages = []

            def notify(self, notifier: object, message: DictParams) -> None:
                self.received_messages.append({"from": notifier, "message": message, "timestamp": message.get("timestamp", "unknown")})

        notifier = Notifier()
        notifiable1 = TestNotifiable("notifiable1")
        notifiable2 = TestNotifiable("notifiable2")

        notifier.with_notifiable(notifiable1, notifiable2)

        test_message = {"type": "integration_test", "content": "Testing integration", "timestamp": "2025-01-01T00:00:00Z"}

        notifier.broadcast(test_message)

        # Check both notifiables received the message
        assert len(notifiable1.received_messages) == 1
        assert len(notifiable2.received_messages) == 1

        # Check message content
        msg1 = notifiable1.received_messages[0]
        assert msg1["from"] is notifier
        assert msg1["message"] == test_message

        msg2 = notifiable2.received_messages[0]
        assert msg2["from"] is notifier
        assert msg2["message"] == test_message

    def test_notifier_removal_and_readdition(self):
        """Test removing and re-adding notifiables."""

        class TestNotifiable(Notifiable):
            def __init__(self, name: str):
                self.name = name
                self.call_count = 0

            def notify(self, notifier: object, message: DictParams) -> None:
                self.call_count += 1

        notifier = Notifier()
        notifiable = TestNotifiable("test")

        # Add, send notification, remove, send again, add back, send again
        notifier.add_notifier(notifiable)
        notifier.broadcast({"type": "test1"})
        assert notifiable.call_count == 1

        notifier.remove_notifiable(notifiable)
        notifier.broadcast({"type": "test2"})
        assert notifiable.call_count == 1  # Should not increase

        notifier.add_notifier(notifiable)
        notifier.broadcast({"type": "test3"})
        assert notifiable.call_count == 2  # Should increase again


class TestNotifierEdgeCases:
    """Test Notifier edge cases and error conditions."""

    def test_notifier_with_invalid_notifiable(self):
        """Test Notifier with objects that don't implement Notifiable."""
        notifier = Notifier()

        # Add an object that doesn't implement Notifiable
        invalid_notifiable = Mock()  # No notify method
        notifier.add_notifier(invalid_notifiable)

        test_message = {"type": "test", "content": "hello"}

        # Should handle gracefully (AttributeError when calling notify)
        notifier.broadcast(test_message)

        # The invalid notifiable should have been called and failed
        # (This would raise AttributeError in real usage, but our error handling catches it)

    def test_notifier_duplicate_additions(self):
        """Test adding the same notifiable multiple times."""
        notifier = Notifier()
        mock_notifiable = Mock(spec=Notifiable)

        notifier.add_notifier(mock_notifiable)
        notifier.add_notifier(mock_notifiable)  # Add same notifiable again

        assert len(notifier._notifiables) == 2  # Should allow duplicates
        assert notifier._notifiables.count(mock_notifiable) == 2

        # Sending notification should call it twice
        notifier.broadcast({"type": "test"})
        assert mock_notifiable.notify.call_count == 2

    def test_notifier_remove_duplicate(self):
        """Test removing duplicate notifiables."""
        notifier = Notifier()
        mock_notifiable = Mock(spec=Notifiable)

        notifier.add_notifier(mock_notifiable)
        notifier.add_notifier(mock_notifiable)

        # Remove one instance
        result = notifier.remove_notifiable(mock_notifiable)
        assert result is True
        assert len(notifier._notifiables) == 1

        # Remove the second instance
        result = notifier.remove_notifiable(mock_notifiable)
        assert result is True
        assert len(notifier._notifiables) == 0

        # Try to remove again (should fail)
        result = notifier.remove_notifiable(mock_notifiable)
        assert result is False
