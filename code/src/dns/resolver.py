import socket
import struct
import logging
from ip_blocker import IPBlocker
from content_checker import ContentChecker
import time
from dns_cache import DNSCache

class DNSResolver:
    def __init__(self, primary_dns, primary_port, fallback_dns_list, notification_manager):
        self.primary_dns = primary_dns
        self.primary_port = primary_port
        self.fallback_dns_list = fallback_dns_list  # List of (dns_server, port) tuples
        self.ip_blocker = IPBlocker()
        self.cache = DNSCache(max_size=1000, ttl=300)  # 5 minutes TTL for cached responses
        self.notification_manager = notification_manager
        self.content_checker = ContentChecker()

    def set_content_check_api_key(self, api_key: str) -> None:
        """Set the API key for content checking."""
        self.content_checker.set_api_key(api_key)

    def resolve(self, query_data):
        """
        Attempts to resolve a DNS query using cache then primary DNS first, then falls back to secondary DNS servers
        Returns the response data if successful, None if all attempts fail
        """
        cached_response = self.cache.get(query_data)
        if cached_response:
            logging.info("Cache hit for DNS query.")
            return cached_response

        # Try primary DNS first
        response = self._try_resolve(query_data, self.primary_dns, self.primary_port, is_primary=True)
        if response:
            self.cache.set(query_data, response)
            return response

        # Try each fallback DNS server in order
        for i, (fallback_dns, fallback_port) in enumerate(self.fallback_dns_list):
            logging.info(f"Trying fallback DNS server {i+1}/{len(self.fallback_dns_list)}: {fallback_dns}")
            response = self._try_resolve(query_data, fallback_dns, fallback_port, is_primary=False)
            
            if response:
                # Extract domain from query for content checking
                domain_parts = self._extract_domain_name(query_data, 12)  # Start after DNS header
                if domain_parts:
                    domain = '.'.join(domain_parts)
                    is_appropriate, reason = self.content_checker.check_domain(domain)
                    if not is_appropriate:
                        self.notification_manager.notify_domain_inappropriate_content(domain, reason)

                self.cache.set(query_data, response)
                return response
            else:
                logging.warning(f"Fallback DNS server {fallback_dns} failed, trying next server...")

        logging.error("All DNS servers failed to resolve the query")
        return None

    def _try_resolve(self, query_data, dns_server, port, is_primary):
        """
        Attempts to resolve a DNS query using the specified DNS server
        """
        query_id = struct.unpack('!H', query_data[:2])[0]
        dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_socket.settimeout(5)  # Set a reasonable timeout of 5 seconds

        try:
            dns_socket.sendto(query_data, (dns_server, port))
            response_data, _ = dns_socket.recvfrom(1024)

            if len(response_data) > 12:
                answer_count = struct.unpack('!H', response_data[6:8])[0]
                if answer_count > 0:
                    # Extract and validate IP addresses from the response
                    if self._validate_response_ips(response_data):
                        logging.info(f"{'Primary' if is_primary else 'Fallback'} DNS resolved query ID: {query_id}")
                        if not is_primary:
                            self.notification_manager.notify_dns_change(self.primary_dns, dns_server)
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
            logging.debug(f"Initial offset: {offset}, Response length: {len(response_data)}")
            
            # Skip question section
            while response_data[offset] != 0:
                offset += 1
            logging.debug(f"After question section, offset: {offset}")
            
            offset += 5  # Skip null terminator and type/class
            logging.debug(f"After skipping type/class, offset: {offset}")
            
            # Check each answer section
            while offset < len(response_data):
                logging.debug(f"Processing answer section at offset: {offset}")
                
                # Skip the name field (which might be compressed)
                name_offset = offset
                while True:
                    if name_offset >= len(response_data):
                        break
                    length = response_data[name_offset]
                    if length == 0:
                        name_offset += 1
                        break
                    if length & 0xc0 == 0xc0:  # Compressed name
                        name_offset += 2
                        break
                    name_offset += 1 + length
                
                # Now we're at the type field
                record_type = struct.unpack('!H', response_data[name_offset:name_offset+2])[0]
                record_type_name = self._get_record_type_name(record_type)
                logging.debug(f"Record type at offset {name_offset}: {record_type} ({record_type_name})")
                
                # Handle different record types
                if record_type == 1:  # A Record (IPv4)
                    # Extract IPv4 address (4 bytes after the type/class)
                    ip_bytes = response_data[name_offset+10:name_offset+14]
                    ip_str = socket.inet_ntoa(ip_bytes)
                    logging.debug(f"Found A record with IPv4: {ip_str}")
                    
                    # Check if IP is blocked
                    is_blocked, reason = self.ip_blocker.is_blocked_ip(ip_str)
                    if is_blocked:
                        logging.warning(f"Blocked IPv4 detected: {ip_str} - {reason}")
                        return False

                elif record_type == 28:  # AAAA Record (IPv6)
                    # Extract IPv6 address (16 bytes after the type/class)
                    ip_bytes = response_data[name_offset+10:name_offset+26]
                    ip_str = socket.inet_ntop(socket.AF_INET6, ip_bytes)
                    logging.debug(f"Found AAAA record with IPv6: {ip_str}")
                    
                    # Check if IP is blocked
                    is_blocked, reason = self.ip_blocker.is_blocked_ip(ip_str)
                    if is_blocked:
                        logging.warning(f"Blocked IPv6 detected: {ip_str} - {reason}")
                        return False

                elif record_type == 5:  # CNAME Record
                    # Extract the target domain name
                    target_name = self._extract_domain_name(response_data, name_offset+10)
                    logging.debug(f"Found CNAME record pointing to: {'.'.join(target_name)}")
                    # Note: We don't block CNAMEs, they're just aliases

                elif record_type == 6:  # SOA Record
                    try:
                        # Extract the primary nameserver and admin email
                        current_offset = name_offset + 10
                        primary_ns = self._extract_domain_name(response_data, current_offset)
                        current_offset += len(primary_ns) + 1  # +1 for the length byte
                        admin_email = self._extract_domain_name(response_data, current_offset)
                        logging.debug(f"Found SOA record - Primary NS: {'.'.join(primary_ns)}, Admin: {'.'.join(admin_email)}")
                    except Exception as e:
                        logging.debug(f"Error parsing SOA record: {str(e)}")
                        # Don't block on SOA parsing errors, just log and continue
                    # Note: We don't block SOA records

                elif record_type == 65:  # HTTPS Record
                    try:
                        # Extract the target name
                        target_name = self._extract_domain_name(response_data, name_offset+10)
                        logging.debug(f"Found HTTPS record pointing to: {'.'.join(target_name)}")
                    except Exception as e:
                        logging.debug(f"Error parsing HTTPS record: {str(e)}")
                        # Don't block on HTTPS parsing errors, just log and continue
                    # Note: We don't block HTTPS records
                
                # Move to next record
                data_length = struct.unpack('!H', response_data[name_offset+8:name_offset+10])[0]
                offset = name_offset + 10 + data_length
                logging.debug(f"Next record offset: {offset}")

            return True
        except Exception as e:
            logging.error(f"Error validating response IPs: {str(e)}")
            return False

    def _get_record_type_name(self, record_type):
        """
        Returns the name of a DNS record type
        """
        record_types = {
            1: "A",
            2: "NS",
            5: "CNAME",
            6: "SOA",
            15: "MX",
            16: "TXT",
            28: "AAAA",
            65: "HTTPS"
        }
        return record_types.get(record_type, f"Unknown({record_type})")

    def _extract_domain_name(self, data, offset):
        """
        Extracts a domain name from DNS response data starting at the given offset
        Handles both direct names and compressed names (pointers)
        """
        name_parts = []
        current_offset = offset
        
        while True:
            if current_offset >= len(data):
                break
                
            length = data[current_offset]
            if length == 0:
                break
                
            # Check if this is a pointer
            if length & 0xc0 == 0xc0:
                # Get the pointer offset
                pointer = struct.unpack('!H', data[current_offset:current_offset+2])[0] & 0x3fff
                # Recursively get the name from the pointer location
                name_parts.extend(self._extract_domain_name(data, pointer))
                break
                
            # Regular name part
            current_offset += 1
            try:
                name_parts.append(data[current_offset:current_offset+length].decode('ascii'))
            except UnicodeDecodeError:
                # If we can't decode as ASCII, try to handle it as a compressed name
                if length & 0xc0 == 0xc0:
                    pointer = struct.unpack('!H', data[current_offset-1:current_offset+1])[0] & 0x3fff
                    name_parts.extend(self._extract_domain_name(data, pointer))
                    break
                else:
                    # If it's not a compressed name, just skip this part
                    logging.debug(f"Could not decode name part at offset {current_offset}")
            current_offset += length
        return name_parts 
