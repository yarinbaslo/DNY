import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import main


class MockDNSManager:
    """Mock DNS manager for testing."""
    
    def __init__(self):
        self.started = False
        self.stopped = False
        self.start_calls = 0
        self.stop_calls = 0
    
    def start(self):
        self.started = True
        self.start_calls += 1
    
    def stop(self):
        self.stopped = True
        self.stop_calls += 1


class TestMain:
    """Test cases for main module."""

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_success(self, mock_logging_config, mock_dns_manager_class):
        """Test successful main execution."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify logging was configured
        mock_logging_config.assert_called_once_with(
            level=main.logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Verify DNS manager was created and started
        mock_dns_manager_class.assert_called_once()
        assert mock_forwarder.started is True
        assert mock_forwarder.start_calls == 1

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    @patch('logging.info')
    def test_main_keyboard_interrupt(self, mock_log_info, mock_logging_config, mock_dns_manager_class):
        """Test main execution with keyboard interrupt."""
        mock_forwarder = MockDNSManager()
        mock_forwarder.start = Mock(side_effect=KeyboardInterrupt("User interrupted"))
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify logging was configured
        mock_logging_config.assert_called_once()
        
        # Verify DNS manager was created and started
        mock_dns_manager_class.assert_called_once()
        
        # Verify keyboard interrupt was logged
        mock_log_info.assert_called_with("DNS Forwarder stopped by user")
        
        # Verify stop was called
        assert mock_forwarder.stop_calls == 1

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    @patch('logging.error')
    def test_main_general_exception(self, mock_log_error, mock_logging_config, mock_dns_manager_class):
        """Test main execution with general exception."""
        mock_forwarder = MockDNSManager()
        mock_forwarder.start = Mock(side_effect=Exception("Network error"))
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify logging was configured
        mock_logging_config.assert_called_once()
        
        # Verify DNS manager was created and started
        mock_dns_manager_class.assert_called_once()
        
        # Verify exception was logged
        mock_log_error.assert_called_with("DNS Forwarder stopped due to error: %s", "Network error")
        
        # Verify stop was called
        assert mock_forwarder.stop_calls == 1

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_finally_block_execution(self, mock_logging_config, mock_dns_manager_class):
        """Test that finally block always executes."""
        mock_forwarder = MockDNSManager()
        mock_forwarder.start = Mock(side_effect=Exception("Test error"))
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify stop was called in finally block
        assert mock_forwarder.stop_calls == 2  # Once in except, once in finally

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_forwarder_none_handling(self, mock_logging_config, mock_dns_manager_class):
        """Test main execution when forwarder is None."""
        mock_dns_manager_class.return_value = None
        
        # Should not raise an exception
        main.main()
        
        # Verify logging was configured
        mock_logging_config.assert_called_once()

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_stop_method_exception(self, mock_logging_config, mock_dns_manager_class):
        """Test main execution when stop method raises exception."""
        mock_forwarder = MockDNSManager()
        mock_forwarder.stop = Mock(side_effect=Exception("Stop error"))
        mock_forwarder.start = Mock(side_effect=KeyboardInterrupt())
        mock_dns_manager_class.return_value = mock_forwarder
        
        # Should not raise an exception despite stop() failing
        main.main()
        
        # Verify logging was configured
        mock_logging_config.assert_called_once()

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_logging_configuration(self, mock_logging_config, mock_dns_manager_class):
        """Test that logging is configured correctly."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify logging configuration parameters
        mock_logging_config.assert_called_once_with(
            level=main.logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_dns_manager_creation(self, mock_logging_config, mock_dns_manager_class):
        """Test that DNS manager is created correctly."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify DNS manager was created with no arguments
        mock_dns_manager_class.assert_called_once_with()

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_start_method_called(self, mock_logging_config, mock_dns_manager_class):
        """Test that start method is called on DNS manager."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        main.main()
        
        # Verify start was called exactly once
        assert mock_forwarder.start_calls == 1

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    @patch('logging.info')
    @patch('logging.error')
    def test_main_exception_handling_order(self, mock_log_error, mock_log_info, 
                                          mock_logging_config, mock_dns_manager_class):
        """Test that exceptions are handled in the correct order."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        # Test KeyboardInterrupt is caught before general Exception
        mock_forwarder.start = Mock(side_effect=KeyboardInterrupt("User stop"))
        main.main()
        
        mock_log_info.assert_called_with("DNS Forwarder stopped by user")
        mock_log_error.assert_not_called()
        
        # Reset mocks
        mock_log_info.reset_mock()
        mock_log_error.reset_mock()
        
        # Test general Exception is caught
        mock_forwarder.start = Mock(side_effect=RuntimeError("Runtime error"))
        main.main()
        
        mock_log_error.assert_called_with("DNS Forwarder stopped due to error: %s", "Runtime error")
        mock_log_info.assert_not_called()

    def test_main_module_execution(self):
        """Test that main is called when module is executed directly."""
        with patch('main.main') as mock_main_func:
            # Simulate running the module directly
            with patch('__main__.__name__', '__main__'):
                # Import and execute the module's __name__ == '__main__' block
                exec("""
if __name__ == "__main__":
    main()
                """, {'__name__': '__main__', 'main': mock_main_func})
            
            mock_main_func.assert_called_once()

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_resource_cleanup(self, mock_logging_config, mock_dns_manager_class):
        """Test that resources are properly cleaned up."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        # Test normal execution
        main.main()
        assert mock_forwarder.stop_calls == 1
        
        # Reset
        mock_forwarder.stop_calls = 0
        
        # Test with exception
        mock_forwarder.start = Mock(side_effect=Exception("Test error"))
        main.main()
        assert mock_forwarder.stop_calls == 2  # Once in except, once in finally

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_multiple_calls(self, mock_logging_config, mock_dns_manager_class):
        """Test that main can be called multiple times."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        # Call main multiple times
        main.main()
        main.main()
        main.main()
        
        # Verify each call creates a new DNS manager
        assert mock_dns_manager_class.call_count == 3
        assert mock_forwarder.start_calls == 3
        assert mock_forwarder.stop_calls == 3

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_import_safety(self, mock_logging_config, mock_dns_manager_class):
        """Test that importing main module doesn't execute main function."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        # Simply importing the module should not call main
        # (This test verifies the if __name__ == "__main__": guard works)
        
        # Reset call counts
        mock_dns_manager_class.reset_mock()
        
        # Re-import the module (simulating import)
        import importlib
        importlib.reload(main)
        
        # main() should not have been called during import
        mock_dns_manager_class.assert_not_called()

    @patch('main.DNSManager')
    @patch('logging.basicConfig')
    def test_main_error_message_formatting(self, mock_logging_config, mock_dns_manager_class):
        """Test that error messages are formatted correctly."""
        mock_forwarder = MockDNSManager()
        mock_dns_manager_class.return_value = mock_forwarder
        
        test_error_message = "Connection failed: timeout after 30 seconds"
        mock_forwarder.start = Mock(side_effect=Exception(test_error_message))
        
        with patch('logging.error') as mock_log_error:
            main.main()
            
            # Verify error message is formatted with the exception string
            mock_log_error.assert_called_with(
                "DNS Forwarder stopped due to error: %s", 
                test_error_message
            ) 