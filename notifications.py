import os
import platform
import subprocess
import logging
from typing import Optional
from datetime import datetime

class NotificationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.notification_history = []
        self.system = platform.system().lower()

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

        # Send system notification
        if self.system == "darwin":  # macOS
            self._notify_macos(title, message)
        elif self.system == "linux":
            self._notify_linux(title, message)
        elif self.system == "windows":
            self._notify_windows(title, message)
        else:
            self.logger.warning(f"Unsupported OS for notifications: {self.system}")

    def _notify_macos(self, title: str, message: str) -> None:
        """Send notification on macOS using osascript."""
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script])
        except Exception as e:
            self.logger.error(f"Failed to send macOS notification: {e}")

    def _notify_linux(self, title: str, message: str) -> None:
        """Send notification on Linux using notify-send."""
        try:
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            self.logger.error(f"Failed to send Linux notification: {e}")

    def _notify_windows(self, title: str, message: str) -> None:
        """Send notification on Windows using win10toast."""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message)
        except Exception as e:
            self.logger.error(f"Failed to send Windows notification: {e}")

    def _log_notification(self, title: str, message: str, notification_type: str) -> None:
        """Log the notification to the appropriate log level."""
        log_message = f"{title}: {message}"
        if notification_type == "error":
            self.logger.error(log_message)
        elif notification_type == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def get_notification_history(self) -> list:
        """Get the history of all notifications."""
        return self.notification_history

    def clear_notification_history(self) -> None:
        """Clear the notification history."""
        self.notification_history = []

    def notify_domain_blocked(self, domain: str, reason: str) -> None:
        """Send notification when a domain is blocked."""
        self.notify(
            "Domain Blocked",
            f"The domain {domain} has been blocked.\nReason: {reason}",
            "warning"
        )

    def notify_dns_switch(self, old_dns: str, new_dns: str) -> None:
        """Send notification when DNS server is switched."""
        self.notify(
            "DNS Server Changed",
            f"DNS server changed from {old_dns} to {new_dns}",
            "info"
        )

    def notify_unsafe_site(self, domain: str, risk_level: str, details: str) -> None:
        """Send notification when a site is flagged as unsafe."""
        self.notify(
            "Unsafe Site Detected",
            f"Domain: {domain}\nRisk Level: {risk_level}\nDetails: {details}",
            "warning"
        ) 