import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import json

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns_manager import DNSManager


class MockOSHandler:
    """Mock OS handler for testing."""
    
    def __init__(self):
        self.dns_configured = False
        self.dns_restored = False
        self.local_dns = "192.168.1.1"
    
    def get_local_dns(self):
        return self.local_dns
    
    def configure_local_dns(self, dns_ips):
        self.dns_configured = True
        return True
    
    def restore_dns_to_dhcp(self):
        self.dns_restored = True
        return True


class MockDNSServer:
    """Mock DNS server for testing."""
    
    def __init__(self, port, resolver):
        self.port = port
        self.resolver = resolver
        self.started = False
        self.stopped = False
    
    def start(self):
        self.started = True
    
    def stop(self):
        self.stopped = True


class MockNotificationManager:
    """Mock notification manager for testing."""
    
    def __init__(self, os_handler):
        self.os_handler = os_handler
        self.notifications = []
    
    def notify_dns_error(self, message):
        self.notifications.append(("dns_error", message))
    
    def notify_dns_change(self, old_dns, new_dns):
        self.notifications.append(("dns_change", old_dns, new_dns))
    
    def notify_service_status(self, status, details=None):
        self.notifications.append(("service_status", status, details))


# Sample DNS list data for testing
SAMPLE_DNS_LIST = [
    {
        "name": "Google Public DNS",
        "primary": "8.8.8.8",
        "secondary": "8.8.4.4",
        "features": ["Fast", "Reliable", "Global availability"]
    },
    {
        "name": "Cloudflare DNS",
        "primary": "1.1.1.1",
        "secondary": "1.0.0.1",
        "features": ["Very fast", "Privacy-focused", "Global"]
    }
]


class TestDNSManager:
    """Test cases for DNSManager class."""

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_init(self, mock_file, mock_notification_manager_class, mock_factory):
        """Test DNSManager initialization."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        manager = DNSManager()
        
        assert manager.os_handler == mock_os_handler
        assert manager.local_dns == "192.168.1.1"
        assert manager.local_port == 53
        assert manager.listen_port == 53
        assert manager.server is None
        assert manager.notification_manager == mock_notification_manager
        # Check that fallback DNS list was loaded correctly 
        expected_fallback = [
            ('8.8.8.8', 53), ('8.8.4.4', 53),
            ('1.1.1.1', 53), ('1.0.0.1', 53)
        ]
        assert manager.fallback_dns_list == expected_fallback

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_init_with_fallback_dns_list(self, mock_file, mock_notification_manager_class, mock_factory):
        """Test DNSManager initialization when dns_list.json file is not found."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        manager = DNSManager()
        
        # Should fall back to default DNS servers
        expected_fallback = [
            ('8.8.8.8', 53),      # Google Primary
            ('8.8.4.4', 53),      # Google Secondary
            ('1.1.1.1', 53),      # Cloudflare Primary
            ('1.0.0.1', 53),      # Cloudflare Secondary
        ]
        assert manager.fallback_dns_list == expected_fallback

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_start_success(self, mock_file, mock_dns_server_class, mock_dns_resolver_class, 
                          mock_notification_manager_class, mock_factory):
        """Test successful DNS manager start."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        manager.start()
        
        # Verify DNS configuration
        assert mock_os_handler.dns_configured is True
        
        # Verify resolver creation with correct parameters
        mock_dns_resolver_class.assert_called_once_with(
            primary_dns="192.168.1.1",
            primary_port=53,
            fallback_dns_list=[
                ('8.8.8.8', 53), ('8.8.4.4', 53),
                ('1.1.1.1', 53), ('1.0.0.1', 53)
            ],
            notification_manager=mock_notification_manager
        )
        
        # Verify server creation and start
        mock_dns_server_class.assert_called_once_with(53, mock_resolver)
        assert mock_server.started is True
        assert manager.server == mock_server
        
        # Verify notifications
        assert len(mock_notification_manager.notifications) == 2
        assert mock_notification_manager.notifications[0] == ("dns_change", "192.168.1.1", "127.0.0.1")
        assert mock_notification_manager.notifications[1][0] == "service_status"
        assert mock_notification_manager.notifications[1][1] == "Started"

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_start_dns_config_failure(self, mock_file, mock_notification_manager_class, mock_factory):
        """Test DNS manager start with DNS configuration failure."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_os_handler.configure_local_dns = Mock(return_value=False)
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        manager = DNSManager()
        manager.start()
        
        # Verify error notification
        assert len(mock_notification_manager.notifications) == 1
        assert mock_notification_manager.notifications[0][0] == "dns_error"
        assert "Failed to configure system DNS settings" in mock_notification_manager.notifications[0][1]
        
        # Verify server was not created
        assert manager.server is None

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_stop_success(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                         mock_notification_manager_class, mock_factory):
        """Test successful DNS manager stop."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        manager.start()  # Start first
        
        # Clear notifications from start
        mock_notification_manager.notifications.clear()
        
        manager.stop()
        
        # Verify server stop
        assert mock_server.stopped is True
        assert manager.server is None
        
        # Verify DNS restoration
        assert mock_os_handler.dns_restored is True
        
        # Verify notifications
        assert len(mock_notification_manager.notifications) == 2
        assert mock_notification_manager.notifications[0] == ("dns_change", "127.0.0.1", "DHCP")
        assert mock_notification_manager.notifications[1] == ("service_status", "Stopped", None)

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_stop_no_server(self, mock_file, mock_notification_manager_class, mock_factory):
        """Test DNS manager stop when no server is running."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        manager = DNSManager()
        manager.stop()  # Stop without starting
        
        # Should not crash and no notifications should be sent
        assert len(mock_notification_manager.notifications) == 0

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_stop_dns_restore_failure(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                                     mock_notification_manager_class, mock_factory):
        """Test DNS manager stop with DNS restoration failure."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_os_handler.restore_dns_to_dhcp = Mock(return_value=False)
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        manager.start()  # Start first
        
        # Clear notifications from start
        mock_notification_manager.notifications.clear()
        
        manager.stop()
        
        # Verify error notification
        assert len(mock_notification_manager.notifications) == 2
        assert mock_notification_manager.notifications[0][0] == "dns_error"
        assert "Failed to restore system DNS settings" in mock_notification_manager.notifications[0][1]
        assert mock_notification_manager.notifications[1] == ("service_status", "Stopped", None)

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_start_stop_cycle(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                             mock_notification_manager_class, mock_factory):
        """Test complete start-stop cycle."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        
        # Start
        manager.start()
        assert mock_server.started is True
        assert manager.server == mock_server
        
        # Stop
        manager.stop()
        assert mock_server.stopped is True
        assert manager.server is None

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_multiple_stops(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                           mock_notification_manager_class, mock_factory):
        """Test multiple stop calls don't cause issues."""
        # Setup mocks
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        manager.start()
        
        # Multiple stops
        manager.stop()
        manager.stop()
        manager.stop()
        
        # Should not cause any issues
        assert manager.server is None

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_default_configuration_values(self, mock_file, mock_notification_manager_class, mock_factory):
        """Test that default configuration values are set correctly."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        manager = DNSManager()
        
        # Test default values
        assert manager.local_port == 53
        assert manager.listen_port == 53
        assert isinstance(manager.fallback_dns_list, list)
        assert len(manager.fallback_dns_list) > 0

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_resolver_configuration(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                                   mock_notification_manager_class, mock_factory):
        """Test that DNS resolver is configured correctly."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        manager.start()
        
        # Verify resolver was created with correct parameters
        mock_dns_resolver_class.assert_called_once_with(
            primary_dns="192.168.1.1",
            primary_port=53,
            fallback_dns_list=[
                ('8.8.8.8', 53), ('8.8.4.4', 53),
                ('1.1.1.1', 53), ('1.0.0.1', 53)
            ],
            notification_manager=mock_notification_manager
        )

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_server_configuration(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                                 mock_notification_manager_class, mock_factory):
        """Test that DNS server is configured correctly."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        manager.start()
        
        # Verify server was created with correct parameters
        mock_dns_server_class.assert_called_once_with(53, mock_resolver)

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('dns_manager.DNSResolver')
    @patch('dns_manager.DNSServer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps(SAMPLE_DNS_LIST))
    def test_notification_integration(self, mock_file, mock_dns_server_class, mock_dns_resolver_class,
                                     mock_notification_manager_class, mock_factory):
        """Test integration with notification manager."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        mock_resolver = Mock()
        mock_dns_resolver_class.return_value = mock_resolver
        
        mock_server = MockDNSServer(53, mock_resolver)
        mock_dns_server_class.return_value = mock_server
        
        manager = DNSManager()
        
        # Start and verify notifications
        manager.start()
        start_notifications = len(mock_notification_manager.notifications)
        assert start_notifications >= 2  # DNS change + service status
        
        # Stop and verify additional notifications
        manager.stop()
        stop_notifications = len(mock_notification_manager.notifications)
        assert stop_notifications > start_notifications

    @patch('dns_manager.OSHandlerFactory.create_handler')
    @patch('dns_manager.NotificationManager')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_fallback_dns_list_invalid_json(self, mock_file, mock_notification_manager_class, mock_factory):
        """Test fallback DNS list loading with invalid JSON."""
        mock_os_handler = MockOSHandler()
        mock_factory.return_value = mock_os_handler
        mock_notification_manager = MockNotificationManager(mock_os_handler)
        mock_notification_manager_class.return_value = mock_notification_manager
        
        manager = DNSManager()
        
        # Should fall back to default DNS servers on JSON parse error
        expected_fallback = [
            ('8.8.8.8', 53),      # Google Primary
            ('8.8.4.4', 53),      # Google Secondary
            ('1.1.1.1', 53),      # Cloudflare Primary
            ('1.0.0.1', 53),      # Cloudflare Secondary
        ]
        assert manager.fallback_dns_list == expected_fallback 