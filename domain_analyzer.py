import openai
import logging
from typing import Dict, Optional

class DomainAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = api_key
        self.cache: Dict[str, Dict] = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def analyze_domain(self, domain: str) -> Dict:
        """
        Analyzes a domain using GPT to determine if it's potentially harmful or unethical.
        Returns a dictionary with analysis results.
        """
        # Check cache first
        if domain in self.cache:
            return self.cache[domain]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing domains for potential harm or unethical content. Provide a concise analysis."},
                    {"role": "user", "content": f"Analyze the domain {domain} for potential harm, unethical content, or security risks. Consider factors like malware, phishing, scams, inappropriate content, and privacy concerns. Provide a risk level (low, medium, high) and a brief explanation."}
                ],
                max_tokens=150
            )

            analysis = response.choices[0].message.content
            result = {
                "domain": domain,
                "analysis": analysis,
                "risk_level": self._extract_risk_level(analysis),
                "timestamp": datetime.now().isoformat()
            }

            # Cache the result
            self.cache[domain] = result
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing domain {domain}: {str(e)}")
            return {
                "domain": domain,
                "analysis": "Analysis failed",
                "risk_level": "unknown",
                "error": str(e)
            }

    def _extract_risk_level(self, analysis: str) -> str:
        """Extracts risk level from the analysis text."""
        analysis_lower = analysis.lower()
        if "high risk" in analysis_lower:
            return "high"
        elif "medium risk" in analysis_lower:
            return "medium"
        elif "low risk" in analysis_lower:
            return "low"
        return "unknown"

    def get_warning_message(self, domain: str) -> Optional[str]:
        """Returns a warning message if the domain is considered risky."""
        result = self.analyze_domain(domain)
        
        if result["risk_level"] == "high":
            return f"WARNING: This domain ({domain}) has been identified as potentially harmful. {result['analysis']}"
        elif result["risk_level"] == "medium":
            return f"CAUTION: This domain ({domain}) may contain harmful content. {result['analysis']}"
        
        return None 