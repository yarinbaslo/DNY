import pytest
from unittest.mock import Mock, patch, MagicMock
import socket
import struct
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns.resolver import DNSResolver
from ip_blocker import IPBlocker
from content_checker import ContentChecker
from dns_cache import DNSCache


class MockNotificationManager:
    """Mock notification manager for testing."""
    
    def __init__(self):
        self.notifications = []
    
    def notify_dns_change(self, old_dns, new_dns):
        self.notifications.append(("dns_change", old_dns, new_dns))
    
    def notify_domain_inappropriate_content(self, domain, reason):
        self.notifications.append(("inappropriate_content", domain, reason))


class TestDNSResolver:
    """Test cases for DNSResolver class."""

    def test_init(self):
        """Test DNSResolver initialization."""
        mock_notification_manager = MockNotificationManager()
        
        resolver = DNSResolver(
            primary_dns="8.8.8.8",
            primary_port=53,
            fallback_dns="1.1.1.1", 
            fallback_port=53,
            notification_manager=mock_notification_manager
        )
        
        assert resolver.primary_dns == "8.8.8.8"
        assert resolver.primary_port == 53
        assert resolver.fallback_dns == "1.1.1.1"
        assert resolver.fallback_port == 53
        assert resolver.notification_manager == mock_notification_manager
        assert isinstance(resolver.ip_blocker, IPBlocker)
        assert isinstance(resolver.cache, DNSCache)
        assert isinstance(resolver.content_checker, ContentChecker)

    def test_set_content_check_api_key(self):
        """Test setting content check API key."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        with patch.object(resolver.content_checker, 'set_api_key') as mock_set_key:
            resolver.set_content_check_api_key("test-api-key")
            mock_set_key.assert_called_once_with("test-api-key")

    def test_resolve_cache_hit(self):
        """Test DNS resolution with cache hit."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = b"test_query"
        cached_response = b"cached_response"
        
        with patch.object(resolver.cache, 'get', return_value=cached_response):
            result = resolver.resolve(query_data)
            
            assert result == cached_response

    def test_resolve_primary_success(self):
        """Test DNS resolution with primary DNS success."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = b"test_query"
        response_data = b"response_data"
        
        with patch.object(resolver.cache, 'get', return_value=None), \
             patch.object(resolver, '_try_resolve', side_effect=[response_data, None]) as mock_try_resolve, \
             patch.object(resolver.cache, 'set') as mock_cache_set:
            
            result = resolver.resolve(query_data)
            
            assert result == response_data
            mock_try_resolve.assert_called_once_with(query_data, "8.8.8.8", 53, is_primary=True)
            mock_cache_set.assert_called_once_with(query_data, response_data)

    def test_resolve_fallback_success(self):
        """Test DNS resolution with fallback DNS success."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = b"test_query"
        response_data = b"response_data"
        
        with patch.object(resolver.cache, 'get', return_value=None), \
             patch.object(resolver, '_try_resolve', side_effect=[None, response_data]) as mock_try_resolve, \
             patch.object(resolver.cache, 'set') as mock_cache_set, \
             patch.object(resolver, '_extract_domain_name', return_value=["example", "com"]), \
             patch.object(resolver.content_checker, 'check_domain', return_value=(True, "Safe", "other")):
            
            result = resolver.resolve(query_data)
            
            assert result == response_data
            assert mock_try_resolve.call_count == 2
            mock_cache_set.assert_called_once_with(query_data, response_data)

    def test_resolve_inappropriate_content_detected(self):
        """Test DNS resolution with inappropriate content detection."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = b"test_query"
        response_data = b"response_data"
        
        with patch.object(resolver.cache, 'get', return_value=None), \
             patch.object(resolver, '_try_resolve', side_effect=[None, response_data]), \
             patch.object(resolver.cache, 'set'), \
             patch.object(resolver, '_extract_domain_name', return_value=["malicious", "com"]), \
             patch.object(resolver.content_checker, 'check_domain', return_value=(False, "Contains malware", "malicious")):
            
            result = resolver.resolve(query_data)
            
            assert result == response_data
            # Check that notification was sent
            assert len(mock_notification_manager.notifications) == 1
            notification = mock_notification_manager.notifications[0]
            assert notification[0] == "inappropriate_content"
            assert notification[1] == "malicious.com"
            assert notification[2] == "Contains malware"

    def test_resolve_both_dns_fail(self):
        """Test DNS resolution when both primary and fallback fail."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = b"test_query"
        
        with patch.object(resolver.cache, 'get', return_value=None), \
             patch.object(resolver, '_try_resolve', return_value=None):
            
            result = resolver.resolve(query_data)
            
            assert result is None

    @patch('socket.socket')
    def test_try_resolve_success(self, mock_socket_class):
        """Test successful DNS resolution attempt."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Create mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock response data with valid DNS response structure
        query_data = struct.pack('!H', 12345) + b"rest_of_query"  # Query ID + data
        response_data = struct.pack('!HHHHHH', 12345, 0x8180, 1, 1, 0, 0) + b"response_data"
        
        mock_socket.recvfrom.return_value = (response_data, ("8.8.8.8", 53))
        
        with patch.object(resolver, '_validate_response_ips', return_value=True):
            result = resolver._try_resolve(query_data, "8.8.8.8", 53, is_primary=True)
            
            assert result == response_data
            mock_socket.sendto.assert_called_once_with(query_data, ("8.8.8.8", 53))
            mock_socket.close.assert_called_once()

    @patch('socket.socket')
    def test_try_resolve_timeout(self, mock_socket_class):
        """Test DNS resolution attempt with timeout."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Create mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.side_effect = socket.timeout("Timeout")
        
        query_data = struct.pack('!H', 12345) + b"rest_of_query"
        
        result = resolver._try_resolve(query_data, "8.8.8.8", 53, is_primary=True)
        
        assert result is None
        mock_socket.close.assert_called_once()

    @patch('socket.socket')
    def test_try_resolve_blocked_ip(self, mock_socket_class):
        """Test DNS resolution attempt with blocked IP in response."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Create mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        query_data = struct.pack('!H', 12345) + b"rest_of_query"
        response_data = struct.pack('!HHHHHH', 12345, 0x8180, 1, 1, 0, 0) + b"response_data"
        
        mock_socket.recvfrom.return_value = (response_data, ("8.8.8.8", 53))
        
        with patch.object(resolver, '_validate_response_ips', return_value=False):
            result = resolver._try_resolve(query_data, "8.8.8.8", 53, is_primary=True)
            
            assert result is None

    @patch('socket.socket')
    def test_try_resolve_no_answers(self, mock_socket_class):
        """Test DNS resolution attempt with no answers in response."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Create mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        query_data = struct.pack('!H', 12345) + b"rest_of_query"
        # Response with 0 answers
        response_data = struct.pack('!HHHHHH', 12345, 0x8180, 1, 0, 0, 0) + b"response_data"
        
        mock_socket.recvfrom.return_value = (response_data, ("8.8.8.8", 53))
        
        result = resolver._try_resolve(query_data, "8.8.8.8", 53, is_primary=True)
        
        assert result is None

    def test_validate_response_ips_a_record_valid(self):
        """Test IP validation with valid A record."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Create mock response with A record for 8.8.8.8
        response_data = (
            b'\x00\x00'  # Query ID
            b'\x81\x80'  # Flags
            b'\x00\x01'  # Questions
            b'\x00\x01'  # Answers
            b'\x00\x00'  # Authority
            b'\x00\x00'  # Additional
            b'\x00'      # End of question section
            b'\x00\x01'  # Type A
            b'\x00\x01'  # Class IN
            b'\xc0\x0c'  # Name (compressed)
            b'\x00\x01'  # Type A
            b'\x00\x01'  # Class IN
            b'\x00\x00\x00\x3c'  # TTL
            b'\x00\x04'  # Data length
            b'\x08\x08\x08\x08'  # IP 8.8.8.8
        )
        
        with patch.object(resolver.ip_blocker, 'is_blocked_ip', return_value=(False, "Looks okay")):
            result = resolver._validate_response_ips(response_data)
            assert result is True

    def test_validate_response_ips_a_record_blocked(self):
        """Test IP validation with blocked A record."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Create mock response with A record for 127.0.0.1 (blocked)
        response_data = (
            b'\x00\x00'  # Query ID
            b'\x81\x80'  # Flags
            b'\x00\x01'  # Questions
            b'\x00\x01'  # Answers
            b'\x00\x00'  # Authority
            b'\x00\x00'  # Additional
            b'\x00'      # End of question section
            b'\x00\x01'  # Type A
            b'\x00\x01'  # Class IN
            b'\xc0\x0c'  # Name (compressed)
            b'\x00\x01'  # Type A
            b'\x00\x01'  # Class IN
            b'\x00\x00\x00\x3c'  # TTL
            b'\x00\x04'  # Data length
            b'\x7f\x00\x00\x01'  # IP 127.0.0.1
        )
        
        with patch.object(resolver.ip_blocker, 'is_blocked_ip', return_value=(True, "Loopback IP")):
            result = resolver._validate_response_ips(response_data)
            assert result is False

    def test_validate_response_ips_exception(self):
        """Test IP validation with exception during parsing."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Invalid response data
        response_data = b"invalid_data"
        
        result = resolver._validate_response_ips(response_data)
        assert result is False

    def test_get_record_type_name(self):
        """Test getting record type names."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        test_cases = [
            (1, "A"),
            (28, "AAAA"),
            (5, "CNAME"),
            (6, "SOA"),
            (15, "MX"),
            (16, "TXT"),
            (65, "HTTPS"),
            (999, "Unknown (999)")
        ]
        
        for record_type, expected_name in test_cases:
            result = resolver._get_record_type_name(record_type)
            assert result == expected_name

    def test_extract_domain_name_simple(self):
        """Test domain name extraction from DNS data."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Simple domain name: example.com
        data = b'\x07example\x03com\x00'
        
        result = resolver._extract_domain_name(data, 0)
        assert result == ["example", "com"]

    def test_extract_domain_name_empty(self):
        """Test domain name extraction with empty data."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Empty or invalid data
        data = b'\x00'
        
        result = resolver._extract_domain_name(data, 0)
        assert result == []

    def test_extract_domain_name_exception(self):
        """Test domain name extraction with exception."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        # Data that will cause an exception
        data = b''
        
        result = resolver._extract_domain_name(data, 0)
        assert result == []

    def test_fallback_dns_notification(self):
        """Test that fallback DNS usage triggers notification."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = struct.pack('!H', 12345) + b"rest_of_query"
        response_data = struct.pack('!HHHHHH', 12345, 0x8180, 1, 1, 0, 0) + b"response_data"
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket
            mock_socket.recvfrom.return_value = (response_data, ("1.1.1.1", 53))
            
            with patch.object(resolver, '_validate_response_ips', return_value=True):
                result = resolver._try_resolve(query_data, "1.1.1.1", 53, is_primary=False)
                
                assert result == response_data
                # Check that DNS change notification was sent
                assert len(mock_notification_manager.notifications) == 1
                notification = mock_notification_manager.notifications[0]
                assert notification[0] == "dns_change"
                assert notification[1] == "8.8.8.8"  # primary DNS
                assert notification[2] == "1.1.1.1"  # fallback DNS

    def test_integration_resolve_flow(self):
        """Test complete resolution flow integration."""
        mock_notification_manager = MockNotificationManager()
        resolver = DNSResolver("8.8.8.8", 53, "1.1.1.1", 53, mock_notification_manager)
        
        query_data = b"test_query"
        
        # Test cache miss -> primary fail -> fallback success -> content check -> cache store
        with patch.object(resolver.cache, 'get', return_value=None), \
             patch.object(resolver, '_try_resolve', side_effect=[None, b"response"]), \
             patch.object(resolver.cache, 'set') as mock_cache_set, \
             patch.object(resolver, '_extract_domain_name', return_value=["safe", "com"]), \
             patch.object(resolver.content_checker, 'check_domain', return_value=(True, "Safe domain", "business")):
            
            result = resolver.resolve(query_data)
            
            assert result == b"response"
            mock_cache_set.assert_called_once_with(query_data, b"response") 