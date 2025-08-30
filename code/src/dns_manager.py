import logging
import os
from os_handlers.factory import OSHandlerFactory
from dns.resolver import DNSResolver
from dns.server import DNSServer
from notification_manager import NotificationManager
from config import Config
from database_manager import DatabaseManager

class DNSManager:
    def __init__(self):
        self.os_handler = OSHandlerFactory.create_handler()
        self.local_dns = self.os_handler.get_local_dns()
        
        # Get DNS configuration
        dns_config = Config.get_dns_config()
        self.local_port = dns_config['local_port']
        self.listen_port = dns_config['listen_port']
        self.timeout = dns_config['timeout']
        self.max_cache_size = dns_config['max_cache_size']
        self.cache_ttl = dns_config['cache_ttl']
        
        # Initialize database manager
        db_config = Config.get_database_config()
        self.database_manager = DatabaseManager(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        self.server = None
        self.notification_manager = NotificationManager(self.os_handler)
        self.fallback_dns_list = self._load_fallback_dns_list()

    def _load_fallback_dns_list(self):
        """Load fallback DNS servers from database - only active providers."""
        try:
            # Get active DNS providers from database
            dns_providers = self.database_manager.get_active_dns_providers()
            
            if not dns_providers:
                logging.warning("No active DNS providers found in database, using default servers")
                return self._get_default_dns_servers()
            
            fallback_list = []
            for provider in dns_providers:
                # Add both primary and secondary DNS servers from each active provider
                if provider.get('primary_ip'):
                    fallback_list.append((provider['primary_ip'], 53))
                    logging.debug(f"Added primary DNS: {provider['primary_ip']} ({provider['name']})")
                
                if provider.get('secondary_ip'):
                    fallback_list.append((provider['secondary_ip'], 53))
                    logging.debug(f"Added secondary DNS: {provider['secondary_ip']} ({provider['name']})")
            
            logging.info(f"Loaded {len(fallback_list)} fallback DNS servers from {len(dns_providers)} active providers in database")
            return fallback_list
            
        except Exception as e:
            logging.error(f"Failed to load DNS list from database: {str(e)}")
            return self._get_default_dns_servers()
    
    def _get_default_dns_servers(self):
        """Get default DNS servers as fallback when database is unavailable."""
        default_dns_config = Config.get_default_dns_config()
        default_servers = []
        
        for server in default_dns_config['servers']:
            default_servers.append((server['ip'], server['port']))
            logging.debug(f"Added default DNS: {server['ip']}:{server['port']} ({server['name']})")
        
        logging.info(f"Using {len(default_servers)} default DNS servers as fallback from config")
        return default_servers

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
            notification_manager=self.notification_manager,
            database_manager=self.database_manager,
            timeout=self.timeout,
            max_cache_size=self.max_cache_size,
            cache_ttl=self.cache_ttl
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
        
        # Close database connection
        if self.database_manager:
            self.database_manager.close()
