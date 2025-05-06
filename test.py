import platform
import logging
from notifications import NotificationManager
from domain_analyzer import DomainAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    # Initialize the analyzer with mock mode enabled
    analyzer = DomainAnalyzer(
        api_key=""
    )
    result = analyzer.analyze_domain("google.com")
    print(result)
