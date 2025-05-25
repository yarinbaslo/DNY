import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import openai
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from content_checker import ContentChecker


class TestContentChecker:
    """Test cases for ContentChecker class."""

    def test_init(self):
        """Test ContentChecker initialization."""
        checker = ContentChecker()
        
        assert checker.api_key is None
        assert hasattr(checker, 'logger')
        assert hasattr(checker, 'session')
        assert isinstance(checker.session, requests.Session)

    def test_set_api_key_valid_format(self):
        """Test setting a valid API key."""
        checker = ContentChecker()
        
        with patch('openai.ChatCompletion.create') as mock_create:
            mock_create.return_value = Mock()
            
            result = checker.set_api_key("sk-" + "a" * 32)
            
            assert result is True
            assert checker.api_key == "sk-" + "a" * 32
            mock_create.assert_called_once()

    def test_set_api_key_invalid_format(self):
        """Test setting an invalid API key format."""
        checker = ContentChecker()
        
        invalid_keys = [
            "invalid-key",
            "sk-short",
            "not-sk-prefix" + "a" * 32,
            "",
            "sk-"
        ]
        
        for invalid_key in invalid_keys:
            result = checker.set_api_key(invalid_key)
            assert result is False
            assert checker.api_key is None

    def test_set_api_key_openai_error(self):
        """Test setting API key when OpenAI validation fails."""
        checker = ContentChecker()
        
        with patch('openai.ChatCompletion.create') as mock_create:
            mock_create.side_effect = openai.error.AuthenticationError("Invalid API key")
            
            result = checker.set_api_key("sk-" + "a" * 32)
            
            assert result is False
            assert checker.api_key is None

    def test_clear_api_key(self):
        """Test clearing the API key."""
        checker = ContentChecker()
        
        # Set an API key first
        with patch('openai.ChatCompletion.create'):
            checker.set_api_key("sk-" + "a" * 32)
            assert checker.api_key is not None
        
        # Clear it
        checker.clear_api_key()
        assert checker.api_key is None

    def test_validate_domain_valid(self):
        """Test domain validation with valid domains."""
        checker = ContentChecker()
        
        valid_domains = [
            "google.com",
            "example.org",
            "sub.domain.co.uk",
            "test-site.com",
            "a.b"
        ]
        
        for domain in valid_domains:
            assert checker._validate_domain(domain) is True

    def test_validate_domain_invalid(self):
        """Test domain validation with invalid domains."""
        checker = ContentChecker()
        
        invalid_domains = [
            "",
            "not-a-domain",
            "no-dot",
            "a" * 256,  # Too long
            ".",
            ".com",
            "domain.",
            None
        ]
        
        for domain in invalid_domains:
            if domain is not None:
                assert checker._validate_domain(domain) is False

    def test_check_domain_no_api_key(self):
        """Test domain checking without API key."""
        checker = ContentChecker()
        
        is_safe, reason = checker.check_domain("example.com")
        
        assert is_safe is True
        assert "Content checking disabled - no API key" in reason

    def test_check_domain_invalid_domain(self):
        """Test domain checking with invalid domain."""
        checker = ContentChecker()
        
        is_safe, reason = checker.check_domain("invalid-domain")
        
        assert is_safe is True
        assert "Invalid domain format" in reason

    @patch('openai.ChatCompletion.create')
    def test_check_domain_with_api_key_success(self, mock_create):
        """Test successful domain checking with API key."""
        checker = ContentChecker()
        
        # Set up API key
        with patch('openai.ChatCompletion.create'):
            checker.set_api_key("sk-" + "a" * 32)
        
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Risk Level: low\nReason: Safe domain"
        mock_create.return_value = mock_response
        
        with patch.object(checker, '_get_website_info', return_value="Safe website"):
            is_safe, reason = checker.check_domain("example.com")
        
        assert is_safe is True
        assert "Safe domain" in reason

    @patch('openai.ChatCompletion.create')
    def test_check_domain_high_risk(self, mock_create):
        """Test domain checking with high risk result."""
        checker = ContentChecker()
        
        # Set up API key
        with patch('openai.ChatCompletion.create'):
            checker.set_api_key("sk-" + "a" * 32)
        
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Risk Level: high\nReason: Contains malware"
        mock_create.return_value = mock_response
        
        with patch.object(checker, '_get_website_info', return_value="Suspicious website"):
            is_safe, reason = checker.check_domain("malicious.com")
        
        assert is_safe is False
        assert "Contains malware" in reason

    @patch('openai.ChatCompletion.create')
    def test_check_domain_timeout(self, mock_create):
        """Test domain checking with timeout."""
        checker = ContentChecker()
        
        # Set up API key
        with patch('openai.ChatCompletion.create'):
            checker.set_api_key("sk-" + "a" * 32)
        
        # Mock timeout
        mock_create.side_effect = openai.error.Timeout("Request timed out")
        
        with patch.object(checker, '_get_website_info', return_value="Website info"):
            is_safe, reason = checker.check_domain("example.com")
        
        assert is_safe is True
        assert "Content check timed out" in reason

    @patch('openai.ChatCompletion.create')
    def test_check_domain_rate_limit(self, mock_create):
        """Test domain checking with rate limit error."""
        checker = ContentChecker()
        
        # Set up API key
        with patch('openai.ChatCompletion.create'):
            checker.set_api_key("sk-" + "a" * 32)
        
        # Mock rate limit error
        mock_create.side_effect = openai.error.RateLimitError("Rate limit exceeded")
        
        with patch.object(checker, '_get_website_info', return_value="Website info"):
            is_safe, reason = checker.check_domain("example.com")
        
        assert is_safe is True
        assert "Content check rate limited" in reason

    def test_extract_risk_level_from_response(self):
        """Test risk level extraction from structured response."""
        checker = ContentChecker()
        
        test_cases = [
            ("Risk Level: low\nReason: Safe", "low"),
            ("Risk Level: medium\nReason: Suspicious", "medium"),
            ("Risk Level: high\nReason: Dangerous", "high"),
            ("No risk level found", "unknown"),
            ("Risk Level: invalid\nReason: Test", "unknown")
        ]
        
        for response, expected in test_cases:
            result = checker._extract_risk_level_from_response(response)
            assert result == expected

    def test_extract_risk_level_fallback(self):
        """Test fallback risk level extraction."""
        checker = ContentChecker()
        
        test_cases = [
            ("This is a low risk domain", "low"),
            ("Medium risk detected", "medium"),
            ("High risk malware site", "high"),
            ("No keywords found", "unknown")
        ]
        
        for analysis, expected in test_cases:
            result = checker._extract_risk_level(analysis)
            assert result == expected

    def test_get_result_from_analysis(self):
        """Test getting final result from risk analysis."""
        checker = ContentChecker()
        
        test_cases = [
            ("low", "Safe domain", (True, "Safe domain")),
            ("medium", "Suspicious content", (False, "Suspicious content")),
            ("high", "Dangerous site", (False, "Dangerous site")),
            ("unknown", "Cannot determine", (True, "Cannot determine"))
        ]
        
        for risk_level, analysis, expected in test_cases:
            result = checker._get_result_from_analysis(risk_level, analysis)
            assert result == expected

    @patch('requests.Session.get')
    def test_get_website_info_success(self, mock_get):
        """Test successful website info retrieval."""
        checker = ContentChecker()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Test Site</title></head>
            <body><p>This is a test website</p></body>
        </html>
        """
        mock_get.return_value = mock_response
        
        with patch.object(checker, '_check_robots_txt', return_value=True):
            info = checker._get_website_info("example.com")
        
        assert "Test Site" in info

    @patch('requests.Session.get')
    def test_get_website_info_robots_disallow(self, mock_get):
        """Test website info when robots.txt disallows crawling."""
        checker = ContentChecker()
        
        with patch.object(checker, '_check_robots_txt', return_value=False):
            info = checker._get_website_info("example.com")
        
        assert info == "Website disallows crawling"
        mock_get.assert_not_called()

    @patch('requests.Session.get')
    def test_get_website_info_request_error(self, mock_get):
        """Test website info retrieval with request error."""
        checker = ContentChecker()
        
        mock_get.side_effect = requests.RequestException("Connection error")
        
        with patch.object(checker, '_check_robots_txt', return_value=True):
            info = checker._get_website_info("example.com")
        
        assert "Error fetching website" in info

    def test_check_robots_txt_success(self):
        """Test successful robots.txt checking."""
        checker = ContentChecker()
        
        with patch('urllib.robotparser.RobotFileParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser.can_fetch.return_value = True
            mock_parser_class.return_value = mock_parser
            
            result = checker._check_robots_txt("example.com")
            
            assert result is True
            mock_parser.set_url.assert_called_once_with("https://example.com/robots.txt")
            mock_parser.read.assert_called_once()
            mock_parser.can_fetch.assert_called_once_with("*", "https://example.com/")

    def test_check_robots_txt_error(self):
        """Test robots.txt checking with error."""
        checker = ContentChecker()
        
        with patch('urllib.robotparser.RobotFileParser') as mock_parser_class:
            mock_parser_class.side_effect = Exception("Network error")
            
            result = checker._check_robots_txt("example.com")
            
            assert result is True  # Should default to True on error

    def test_session_configuration(self):
        """Test that requests session is properly configured."""
        checker = ContentChecker()
        
        # Check that session has retry configuration
        assert hasattr(checker.session, 'adapters')
        assert 'https://' in checker.session.adapters

    @patch('openai.ChatCompletion.create')
    def test_check_domain_generic_exception(self, mock_create):
        """Test domain checking with generic exception."""
        checker = ContentChecker()
        
        # Set up API key
        with patch('openai.ChatCompletion.create'):
            checker.set_api_key("sk-" + "a" * 32)
        
        # Mock generic exception
        mock_create.side_effect = Exception("Generic error")
        
        with patch.object(checker, '_get_website_info', return_value="Website info"):
            is_safe, reason = checker.check_domain("example.com")
        
        assert is_safe is True
        assert "Content check failed" in reason
        assert "Generic error" in reason

    def test_multiple_domain_checks(self):
        """Test multiple domain checks in sequence."""
        checker = ContentChecker()
        
        domains = ["example.com", "test.org", "sample.net"]
        
        for domain in domains:
            is_safe, reason = checker.check_domain(domain)
            assert is_safe is True  # Without API key, should default to safe
            assert "Content checking disabled" in reason 