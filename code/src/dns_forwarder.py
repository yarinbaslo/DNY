import logging
from .os_handlers.factory import OSHandlerFactory
from .dns.resolver import DNSResolver
from .dns.server import DNSServer

class DNSForwarder:
    def __init__(self):
        self.os_handler = OSHandlerFactory.create_handler()
        self.local_dns = self.os_handler.get_local_dns()
        self.local_port = 53
        self.google_dns = '8.8.8.8'
        self.google_port = 53
        self.listen_port = 53
        self.server = None

    def start(self):
        """
        Starts the DNS forwarder service
        """
        # Configure system DNS
        if not self.os_handler.configure_local_dns():
            logging.error("Failed to configure system DNS settings")
            return

        # Create resolver and server instances
        resolver = DNSResolver(
            primary_dns=self.local_dns,
            primary_port=self.local_port,
            fallback_dns=self.google_dns,
            fallback_port=self.google_port
        )

        self.server = DNSServer(self.listen_port, resolver)
        logging.info("Primary DNS: %s, Fallback DNS: %s", self.local_dns, self.google_dns)
        
        # Start the server
        self.server.start()

    def stop(self):
        """
        Stops the DNS forwarder service
        """
        if self.server:
            self.server.stop()
            self.server = None 