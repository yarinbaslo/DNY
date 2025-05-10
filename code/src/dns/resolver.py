import socket
import struct
import logging

class DNSResolver:
    def __init__(self, primary_dns, primary_port, fallback_dns, fallback_port):
        self.primary_dns = primary_dns
        self.primary_port = primary_port
        self.fallback_dns = fallback_dns
        self.fallback_port = fallback_port

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
                    logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS resolved query ID: {query_id}")
                    return response_data

            logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS returned no answers for query ID: {query_id}")
            return None

        except socket.timeout:
            logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS timeout for query ID: {query_id}")
            return None
        finally:
            dns_socket.close() 