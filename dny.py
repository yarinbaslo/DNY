import socket
import threading
import logging
import subprocess
import re
import struct
import platform


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DNSForwarder:
    def _init_(self):
        self.local_dns = self.get_local_dns()  # Automatically detect local DNS
        self.local_port = 53
        self.google_dns = '8.8.8.8'  # Google DNS as fallback
        self.google_port = 53
        self.listen_port = 53
        self.socket = None


    def get_local_dns(self):
        try:
            current_os = platform.system().lower()

            if current_os == 'windows':
                # Windows: use ipconfig
                output = subprocess.check_output(['ipconfig', '/all'], encoding='utf-8', errors='ignore')
                matches = re.findall(r'DNS Servers[^\d]*(\d+\.\d+\.\d+\.\d+)', output)
                if matches:
                    dns = matches[0]
                    logging.info("Found local DNS from ipconfig: %s", dns)
                    return dns

            elif current_os in ['linux', 'darwin']:
                # macOS or Linux: try /etc/resolv.conf
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns = line.split()[1]
                            logging.info("Found local DNS in resolv.conf: %s", dns)
                            return dns

                # macOS fallback
                if current_os == 'darwin':
                    output = subprocess.check_output(['scutil', '--dns'], encoding='utf-8', errors='ignore')
                    match = re.search(r'nameserver\[0\] : (\d+\.\d+\.\d+\.\d+)', output)
                    if match:
                        dns = match.group(1)
                        logging.info("Found local DNS from scutil: %s", dns)
                        return dns

            # Fallback
            default_dns = '8.8.8.8'
            logging.warning("Could not detect local DNS, using default: %s", default_dns)
            return default_dns

        except Exception as e:
            logging.error("Error detecting local DNS: %s", str(e))
            return '8.8.8.8'


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
            # Extract query ID from DNS packet
            query_id = struct.unpack('!H', data[:2])[0]
            logging.info("Received DNS query with ID: %d", query_id)

            # First try local DNS
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_socket.settimeout(10)  # Short timeout for local DNS
            local_socket.sendto(data, (self.local_dns, self.local_port))

            try:
                response_data, _ = local_socket.recvfrom(1024)
                # Check if response has answers
                if len(response_data) > 12:  # DNS header is 12 bytes
                    answer_count = struct.unpack('!H', response_data[6:8])[0]
                    if answer_count > 0:
                        logging.info("Local DNS resolved query ID: %d", query_id)
                        self.socket.sendto(response_data, client_address)
                        return
                
                logging.info("Local DNS returned no answers for query ID: %d, trying Google DNS", query_id)
                
            except socket.timeout:
                logging.info("Local DNS timeout for query ID: %d, trying Google DNS", query_id)
            finally:
                local_socket.close()

            # Try Google DNS
            google_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            google_socket.settimeout(5)
            google_socket.sendto(data, (self.google_dns, self.google_port))

            try:
                response_data, _ = google_socket.recvfrom(1024)
                logging.info("Google DNS resolved query ID: %d", query_id)
                self.socket.sendto(response_data, client_address)
            except socket.timeout:
                logging.error("Google DNS timeout for query ID: %d", query_id)
            finally:
                google_socket.close()

        except Exception as e:
            logging.error("Error handling query: %s", str(e))

if _name_ == "_main_":
    # Create and start the DNS forwarder
    dns_forwarder = DNSForwarder()
    dns_forwarder.start()
