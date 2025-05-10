import socket
import threading
import logging
from .resolver import DNSResolver

class DNSServer:
    def __init__(self, listen_port, resolver):
        self.listen_port = listen_port
        self.resolver = resolver
        self.socket = None

    def start(self):
        """
        Starts the DNS server and begins listening for queries
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.listen_port))
        logging.info("DNS Server listening on port %d", self.listen_port)

        while True:
            try:
                data, client_address = self.socket.recvfrom(1024)
                threading.Thread(target=self._handle_query, args=(data, client_address)).start()
            except Exception as e:
                logging.error("Error in main loop: %s", str(e))

    def _handle_query(self, data, client_address):
        """
        Handles an incoming DNS query
        """
        try:
            response_data = self.resolver.resolve(data)
            if response_data:
                self.socket.sendto(response_data, client_address)
        except Exception as e:
            logging.error("Error handling query: %s", str(e))

    def stop(self):
        """
        Stops the DNS server and cleans up resources
        """
        if self.socket:
            self.socket.close()
            self.socket = None 