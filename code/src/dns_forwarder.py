import socket
import threading
import logging
import struct
from .os_handlers.factory import OSHandlerFactory

class DNSForwarder:
    def __init__(self):
        self.os_handler = OSHandlerFactory.create_handler()
        self.local_dns = self.os_handler.get_local_dns()
        self.local_port = 53
        self.google_dns = '8.8.8.8'
        self.google_port = 53
        self.listen_port = 53
        self.socket = None

    def start(self):
        # Configure system DNS
        if not self.os_handler.configure_local_dns():
            logging.error("Failed to configure system DNS settings")
            return

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
            query_id = struct.unpack('!H', data[:2])[0]
            logging.info("Received DNS query with ID: %d", query_id)

            # Try local DNS first
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_socket.settimeout(10)
            local_socket.sendto(data, (self.local_dns, self.local_port))

            try:
                response_data, _ = local_socket.recvfrom(1024)
                if len(response_data) > 12:
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

            # Try Google DNS as fallback
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