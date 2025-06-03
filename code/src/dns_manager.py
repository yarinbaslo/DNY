import logging
import json
import os
from os_handlers.factory import OSHandlerFactory
from dns.resolver import DNSResolver
from dns.server import DNSServer
from notification_manager import NotificationManager

class DNSManager:
    def __init__(self):
        self.os_handler = OSHandlerFactory.create_handler()
        self.local_dns = self.os_handler.get_local_dns()
        self.local_port = 53
        self.listen_port = 53
        self.server = None
        self.notification_manager = NotificationManager(self.os_handler)
        self.fallback_dns_list = self._load_fallback_dns_list()

    def _load_fallback_dns_list(self):
        """Load fallback DNS servers from dns_list.json file."""
        try:
            # Get the directory where this script is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to the code directory and find dns_list.json
            dns_list_path = os.path.join(os.path.dirname(current_dir), 'dns_list.json')
            
            with open(dns_list_path, 'r') as f:
                dns_providers = json.load(f)
            
            fallback_list = []
            for provider in dns_providers:
                # Add both primary and secondary DNS servers from each provider
                fallback_list.append((provider['primary'], 53))
                fallback_list.append((provider['secondary'], 53))
            
            logging.info(f"Loaded {len(fallback_list)} fallback DNS servers from dns_list.json")
            return fallback_list
            
        except Exception as e:
            logging.error(f"Failed to load DNS list from file: {str(e)}")
            # Fallback to default DNS servers if file loading fails
            return [
                ('8.8.8.8', 53),      # Google Primary
                ('8.8.4.4', 53),      # Google Secondary
                ('1.1.1.1', 53),      # Cloudflare Primary
                ('1.0.0.1', 53),      # Cloudflare Secondary
            ]

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
            fallback_dns_list=self.fallback_dns_list,
            notification_manager=self.notification_manager
        )

        self.server = DNSServer(self.listen_port, resolver)
        
        # Log primary and fallback DNS information
        fallback_dns_info = ", ".join([f"{dns}:{port}" for dns, port in self.fallback_dns_list[:4]])  # Show first 4
        logging.info("Primary DNS: %s, Fallback DNS servers: %s (and %d more)", 
                    self.local_dns, fallback_dns_info, max(0, len(self.fallback_dns_list) - 4))
        
        # Notify about service start
        self.notification_manager.notify_service_status(
            "Started",
            f"Using Primary DNS: {self.local_dns}, with {len(self.fallback_dns_list)} fallback servers"
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
