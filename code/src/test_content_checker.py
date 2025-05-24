import logging
from content_checker import ContentChecker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_content_checker():
    # Initialize the content checker
    checker = ContentChecker()
    
    # Test domains to check
    test_domains = [
        "google.com",  # Should be safe
        "example.com",  # Should be safe
        "wikipedia.org"  # Should be safe
    ]
    
    # Test without API key first
    logger.info("Testing without API key...")
    for domain in test_domains:
        is_safe, reason = checker.check_domain(domain)
        logger.info(f"Domain: {domain}")
        logger.info(f"Is safe: {is_safe}")
        logger.info(f"Reason: {reason}")
        logger.info("-" * 50)
    
    # Note: To test with API key, you would need to set it first:
    # checker.set_api_key("your-api-key-here")

if __name__ == "__main__":
    test_content_checker() 