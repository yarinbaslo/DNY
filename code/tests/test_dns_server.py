import pytest
from unittest.mock import Mock, patch, MagicMock
import socket
import threading
import time
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns.server import DNSServer


class MockResolver:
    """Mock DNS resolver for testing."""
    
    def __init__(self):
        self.resolve_calls = []
    
    def resolve(self, query_data):
        self.resolve_calls.append(query_data)
        return b"mock_response_data"


class TestDNSServer:
    """Test cases for DNSServer class."""

    def test_init(self):
        """Test DNSServer initialization."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)  # Use non-privileged port for testing
        
        assert server.port == 5353
        assert server.resolver == mock_resolver
        assert server.running is False
        assert server.server_socket is None

    @patch('socket.socket')
    def test_start_success(self, mock_socket_class):
        """Test successful DNS server start."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock threading to avoid actual thread creation
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            
            server.start()
            
            # Verify socket setup
            mock_socket.bind.assert_called_once_with(('', 5353))
            mock_socket.settimeout.assert_called_once_with(1.0)
            
            # Verify thread creation and start
            mock_thread_class.assert_called_once_with(target=server._run_server)
            mock_thread.start.assert_called_once()
            
            assert server.running is True
            assert server.server_socket == mock_socket

    @patch('socket.socket')
    def test_start_bind_error(self, mock_socket_class):
        """Test DNS server start with bind error."""
        mock_resolver = MockResolver()
        server = DNSServer(53, mock_resolver)  # Privileged port likely to fail
        
        # Mock socket that fails to bind
        mock_socket = Mock()
        mock_socket.bind.side_effect = OSError("Permission denied")
        mock_socket_class.return_value = mock_socket
        
        with patch('logging.error') as mock_log_error:
            server.start()
            
            # Verify error was logged
            mock_log_error.assert_called()
            assert server.running is False
            assert server.server_socket is None

    def test_stop_when_not_running(self):
        """Test stopping server when it's not running."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Should not raise any errors
        server.stop()
        assert server.running is False

    @patch('socket.socket')
    def test_stop_when_running(self, mock_socket_class):
        """Test stopping server when it's running."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Start server first
        with patch('threading.Thread'):
            server.start()
        
        # Stop server
        server.stop()
        
        assert server.running is False
        mock_socket.close.assert_called_once()

    @patch('socket.socket')
    def test_run_server_receive_and_respond(self, mock_socket_class):
        """Test server receiving and responding to DNS queries."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock receiving data
        query_data = b"mock_query_data"
        client_address = ("192.168.1.100", 12345)
        mock_socket.recvfrom.side_effect = [
            (query_data, client_address),
            socket.timeout()  # Second call times out to exit loop
        ]
        
        # Set up server state
        server.server_socket = mock_socket
        server.running = True
        
        # Run server (will exit after timeout)
        server._run_server()
        
        # Verify query was processed
        assert len(mock_resolver.resolve_calls) == 1
        assert mock_resolver.resolve_calls[0] == query_data
        
        # Verify response was sent
        mock_socket.sendto.assert_called_once_with(b"mock_response_data", client_address)

    @patch('socket.socket')
    def test_run_server_resolver_returns_none(self, mock_socket_class):
        """Test server behavior when resolver returns None."""
        mock_resolver = Mock()
        mock_resolver.resolve.return_value = None
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock receiving data
        query_data = b"mock_query_data"
        client_address = ("192.168.1.100", 12345)
        mock_socket.recvfrom.side_effect = [
            (query_data, client_address),
            socket.timeout()  # Second call times out to exit loop
        ]
        
        # Set up server state
        server.server_socket = mock_socket
        server.running = True
        
        # Run server (will exit after timeout)
        server._run_server()
        
        # Verify query was processed but no response sent
        mock_resolver.resolve.assert_called_once_with(query_data)
        mock_socket.sendto.assert_not_called()

    @patch('socket.socket')
    def test_run_server_socket_error(self, mock_socket_class):
        """Test server behavior with socket errors."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock socket error
        mock_socket.recvfrom.side_effect = socket.error("Network error")
        
        # Set up server state
        server.server_socket = mock_socket
        server.running = True
        
        with patch('logging.error') as mock_log_error:
            server._run_server()
            
            # Verify error was logged
            mock_log_error.assert_called()

    @patch('socket.socket')
    def test_run_server_general_exception(self, mock_socket_class):
        """Test server behavior with general exceptions."""
        mock_resolver = Mock()
        mock_resolver.resolve.side_effect = Exception("Resolver error")
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock receiving data
        query_data = b"mock_query_data"
        client_address = ("192.168.1.100", 12345)
        mock_socket.recvfrom.side_effect = [
            (query_data, client_address),
            socket.timeout()  # Second call times out to exit loop
        ]
        
        # Set up server state
        server.server_socket = mock_socket
        server.running = True
        
        with patch('logging.error') as mock_log_error:
            server._run_server()
            
            # Verify error was logged
            mock_log_error.assert_called()

    @patch('socket.socket')
    def test_run_server_stops_when_running_false(self, mock_socket_class):
        """Test that server loop exits when running is set to False."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock timeout to simulate no incoming data
        mock_socket.recvfrom.side_effect = socket.timeout()
        
        # Set up server state
        server.server_socket = mock_socket
        server.running = True
        
        # Stop server after a short delay
        def stop_server():
            time.sleep(0.1)
            server.running = False
        
        stop_thread = threading.Thread(target=stop_server)
        stop_thread.start()
        
        # Run server (should exit when running becomes False)
        server._run_server()
        
        stop_thread.join()
        assert server.running is False

    def test_multiple_start_calls(self):
        """Test that multiple start calls don't cause issues."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        with patch('socket.socket') as mock_socket_class, \
             patch('threading.Thread') as mock_thread_class:
            
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            
            # Start server multiple times
            server.start()
            server.start()
            server.start()
            
            # Should only create one thread
            assert mock_thread_class.call_count == 1
            assert mock_thread.start.call_count == 1

    def test_multiple_stop_calls(self):
        """Test that multiple stop calls don't cause issues."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = Mock()
            mock_socket_class.return_value = mock_socket
            
            with patch('threading.Thread'):
                server.start()
            
            # Stop server multiple times
            server.stop()
            server.stop()
            server.stop()
            
            # Should only close socket once
            assert mock_socket.close.call_count == 1

    @patch('socket.socket')
    def test_server_handles_concurrent_requests(self, mock_socket_class):
        """Test server handling multiple concurrent requests."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Mock socket
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        # Mock multiple incoming requests
        requests = [
            (b"query1", ("192.168.1.100", 12345)),
            (b"query2", ("192.168.1.101", 12346)),
            (b"query3", ("192.168.1.102", 12347)),
        ]
        
        mock_socket.recvfrom.side_effect = requests + [socket.timeout()]
        
        # Set up server state
        server.server_socket = mock_socket
        server.running = True
        
        # Run server
        server._run_server()
        
        # Verify all queries were processed
        assert len(mock_resolver.resolve_calls) == 3
        assert mock_resolver.resolve_calls == [b"query1", b"query2", b"query3"]
        
        # Verify all responses were sent
        assert mock_socket.sendto.call_count == 3

    def test_server_port_validation(self):
        """Test server with different port values."""
        mock_resolver = MockResolver()
        
        # Test valid ports
        valid_ports = [53, 5353, 8053, 65535]
        for port in valid_ports:
            server = DNSServer(port, mock_resolver)
            assert server.port == port
        
        # Test edge cases
        server = DNSServer(1, mock_resolver)
        assert server.port == 1
        
        server = DNSServer(65535, mock_resolver)
        assert server.port == 65535

    @patch('socket.socket')
    def test_server_socket_configuration(self, mock_socket_class):
        """Test that server socket is configured correctly."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        with patch('threading.Thread'):
            server.start()
        
        # Verify socket type and configuration
        mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
        mock_socket.bind.assert_called_once_with(('', 5353))
        mock_socket.settimeout.assert_called_once_with(1.0)

    @patch('socket.socket')
    def test_server_logging(self, mock_socket_class):
        """Test that server logs important events."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        
        with patch('logging.info') as mock_log_info, \
             patch('threading.Thread'):
            
            server.start()
            
            # Verify start was logged
            mock_log_info.assert_called()

    def test_server_thread_safety(self):
        """Test that server operations are thread-safe."""
        mock_resolver = MockResolver()
        server = DNSServer(5353, mock_resolver)
        
        # Test that start/stop can be called from different threads
        def start_server():
            with patch('socket.socket'), patch('threading.Thread'):
                server.start()
        
        def stop_server():
            server.stop()
        
        start_thread = threading.Thread(target=start_server)
        stop_thread = threading.Thread(target=stop_server)
        
        start_thread.start()
        start_thread.join()
        
        stop_thread.start()
        stop_thread.join()
        
        # Should not raise any exceptions
        assert True 