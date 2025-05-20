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
    
    def configure_local_dns(self, dns_ips: list = ["127.0.0.1"]) -> bool:
        """Configure DNS settings for the system."""
        return self.set_dns(dns_ips)


    @abstractmethod
    def notify(self, title: str, message: str, notification_type: str = "info", 
               urgency: str = "normal", timeout: int = 5000) -> None:
        """
        Send a system notification.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error)
            urgency: Notification urgency (low, normal, critical)
            timeout: Notification timeout in milliseconds
        """
        pass