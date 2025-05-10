import socket
import threading
import logging
import subprocess
import re
import struct
import platform
import os
from datetime import datetime
from domain_analyzer import DomainAnalyzer
from notifications import NotificationManager
from ip_blocker import is_blocked_ip  # Import the IP blocker

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
        self.analyzer = DomainAnalyzer(api_key="")  # API key
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

    def get_network_interfaces(self):
        """Get list of available network interfaces based on OS."""
        system = platform.system().lower()
        interfaces = []

        if system == "darwin":  # macOS
            try:
                # Get the active interface using route command
                active_interface = subprocess.check_output(['route', 'get', 'default']).decode()
                for line in active_interface.split('\n'):
                    if 'interface:' in line:
                        interface_name = line.split(':')[1].strip()
                        # Get the service name for this interface
                        services = subprocess.check_output(['networksetup', '-listallnetworkservices']).decode()
                        for service in services.split('\n'):
                            if service.strip() and not service.startswith('*'):
                                # Check if this service matches our interface
                                service_info = subprocess.check_output(['networksetup', '-getinfo', service.strip()]).decode()
                                if interface_name in service_info:
                                    interfaces.append(service.strip())
                                    break
            except Exception as e:
                self.logger.error(f"Error getting network interfaces on macOS: {str(e)}")

        elif system == "windows":
            try:
                # Get active interface using ipconfig
                output = subprocess.check_output(['ipconfig']).decode()
                current_interface = None
                for line in output.split('\n'):
                    if 'adapter' in line.lower():
                        current_interface = line.split(':')[0].strip()
                    elif 'IPv4' in line and current_interface:
                        # If it has an IP address, it's active
                        interfaces.append(current_interface)
                        current_interface = None
            except Exception as e:
                self.logger.error(f"Error getting network interfaces on Windows: {str(e)}")

        elif system == "linux":
            try:
                # Get active interface using ip route
                output = subprocess.check_output(['ip', 'route', 'get', '8.8.8.8']).decode()
                if 'dev' in output:
                    interface = output.split('dev')[1].split()[0]
                    interfaces.append(interface)
            except Exception as e:
                self.logger.error(f"Error getting network interfaces on Linux: {str(e)}")

        return interfaces

    def get_active_interface(self):
        """Get the active network interface."""
        interfaces = self.get_network_interfaces()
        if interfaces:
            return interfaces[0]  # Return the first (and should be only) active interface
        return None

    def set_dns_linux(self, dns_ip="127.0.0.1"):
        """Set DNS server for Linux systems."""
        try:
            resolv_conf = "/etc/resolv.conf"
            with open(resolv_conf, "w") as f:
                f.write(f"nameserver {dns_ip}\n")
            self.logger.info(f"Successfully set DNS to {dns_ip} on Linux")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set DNS on Linux: {str(e)}")
            return False

    def set_dns_macos(self, interface=None, dns_ip="127.0.0.1"):
        """Set DNS server for macOS systems."""
        if interface is None:
            interface = self.get_active_interface()
            if interface is None:
                self.logger.error("No active network interface found")
                return False

        try:
            subprocess.run(["networksetup", "-setdnsservers", interface, dns_ip], check=True)
            self.logger.info(f"Successfully set DNS to {dns_ip} on macOS for interface {interface}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set DNS on macOS: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error setting DNS on macOS: {str(e)}")
            return False

    def set_dns_windows(self, interface=None, dns_ip="127.0.0.1"):
        """Set DNS server for Windows systems."""
        if interface is None:
            interface = self.get_active_interface()
            if interface is None:
                self.logger.error("No active network interface found")
                return False

        try:
            subprocess.run(["netsh", "interface", "ip", "set", "dns",
                          f"name={interface}", f"source=static", f"addr={dns_ip}"],
                         check=True)
            self.logger.info(f"Successfully set DNS to {dns_ip} on Windows for interface {interface}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set DNS on Windows: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error setting DNS on Windows: {str(e)}")
            return False

    def configure_local_dns(self, dns_ip="127.0.0.1"):
        """Configure DNS settings based on the operating system."""
        system = platform.system().lower()
        success = False

        if system == "linux":
            success = self.set_dns_linux(dns_ip)
        elif system == "darwin":  # macOS
            success = self.set_dns_macos(None, dns_ip)
        elif system == "windows":
            success = self.set_dns_windows(None, dns_ip)
        else:
            self.logger.error(f"Unsupported operating system: {system}")
            return False

        if success:
            self.notifier.notify_dns_switch("System DNS", dns_ip)
        return success

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

    def _extract_ip_from_response(self, response_data):
        """Extract the first IP address from a DNS response."""
        try:
            # Skip header (12 bytes)
            pos = 12
            
            # Skip question section
            while True:
                length = response_data[pos]
                if length == 0:
                    pos += 5  # Skip type and class
                    break
                pos += 1
                pos += length
            
            # Check if we have answers
            ancount = struct.unpack('!H', response_data[6:8])[0]
            if ancount == 0:
                return None
                
            # Skip answer name (compressed)
            pos += 2  # Skip pointer
            
            # Get type and class
            rtype = struct.unpack('!H', response_data[pos:pos+2])[0]
            pos += 4  # Skip class and TTL
            
            # Get data length
            rdlength = struct.unpack('!H', response_data[pos:pos+2])[0]
            pos += 2
            
            # If it's an A record (type 1), extract the IP
            if rtype == 1 and rdlength == 4:
                ip_bytes = response_data[pos:pos+4]
                return socket.inet_ntoa(ip_bytes)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting IP from response: {str(e)}")
            return None

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
                    # Check if the resolved IP is blocked
                    resolved_ip = self._extract_ip_from_response(local_response)
                    if resolved_ip:
                        blocked, reason = is_blocked_ip(resolved_ip)
                        if blocked:
                            self.logger.info(f"Local DNS returned blocked IP {resolved_ip}: {reason}, trying Google DNS")
                            self.notifier.notify_dns_switch(self.local_dns, self.google_dns)
                            # Fall through to Google DNS
                        else:
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