import socket
import threading
import logging
import subprocess
import re
import struct
from datetime import datetime
from domain_analyzer import DomainAnalyzer
from notifications import NotificationManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DNSForwarder:
    def __init__(self):
        self.local_dns = self.get_local_dns()  # Automatically detect local DNS
        self.local_port = 53
        self.google_dns = '8.8.8.8'  # Google DNS as fallback
        self.google_port = 53
        self.listen_port = 53
        self.socket = None
        self.analyzer = DomainAnalyzer(api_key="openai-api-key")  # API key
        self.notifier = NotificationManager()
        self.logger = logging.getLogger(__name__)

    def get_local_dns(self):
        try:
            # Try to get DNS from resolv.conf (Linux/macOS)
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        dns = line.split()[1]
                        logging.info("Found local DNS in resolv.conf: %s", dns)
                        return dns

            # Try to get DNS from system configuration (macOS)
            try:
                output = subprocess.check_output(['scutil', '--dns']).decode()
                match = re.search(r'nameserver\[0\] : (\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    dns = match.group(1)
                    logging.info("Found local DNS from scutil: %s", dns)
                    return dns
            except:
                pass

            # Try to get DNS from ipconfig (Windows)
            try:
                output = subprocess.check_output(['ipconfig', '/all']).decode()
                match = re.search(r'DNS Servers[^\d]*(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    dns = match.group(1)
                    logging.info("Found local DNS from ipconfig: %s", dns)
                    return dns
            except:
                pass

            # If all methods fail, use Google DNS
            logging.warning("Could not detect local DNS, using Google DNS")
            self.notifier.notify_dns_switch("Unknown", self.google_dns)
            return self.google_dns

        except Exception as e:
            logging.error("Error detecting local DNS: %s", str(e))
            self.notifier.notify_dns_switch("Unknown", self.google_dns)
            return self.google_dns

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.listen_port))
        logging.info("DNS Forwarder listening on port %d", self.listen_port)
        logging.info("Primary DNS: %s, Fallback DNS: %s", self.local_dns, self.google_dns)

        while True:
            try:
                data, client_address = self.socket.recvfrom(1024)
                threading.Thread(target=self.handle_query, args=(data, client_address)).start()
            except Exception as e:
                logging.error("Error in main loop: %s", str(e))

    def handle_query(self, data, client_address):
        try:
            # Extract domain from DNS query
            domain = self._extract_domain(data)
            self.logger.info("Received query for domain: %s", domain)

            # Analyze domain
            warning = self.analyzer.get_warning_message(domain)
            if warning:
                self.logger.warning(warning)
                # Notify about unsafe site
                result = self.analyzer.analyze_domain(domain)
                self.notifier.notify_unsafe_site(
                    domain,
                    result["risk_level"],
                    result["analysis"]
                )

            # Try local DNS first
            try:
                local_response = self.forward_query(data, self.local_dns)
                if self._has_records(local_response):
                    self.logger.info("Resolved by local DNS: %s", domain)
                    self.socket.sendto(local_response, client_address)
                    return
            except Exception as e:
                self.logger.warning("Local DNS failed: %s", str(e))
                self.notifier.notify_dns_switch(self.local_dns, self.google_dns)

            # Fall back to Google DNS
            google_response = self.forward_query(data, self.google_dns)
            self.logger.info("Resolved by Google DNS: %s", domain)
            self.socket.sendto(google_response, client_address)

        except Exception as e:
            self.logger.error("Error handling query: %s", str(e))

    def _extract_domain(self, data):
        """Extract domain name from DNS query."""
        try:
            # Skip header (12 bytes)
            pos = 12
            domain_parts = []
            
            # Extract domain parts
            while True:
                length = data[pos]
                if length == 0:
                    break
                pos += 1
                domain_parts.append(data[pos:pos+length].decode('ascii'))
                pos += length
            
            return '.'.join(domain_parts)
        except Exception as e:
            self.logger.error("Error extracting domain: %s", str(e))
            return "unknown"

    def _has_records(self, response):
        """Check if DNS response contains any records."""
        if not response:
            return False
        # Check if response has any answer records (ANCOUNT in header)
        ancount = struct.unpack('!H', response[6:8])[0]
        return ancount > 0

    def forward_query(self, data, dns):
        # First try local DNS
        local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_socket.settimeout()  # Short timeout for local DNS
        local_socket.sendto(data, (dns, self.local_port))

        try:
            response_data, _ = local_socket.recvfrom(1024)
            # Check if response has answers
            if len(response_data) > 12:  # DNS header is 12 bytes
                answer_count = struct.unpack('!H', response_data[6:8])[0]
                if answer_count > 0:
                    self.logger.info("Local DNS resolved query ID: %s", self._extract_domain(data))
                    return response_data
            
            self.logger.info("Local DNS returned no answers for query ID: %s, trying Google DNS", self._extract_domain(data))
            
        except socket.timeout:
            self.logger.info("Local DNS timeout for query ID: %s, trying Google DNS", self._extract_domain(data))
        finally:
            local_socket.close()

        # Try Google DNS
        google_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        google_socket.settimeout(5)
        google_socket.sendto(data, (self.google_dns, self.google_port))

        try:
            response_data, _ = google_socket.recvfrom(1024)
            self.logger.info("Google DNS resolved query ID: %s", self._extract_domain(data))
            return response_data
        except socket.timeout:
            self.logger.error("Google DNS timeout for query ID: %s", self._extract_domain(data))
        finally:
            google_socket.close()

if __name__ == "__main__":
    # Create and start the DNS forwarder
    dns_forwarder = DNSForwarder()
    dns_forwarder.start() 