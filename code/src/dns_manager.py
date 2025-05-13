import logging
from os_handlers.factory import OSHandlerFactory
from dns.resolver import DNSResolver
from dns.server import DNSServer
from notification_manager import NotificationManager

class DNSManager:
    def __init__(self):
        self.os_handler = OSHandlerFactory.create_handler()
        self.local_dns = self.os_handler.get_local_dns()
        self.local_port = 53
        self.google_dns = '8.8.8.8'
        self.google_port = 53
        self.listen_port = 53
        self.server = None
        self.notification_manager = NotificationManager(self.os_handler)

    def start(self):
        """
        Starts the DNS forwarder service
        """
        # Configure system DNS
        if not self.os_handler.configure_local_dns(dns_ips=["127.0.0.1", self.local_dns]):
            error_msg = "Failed to configure system DNS settings"
            logging.error(error_msg)
            self.notification_manager.notify_dns_error(error_msg)
            return
        else:
            self.notification_manager.notify_dns_change(self.local_dns, "127.0.0.1")


        # Create resolver and server instances
        resolver = DNSResolver(
            primary_dns=self.local_dns,
            primary_port=self.local_port,
            fallback_dns=self.google_dns,
            fallback_port=self.google_port,
            notification_manager=self.notification_manager
        )

        self.server = DNSServer(self.listen_port, resolver)
        logging.info("Primary DNS: %s, Fallback DNS: %s", self.local_dns, self.google_dns)
        
        # Notify about service start
        self.notification_manager.notify_service_status(
            "Started",
            f"Using Primary DNS: {self.local_dns}, Fallback DNS: {self.google_dns}"
        )
        
        # Start the server
        self.server.start()

    def stop(self):
        """
        Stops the DNS forwarder service
        """
        if self.server:
            self.server.stop()
            self.server = None

            # Restore system DNS to automatic (DHCP)
            if not self.os_handler.restore_dns_to_dhcp():
                error_msg = "Failed to restore system DNS settings to automatic (DHCP)"
                logging.error(error_msg)
                self.notification_manager.notify_dns_error(error_msg)
            else:
                self.notification_manager.notify_dns_change("127.0.0.1", "DHCP")

            # Notify about service stop
            self.notification_manager.notify_service_status("Stopped")
