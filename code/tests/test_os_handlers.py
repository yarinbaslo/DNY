import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from os_handlers.base import OSHandler
from os_handlers.factory import OSHandlerFactory


class TestOSHandler:
    """Test cases for OSHandler base class."""

    def test_abstract_methods(self):
        """Test that OSHandler is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            OSHandler()

    def test_configure_local_dns_default_implementation(self):
        """Test the default implementation of configure_local_dns."""
        # Create a concrete implementation for testing
        class ConcreteOSHandler(OSHandler):
            def get_local_dns(self):
                return "192.168.1.1"
            
            def get_active_interface(self):
                return "eth0"
            
            def set_dns(self, dns_ip="127.0.0.1"):
                return True
            
            def notify(self, title, message, notification_type="info", urgency="normal", timeout=5000):
                pass
        
        handler = ConcreteOSHandler()
        
        # Test that configure_local_dns calls set_dns with the first IP
        with patch.object(handler, 'set_dns', return_value=True) as mock_set_dns:
            result = handler.configure_local_dns(["127.0.0.1", "8.8.8.8"])
            mock_set_dns.assert_called_once_with(["127.0.0.1", "8.8.8.8"])
            assert result is True


class TestOSHandlerFactory:
    """Test cases for OSHandlerFactory."""

    @patch('platform.system')
    def test_create_handler_windows(self, mock_system):
        """Test creating Windows handler."""
        mock_system.return_value = "Windows"
        
        with patch('os_handlers.factory.WindowsHandler') as mock_windows_handler:
            mock_instance = Mock()
            mock_windows_handler.return_value = mock_instance
            
            result = OSHandlerFactory.create_handler()
            
            mock_windows_handler.assert_called_once()
            assert result == mock_instance

    @patch('platform.system')
    def test_create_handler_linux(self, mock_system):
        """Test creating Linux handler."""
        mock_system.return_value = "Linux"
        
        with patch('os_handlers.factory.LinuxHandler') as mock_linux_handler:
            mock_instance = Mock()
            mock_linux_handler.return_value = mock_instance
            
            result = OSHandlerFactory.create_handler()
            
            mock_linux_handler.assert_called_once()
            assert result == mock_instance

    @patch('platform.system')
    def test_create_handler_macos(self, mock_system):
        """Test creating macOS handler."""
        mock_system.return_value = "Darwin"
        
        with patch('os_handlers.factory.MacOSHandler') as mock_macos_handler:
            mock_instance = Mock()
            mock_macos_handler.return_value = mock_instance
            
            result = OSHandlerFactory.create_handler()
            
            mock_macos_handler.assert_called_once()
            assert result == mock_instance

    @patch('platform.system')
    def test_create_handler_unsupported(self, mock_system):
        """Test creating handler for unsupported OS."""
        mock_system.return_value = "UnsupportedOS"
        
        with pytest.raises(OSError) as exc_info:
            OSHandlerFactory.create_handler()
        
        assert "Unsupported operating system: UnsupportedOS" in str(exc_info.value)


# Test specific OS handlers if they can be imported
try:
    from os_handlers.windows import WindowsHandler
    
    class TestWindowsHandler:
        """Test cases for WindowsHandler."""
        
        def test_init(self):
            """Test WindowsHandler initialization."""
            handler = WindowsHandler()
            assert hasattr(handler, 'logger')
        
        @patch('subprocess.run')
        def test_get_local_dns_success(self, mock_run):
            """Test getting local DNS on Windows."""
            handler = WindowsHandler()
            
            # Mock successful netsh command output
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "DNS Servers configured through DHCP: 192.168.1.1"
            mock_run.return_value = mock_result
            
            result = handler.get_local_dns()
            assert result == "192.168.1.1"
        
        @patch('subprocess.run')
        def test_get_local_dns_failure(self, mock_run):
            """Test getting local DNS failure on Windows."""
            handler = WindowsHandler()
            
            # Mock failed netsh command
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            
            result = handler.get_local_dns()
            assert result == "8.8.8.8"  # Should return default
        
        @patch('subprocess.run')
        def test_set_dns_success(self, mock_run):
            """Test setting DNS on Windows."""
            handler = WindowsHandler()
            
            # Mock successful commands
            mock_run.return_value.returncode = 0
            
            with patch.object(handler, 'get_active_interface', return_value="Wi-Fi"):
                result = handler.set_dns("127.0.0.1")
                assert result is True
        
        @patch('subprocess.run')
        def test_set_dns_failure(self, mock_run):
            """Test setting DNS failure on Windows."""
            handler = WindowsHandler()
            
            # Mock failed command
            mock_run.return_value.returncode = 1
            
            with patch.object(handler, 'get_active_interface', return_value="Wi-Fi"):
                result = handler.set_dns("127.0.0.1")
                assert result is False
        
        def test_notify(self):
            """Test notification on Windows."""
            handler = WindowsHandler()
            
            with patch('win10toast.ToastNotifier') as mock_toast:
                mock_notifier = Mock()
                mock_toast.return_value = mock_notifier
                
                handler.notify("Test Title", "Test Message")
                mock_notifier.show_toast.assert_called_once()

except ImportError:
    pass  # Windows handler not available on this platform


try:
    from os_handlers.linux import LinuxHandler
    
    class TestLinuxHandler:
        """Test cases for LinuxHandler."""
        
        def test_init(self):
            """Test LinuxHandler initialization."""
            handler = LinuxHandler()
            assert hasattr(handler, 'logger')
        
        @patch('subprocess.run')
        def test_get_local_dns_success(self, mock_run):
            """Test getting local DNS on Linux."""
            handler = LinuxHandler()
            
            # Mock successful systemd-resolve command
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "DNS Servers: 192.168.1.1"
            mock_run.return_value = mock_result
            
            result = handler.get_local_dns()
            assert result == "192.168.1.1"
        
        @patch('subprocess.run')
        def test_set_dns_success(self, mock_run):
            """Test setting DNS on Linux."""
            handler = LinuxHandler()
            
            # Mock successful commands
            mock_run.return_value.returncode = 0
            
            with patch.object(handler, 'get_active_interface', return_value="eth0"):
                result = handler.set_dns("127.0.0.1")
                assert result is True
        
        @patch('subprocess.run')
        def test_notify_success(self, mock_run):
            """Test notification on Linux."""
            handler = LinuxHandler()
            
            # Mock successful notify-send command
            mock_run.return_value.returncode = 0
            
            handler.notify("Test Title", "Test Message")
            mock_run.assert_called_once()

except ImportError:
    pass  # Linux handler not available on this platform


try:
    from os_handlers.macos import MacOSHandler
    
    class TestMacOSHandler:
        """Test cases for MacOSHandler."""
        
        def test_init(self):
            """Test MacOSHandler initialization."""
            handler = MacOSHandler()
            assert hasattr(handler, 'logger')
        
        @patch('subprocess.run')
        def test_get_local_dns_success(self, mock_run):
            """Test getting local DNS on macOS."""
            handler = MacOSHandler()
            
            # Mock successful networksetup command
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "192.168.1.1"
            mock_run.return_value = mock_result
            
            result = handler.get_local_dns()
            assert result == "192.168.1.1"
        
        @patch('subprocess.run')
        def test_set_dns_success(self, mock_run):
            """Test setting DNS on macOS."""
            handler = MacOSHandler()
            
            # Mock successful commands
            mock_run.return_value.returncode = 0
            
            with patch.object(handler, 'get_active_interface', return_value="en0"):
                result = handler.set_dns("127.0.0.1")
                assert result is True
        
        @patch('subprocess.run')
        def test_restore_dns_to_dhcp_success(self, mock_run):
            """Test restoring DNS to DHCP on macOS."""
            handler = MacOSHandler()
            
            # Mock successful commands
            mock_run.return_value.returncode = 0
            
            with patch.object(handler, 'get_active_interface', return_value="en0"):
                result = handler.restore_dns_to_dhcp()
                assert result is True
        
        @patch('subprocess.run')
        def test_notify_success(self, mock_run):
            """Test notification on macOS."""
            handler = MacOSHandler()
            
            # Mock successful osascript command
            mock_run.return_value.returncode = 0
            
            handler.notify("Test Title", "Test Message")
            mock_run.assert_called_once()
        
        @patch('subprocess.run')
        def test_get_active_interface_success(self, mock_run):
            """Test getting active interface on macOS."""
            handler = MacOSHandler()
            
            # Mock successful route command
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "default via 192.168.1.1 dev en0"
            mock_run.return_value = mock_result
            
            result = handler.get_active_interface()
            assert result == "en0"
        
        @patch('subprocess.run')
        def test_get_active_interface_failure(self, mock_run):
            """Test getting active interface failure on macOS."""
            handler = MacOSHandler()
            
            # Mock failed route command
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            
            result = handler.get_active_interface()
            assert result == "en0"  # Should return default

except ImportError:
    pass  # macOS handler not available on this platform


class TestOSHandlerIntegration:
    """Integration tests for OS handlers."""
    
    @patch('platform.system')
    def test_factory_creates_correct_handler_type(self, mock_system):
        """Test that factory creates handlers that implement OSHandler interface."""
        test_cases = [
            ("Windows", "WindowsHandler"),
            ("Linux", "LinuxHandler"), 
            ("Darwin", "MacOSHandler")
        ]
        
        for os_name, handler_class in test_cases:
            mock_system.return_value = os_name
            
            with patch(f'os_handlers.factory.{handler_class}') as mock_handler_class:
                mock_instance = Mock()
                mock_handler_class.return_value = mock_instance
                
                # Add required methods to mock
                mock_instance.get_local_dns = Mock(return_value="192.168.1.1")
                mock_instance.get_active_interface = Mock(return_value="eth0")
                mock_instance.set_dns = Mock(return_value=True)
                mock_instance.notify = Mock()
                
                handler = OSHandlerFactory.create_handler()
                
                # Test that all required methods exist and work
                assert handler.get_local_dns() == "192.168.1.1"
                assert handler.get_active_interface() == "eth0"
                assert handler.set_dns("127.0.0.1") is True
                handler.notify("Test", "Message")  # Should not raise
    
    def test_handler_interface_compliance(self):
        """Test that all handlers implement the required interface."""
        # Create a concrete implementation for testing
        class TestHandler(OSHandler):
            def get_local_dns(self):
                return "192.168.1.1"
            
            def get_active_interface(self):
                return "eth0"
            
            def set_dns(self, dns_ip="127.0.0.1"):
                return True
            
            def notify(self, title, message, notification_type="info", urgency="normal", timeout=5000):
                pass
        
        handler = TestHandler()
        
        # Test all required methods exist and have correct signatures
        assert callable(handler.get_local_dns)
        assert callable(handler.get_active_interface)
        assert callable(handler.set_dns)
        assert callable(handler.notify)
        assert callable(handler.configure_local_dns)
        
        # Test method return types
        assert isinstance(handler.get_local_dns(), str)
        assert isinstance(handler.get_active_interface(), str)
        assert isinstance(handler.set_dns(), bool)
        assert isinstance(handler.configure_local_dns(["127.0.0.1"]), bool)
    
    def test_error_handling_in_handlers(self):
        """Test error handling in OS handlers."""
        class ErrorProneHandler(OSHandler):
            def get_local_dns(self):
                raise Exception("DNS lookup failed")
            
            def get_active_interface(self):
                raise Exception("Interface lookup failed")
            
            def set_dns(self, dns_ip="127.0.0.1"):
                raise Exception("DNS setting failed")
            
            def notify(self, title, message, notification_type="info", urgency="normal", timeout=5000):
                raise Exception("Notification failed")
        
        handler = ErrorProneHandler()
        
        # Test that exceptions are properly raised
        with pytest.raises(Exception, match="DNS lookup failed"):
            handler.get_local_dns()
        
        with pytest.raises(Exception, match="Interface lookup failed"):
            handler.get_active_interface()
        
        with pytest.raises(Exception, match="DNS setting failed"):
            handler.set_dns()
        
        with pytest.raises(Exception, match="Notification failed"):
            handler.notify("Test", "Message") 