import socket
import struct
import logging
from ..ip_blocker import IPBlocker

class DNSResolver:
    def __init__(self, primary_dns, primary_port, fallback_dns, fallback_port):
        self.primary_dns = primary_dns
        self.primary_port = primary_port
        self.fallback_dns = fallback_dns
        self.fallback_port = fallback_port
        self.ip_blocker = IPBlocker()

    def resolve(self, query_data):
        """
        Attempts to resolve a DNS query using primary DNS first, then falls back to secondary DNS
        Returns the response data if successful, None if both attempts fail
        """
        # Try primary DNS first
        response = self._try_resolve(query_data, self.primary_dns, self.primary_port, is_primary=True)
        if response:
            return response

        # Try fallback DNS
        return self._try_resolve(query_data, self.fallback_dns, self.fallback_port, is_primary=False)

    def _try_resolve(self, query_data, dns_server, port, is_primary):
        """
        Attempts to resolve a DNS query using the specified DNS server
        """
        query_id = struct.unpack('!H', query_data[:2])[0]
        dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_socket.settimeout(10 if is_primary else 5)

        try:
            dns_socket.sendto(query_data, (dns_server, port))
            response_data, _ = dns_socket.recvfrom(1024)

            if len(response_data) > 12:
                answer_count = struct.unpack('!H', response_data[6:8])[0]
                if answer_count > 0:
                    # Extract and validate IP addresses from the response
                    if self._validate_response_ips(response_data):
                        logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS resolved query ID: {query_id}")
                        return response_data
                    else:
                        logging.warning(f"Blocked IP detected in response for query ID: {query_id}")
                        return None

            logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS returned no answers for query ID: {query_id}")
            return None

        except socket.timeout:
            logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS timeout for query ID: {query_id}")
            return None
        finally:
            dns_socket.close()

    def _validate_response_ips(self, response_data):
        """
        Validates IP addresses in the DNS response against blocking rules
        Returns True if all IPs are valid, False if any are blocked
        """
        try:
            # Skip header (12 bytes) and question section
            offset = 12
            # Skip question section
            while response_data[offset] != 0:
                offset += 1
            offset += 5  # Skip null terminator and type/class

            # Check each answer section
            while offset < len(response_data):
                # Check if this is an A record (type 1)
                if response_data[offset:offset+2] == b'\x00\x01':
                    # Extract IP address (4 bytes after the type/class)
                    ip_bytes = response_data[offset+10:offset+14]
                    ip_str = socket.inet_ntoa(ip_bytes)
                    
                    # Check if IP is blocked
                    is_blocked, reason = self.ip_blocker.is_blocked_ip(ip_str)
                    if is_blocked:
                        logging.warning(f"Blocked IP detected: {ip_str} - {reason}")
                        return False
                
                # Move to next record
                offset += 10  # Skip name pointer
                data_length = struct.unpack('!H', response_data[offset:offset+2])[0]
                offset += 2 + data_length

            return True
        except Exception as e:
            logging.error(f"Error validating response IPs: {str(e)}")
            return False 