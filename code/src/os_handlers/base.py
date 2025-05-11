from abc import ABC, abstractmethod
import logging

class OSHandler(ABC):
    """Base class for OS-specific operations."""
    
    @abstractmethod
    def get_local_dns(self) -> str:
        """Get the local DNS server address."""
        pass

    @abstractmethod
    def get_active_interface(self) -> str:
        """Get the active network interface."""
        pass

    @abstractmethod
    def set_dns(self, dns_ip: str = "127.0.0.1") -> bool:
        """Set DNS server for the system."""
        pass

    def configure_local_dns(self, dns_ip: str = "127.0.0.1") -> bool:
        """Configure DNS settings for the system."""
        return self.set_dns(dns_ip) 