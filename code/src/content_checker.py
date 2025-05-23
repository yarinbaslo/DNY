import logging
import requests
from typing import Tuple, Optional
import json
import openai
import re
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import urllib.robotparser

class ContentChecker:
    def __init__(self):
        """Initialize the content checker."""
        self.api_key = None
        self.logger = logging.getLogger(__name__)
        
        # Configure requests session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
    def set_api_key(self, api_key: str) -> bool:
        """
        Set the API key for content checking.
        
        Args:
            api_key: OpenAI API key
            
        Returns:
            bool: True if key is valid, False otherwise
        """
        if not re.match(r'^sk-[A-Za-z0-9]{32,}$', api_key):
            self.logger.error("Invalid API key format")
            return False
            
        try:
            # Test the API key
            openai.api_key = api_key
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            self.api_key = api_key
            return True
        except Exception as e:
            self.logger.error(f"Failed to validate API key: {str(e)}")
            return False
            
    def clear_api_key(self) -> None:
        """Clear the API key."""
        self.api_key = None
        openai.api_key = None
        
    def check_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a domain's content is appropriate using AI.
        
        Args:
            domain: The domain to check
            
        Returns:
            Tuple[bool, Optional[str]]: 
                - bool: True if content is appropriate, False if not
                - str: Reason for the decision, or None if check failed
        """
        if not self._validate_domain(domain):
            return True, "Invalid domain format"
            
        if not self.api_key:
            self.logger.warning("No API key set for content checking")
            return True, "Content checking disabled - no API key"
            
        try:
            # Get website content for context
            website_info = self._get_website_info(domain)
            
            # Prepare the prompt with structured format
            prompt = (
                f"Analyze the domain {domain} for potential harm, unethical content, or security risks. Consider factors like malware, phishing, scams, inappropriate content, and privacy concerns. Context: {website_info}\n\n"
                "Respond with:\nRisk Level: <low|medium|high>\nReason: <short explanation>"
            )
            
            # Log the prompt at debug level
            self.logger.debug(f"Sending prompt to GPT: {prompt}")
            
            # Analyze domain using GPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing domains for potential harm or unethical content. Provide a concise analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                timeout=10
            )

            analysis = response.choices[0].message.content
            
            # Log truncated response at debug level
            self.logger.debug(f"Received GPT response: {analysis[:300]}...")
            
            # Try to extract risk level using regex first
            risk_level = self._extract_risk_level_from_response(analysis)
            if risk_level == "unknown":
                # Fallback to generic extraction if regex fails
                risk_level = self._extract_risk_level(analysis)
            
            return self._get_result_from_analysis(risk_level, analysis)
            
        except openai.error.Timeout:
            self.logger.error("OpenAI API timeout")
            return True, "Content check timed out"
        except openai.error.RateLimitError:
            self.logger.error("OpenAI API rate limit exceeded")
            return True, "Content check rate limited"
        except Exception as e:
            self.logger.error(f"Error checking domain content: {str(e)}")
            return True, f"Content check failed: {str(e)}"

    def _validate_domain(self, domain: str) -> bool:
        """Validate domain format."""
        try:
            # Basic domain validation
            if not domain or len(domain) > 255:
                return False
                
            # Check if it's a valid domain format
            result = urlparse(f"http://{domain}")
            return bool(result.netloc) and '.' in result.netloc
        except Exception:
            return False

    def _check_robots_txt(self, domain: str) -> bool:
        """Check if the website allows crawling."""
        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"https://{domain}/robots.txt")
            rp.read()
            return rp.can_fetch("*", f"https://{domain}/")
        except Exception as e:
            self.logger.debug(f"Error checking robots.txt for {domain}: {str(e)}")
            return True  # Allow crawling if robots.txt check fails

    def _get_website_info(self, domain: str) -> str:
        """Get basic information about the website."""
        try:
            # Check robots.txt first
            if not self._check_robots_txt(domain):
                self.logger.info(f"Website {domain} disallows crawling in robots.txt")
                return "Website disallows crawling"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.session.get(
                f"https://{domain}",
                headers=headers,
                timeout=5,
                verify=True,  # SSL verification
                allow_redirects=True
            )
            
            info = []
            if response.status_code == 200:
                # Use BeautifulSoup for better HTML parsing
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get title
                title = soup.title.string if soup.title else ""
                if title:
                    info.append(f"Title: {title}")
                
                # Get meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    info.append(f"Description: {meta_desc['content']}")
                
                # Try to get main content
                main_content = None
                
                # Try main content areas first
                for selector in ['main', 'article', 'div.content', 'div#content', 'div.main']:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                # If no main content found, try to get some paragraph text
                if not main_content:
                    paragraphs = soup.find_all('p', limit=3)
                    if paragraphs:
                        main_content = BeautifulSoup(''.join(str(p) for p in paragraphs), 'html.parser')
                
                # If still no content, try body text
                if not main_content:
                    main_content = soup.find('body')
                
                if main_content:
                    text = main_content.get_text(strip=True, separator=' ')[:200]
                    if text:
                        info.append(f"Content preview: {text}")
            
            return " | ".join(info) if info else "No additional context available"
            
        except requests.exceptions.SSLError:
            self.logger.warning(f"SSL verification failed for {domain}")
            return "SSL verification failed"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting website info: {str(e)}")
            return "Failed to get website info"

    def _extract_risk_level_from_response(self, response: str) -> str:
        """Extract risk level from structured GPT response."""
        # Look for the structured format first
        risk_match = re.search(r'Risk Level:\s*(low|medium|high)', response, re.IGNORECASE)
        if risk_match:
            return risk_match.group(1).lower()
        return "unknown"

    def _extract_risk_level(self, analysis: str) -> str:
        """Extracts risk level from the analysis text using pattern matching."""
        analysis_lower = analysis.lower()
        
        # More comprehensive risk level detection
        risk_patterns = {
            'high': [
                r'high(?:-|\s)?risk',
                r'severe(?:-|\s)?risk',
                r'critical(?:-|\s)?risk',
                r'extremely(?:-|\s)?dangerous',
                r'block(?:ed)?\s+immediately'
            ],
            'medium': [
                r'medium(?:-|\s)?risk',
                r'moderate(?:-|\s)?risk',
                r'caution(?:ary)?',
                r'potentially(?:-|\s)?harmful',
                r'proceed(?:-|\s)?with(?:-|\s)?caution'
            ],
            'low': [
                r'low(?:-|\s)?risk',
                r'minimal(?:-|\s)?risk',
                r'likely(?:-|\s)?safe',
                r'no(?:-|\s)?significant(?:-|\s)?risk'
            ]
        }
        
        for level, patterns in risk_patterns.items():
            if any(re.search(pattern, analysis_lower) for pattern in patterns):
                return level
                
        return "unknown"

    def _get_result_from_analysis(self, risk_level: str, analysis: str) -> Tuple[bool, str]:
        """Convert analysis result to a tuple of (is_appropriate, reason)."""
        if risk_level == "high":
            return False, f"WARNING: This domain has been identified as potentially harmful. {analysis}"
        elif risk_level == "medium":
            return False, f"CAUTION: This domain may contain harmful content. {analysis}"
        return True, "Content appears appropriate" 