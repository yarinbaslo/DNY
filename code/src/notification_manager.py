import logging
from datetime import datetime
from typing import Dict, List, Optional
from os_handlers.base import OSHandler

class NotificationManager:
    def __init__(self, os_handler: OSHandler):
        self.logger = logging.getLogger(__name__)
        self.notification_history: List[Dict] = []
        self.os_handler = os_handler

    def notify(self, title: str, message: str, notification_type: str = "info") -> None:
        """
        Send a system notification based on the operating system.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error)
        """
        # Log the notification
        self._log_notification(title, message, notification_type)
        
        # Store in history
        self.notification_history.append({
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "type": notification_type
        })

        # Send system notification using OS handler
        self.os_handler.notify(title, message, notification_type)

    def _log_notification(self, title: str, message: str, notification_type: str) -> None:
        """Log the notification to the appropriate log level."""
        log_message = f"{title}: {message}"
        if notification_type == "error":
            self.logger.error(log_message)
        elif notification_type == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def get_notification_history(self) -> List[Dict]:
        """Get the history of all notifications."""
        return self.notification_history

    def clear_notification_history(self) -> None:
        """Clear the notification history."""
        self.notification_history = []

    def notify_dns_change(self, old_dns: str, new_dns: str) -> None:
        """Send notification when DNS server is changed."""
        self.notify(
            "DNS Server Changed",
            f"DNS server changed from {old_dns} to {new_dns}",
            "info"
        )

    def notify_dns_error(self, error_message: str) -> None:
        """Send notification when DNS configuration fails."""
        self.notify(
            "DNS Configuration Error",
            error_message,
            "error"
        )

    def notify_service_status(self, status: str, details: Optional[str] = None) -> None:
        """Send notification about service status changes."""
        message = f"DNS Forwarder Service: {status}"
        if details:
            message += f"\nDetails: {details}"
        self.notify(
            "Service Status Update",
            message,
            "info"
        ) 

    def notify_domain_blocked(self, domain, reason):
        """Send notification when a domain is blocked."""
        self.notify(
            "Domain Blocked",
            "The domain %s has been blocked.\nReason: %s" % (domain, reason),
            "warning"
        )