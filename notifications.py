import os
import platform
import subprocess
import logging
from datetime import datetime

class NotificationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.notification_history = []
        self.system = platform.system().lower()

    def notify(self, title, message, notification_type="info"):
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
            self.logger.warning("Unsupported OS for notifications: %s" % self.system)

    def _notify_macos(self, title, message):
        """Send notification on macOS using terminal-notifier."""
        try:
            # Use terminal-notifier for macOS notifications
            subprocess.call([
                'terminal-notifier',
                '-title', title,
                '-message', message,
                '-sound', 'default'
            ])
        except Exception as e:
            self.logger.error("Failed to send macOS notification: %s" % str(e))

    def _notify_linux(self, title, message):
        """Send notification on Linux using notify-send."""
        try:
            subprocess.call(['notify-send', title, message])
        except Exception as e:
            self.logger.error("Failed to send Linux notification: %s" % str(e))

    def _notify_windows(self, title, message):
        """Send notification on Windows using win10toast."""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message)
        except Exception as e:
            self.logger.error("Failed to send Windows notification: %s" % str(e))

    def _log_notification(self, title, message, notification_type):
        """Log the notification to the appropriate log level."""
        log_message = "%s: %s" % (title, message)
        if notification_type == "error":
            self.logger.error(log_message)
        elif notification_type == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def get_notification_history(self):
        """Get the history of all notifications."""
        return self.notification_history

    def clear_notification_history(self):
        """Clear the notification history."""
        self.notification_history = []

    def notify_domain_blocked(self, domain, reason):
        """Send notification when a domain is blocked."""
        self.notify(
            "Domain Blocked",
            "The domain %s has been blocked.\nReason: %s" % (domain, reason),
            "warning"
        )

    def notify_dns_switch(self, old_dns, new_dns):
        """Send notification when DNS server is switched."""
        self.notify(
            "DNS Server Changed",
            "DNS server changed from %s to %s" % (old_dns, new_dns),
            "info"
        )

    def notify_unsafe_site(self, domain, risk_level, details):
        """Send notification when a site is flagged as unsafe."""
        self.notify(
            "Unsafe Site Detected",
            "Domain: %s\nRisk Level: %s\nDetails: %s" % (domain, risk_level, details),
            "warning"
        ) 