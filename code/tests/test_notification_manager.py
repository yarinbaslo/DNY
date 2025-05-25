import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notification_manager import NotificationManager
from os_handlers.base import OSHandler


class MockOSHandler(OSHandler):
    """Mock OS handler for testing."""
    
    def __init__(self):
        self.notifications = []
    
    def get_local_dns(self) -> str:
        return "192.168.1.1"
    
    def get_active_interface(self) -> str:
        return "eth0"
    
    def set_dns(self, dns_ip: str = "127.0.0.1") -> bool:
        return True
    
    def notify(self, title: str, message: str, notification_type: str = "info", 
               urgency: str = "normal", timeout: int = 5000) -> None:
        self.notifications.append({
            "title": title,
            "message": message,
            "type": notification_type,
            "urgency": urgency,
            "timeout": timeout
        })


class TestNotificationManager:
    """Test cases for NotificationManager class."""

    def test_init(self):
        """Test NotificationManager initialization."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        assert manager.os_handler == mock_os_handler
        assert manager.notification_history == []
        assert hasattr(manager, 'logger')

    def test_notify_basic(self):
        """Test basic notification functionality."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager, '_log_notification') as mock_log:
            manager.notify("Test Title", "Test Message", "info")
            
            # Check that logging was called
            mock_log.assert_called_once_with("Test Title", "Test Message", "info")
            
            # Check that OS handler was called
            assert len(mock_os_handler.notifications) == 1
            notification = mock_os_handler.notifications[0]
            assert notification["title"] == "Test Title"
            assert notification["message"] == "Test Message"
            assert notification["type"] == "info"
            
            # Check that history was updated
            assert len(manager.notification_history) == 1
            history_entry = manager.notification_history[0]
            assert history_entry["title"] == "Test Title"
            assert history_entry["message"] == "Test Message"
            assert history_entry["type"] == "info"
            assert "timestamp" in history_entry

    def test_notify_default_type(self):
        """Test notification with default type."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        manager.notify("Title", "Message")
        
        # Check default type is "info"
        assert manager.notification_history[0]["type"] == "info"
        assert mock_os_handler.notifications[0]["type"] == "info"

    def test_log_notification_info(self):
        """Test logging of info notifications."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager.logger, 'info') as mock_info:
            manager._log_notification("Title", "Message", "info")
            mock_info.assert_called_once_with("Title: Message")

    def test_log_notification_warning(self):
        """Test logging of warning notifications."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager.logger, 'warning') as mock_warning:
            manager._log_notification("Title", "Message", "warning")
            mock_warning.assert_called_once_with("Title: Message")

    def test_log_notification_error(self):
        """Test logging of error notifications."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager.logger, 'error') as mock_error:
            manager._log_notification("Title", "Message", "error")
            mock_error.assert_called_once_with("Title: Message")

    def test_get_notification_history(self):
        """Test getting notification history."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        # Initially empty
        assert manager.get_notification_history() == []
        
        # Add some notifications
        manager.notify("Title1", "Message1", "info")
        manager.notify("Title2", "Message2", "warning")
        
        history = manager.get_notification_history()
        assert len(history) == 2
        assert history[0]["title"] == "Title1"
        assert history[1]["title"] == "Title2"

    def test_clear_notification_history(self):
        """Test clearing notification history."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        # Add some notifications
        manager.notify("Title1", "Message1")
        manager.notify("Title2", "Message2")
        assert len(manager.notification_history) == 2
        
        # Clear history
        manager.clear_notification_history()
        assert len(manager.notification_history) == 0

    def test_notify_dns_change(self):
        """Test DNS change notification."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager, 'notify') as mock_notify:
            manager.notify_dns_change("8.8.8.8", "1.1.1.1")
            
            mock_notify.assert_called_once_with(
                "DNS Server Changed",
                "DNS server changed from 8.8.8.8 to 1.1.1.1",
                "info"
            )

    def test_notify_dns_error(self):
        """Test DNS error notification."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager, 'notify') as mock_notify:
            manager.notify_dns_error("Failed to configure DNS")
            
            mock_notify.assert_called_once_with(
                "DNS Configuration Error",
                "Failed to configure DNS",
                "error"
            )

    def test_notify_service_status_without_details(self):
        """Test service status notification without details."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager, 'notify') as mock_notify:
            manager.notify_service_status("Started")
            
            mock_notify.assert_called_once_with(
                "Service Status Update",
                "DNS Forwarder Service: Started",
                "info"
            )

    def test_notify_service_status_with_details(self):
        """Test service status notification with details."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager, 'notify') as mock_notify:
            manager.notify_service_status("Started", "Using primary DNS: 8.8.8.8")
            
            expected_message = "DNS Forwarder Service: Started\nDetails: Using primary DNS: 8.8.8.8"
            mock_notify.assert_called_once_with(
                "Service Status Update",
                expected_message,
                "info"
            )

    def test_notify_domain_inappropriate_content(self):
        """Test inappropriate content notification."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch.object(manager, 'notify') as mock_notify:
            manager.notify_domain_inappropriate_content("example.com", "Contains malware")
            
            expected_message = "The domain example.com was flagged for inappropriate content.\nReason: Contains malware"
            mock_notify.assert_called_once_with(
                "Inappropriate Content Alert",
                expected_message,
                "warning"
            )

    def test_multiple_notifications_history_order(self):
        """Test that notification history maintains chronological order."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        # Add notifications with slight delay to ensure different timestamps
        with patch('notification_manager.datetime') as mock_datetime:
            # Mock datetime to return predictable timestamps
            mock_datetime.now.side_effect = [
                datetime(2023, 1, 1, 10, 0, 0),
                datetime(2023, 1, 1, 10, 0, 1),
                datetime(2023, 1, 1, 10, 0, 2)
            ]
            mock_datetime.now().isoformat.side_effect = [
                "2023-01-01T10:00:00",
                "2023-01-01T10:00:01", 
                "2023-01-01T10:00:02"
            ]
            
            manager.notify("First", "Message1")
            manager.notify("Second", "Message2")
            manager.notify("Third", "Message3")
        
        history = manager.get_notification_history()
        assert len(history) == 3
        assert history[0]["title"] == "First"
        assert history[1]["title"] == "Second"
        assert history[2]["title"] == "Third"

    def test_notification_timestamp_format(self):
        """Test that notification timestamps are in ISO format."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        with patch('notification_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T10:00:00"
            
            manager.notify("Test", "Message")
            
            history = manager.get_notification_history()
            assert history[0]["timestamp"] == "2023-01-01T10:00:00"

    def test_os_handler_integration(self):
        """Test integration with OS handler."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        manager.notify("Test Title", "Test Message", "warning")
        
        # Check that OS handler received the notification
        assert len(mock_os_handler.notifications) == 1
        notification = mock_os_handler.notifications[0]
        assert notification["title"] == "Test Title"
        assert notification["message"] == "Test Message"
        assert notification["type"] == "warning"

    def test_notification_types(self):
        """Test different notification types."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        types = ["info", "warning", "error", "custom"]
        
        for notification_type in types:
            manager.notify(f"Title {notification_type}", f"Message {notification_type}", notification_type)
        
        history = manager.get_notification_history()
        assert len(history) == 4
        
        for i, notification_type in enumerate(types):
            assert history[i]["type"] == notification_type

    def test_empty_strings_handling(self):
        """Test handling of empty strings in notifications."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        manager.notify("", "", "info")
        
        history = manager.get_notification_history()
        assert len(history) == 1
        assert history[0]["title"] == ""
        assert history[0]["message"] == ""
        assert history[0]["type"] == "info"

    def test_special_characters_in_notifications(self):
        """Test handling of special characters in notifications."""
        mock_os_handler = MockOSHandler()
        manager = NotificationManager(mock_os_handler)
        
        special_title = "Title with émojis 🚀 and symbols @#$%"
        special_message = "Message with\nnewlines and\ttabs"
        
        manager.notify(special_title, special_message, "info")
        
        history = manager.get_notification_history()
        assert history[0]["title"] == special_title
        assert history[0]["message"] == special_message 