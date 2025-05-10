import subprocess
import logging
from .base import OSHandler

class LinuxHandler(OSHandler):
    def get_local_dns(self) -> str:
        try:
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        dns = line.split()[1]
                        logging.info("Found local DNS in resolv.conf: %s", dns)
                        return dns
        except Exception as e:
            logging.error("Error detecting local DNS: %s", str(e))
        return '8.8.8.8'

    def get_network_interfaces(self) -> list:
        interfaces = []
        try:
            output = subprocess.check_output(['ip', 'route', 'get', '8.8.8.8'], encoding='utf-8', errors='ignore')
            if 'dev' in output:
                interface = output.split('dev')[1].split()[0]
                interfaces.append(interface)
        except Exception as e:
            logging.error(f"Error getting network interfaces on Linux: {str(e)}")
        return interfaces

    def get_active_interface(self) -> str:
        try:
            # First try to get the default route interface
            try:
                route_output = subprocess.check_output(['ip', 'route', 'get', '8.8.8.8'], encoding='utf-8', errors='ignore')
                if 'dev' in route_output:
                    interface = route_output.split('dev')[1].split()[0]
                    # Verify the interface is up and has an IP
                    ip_output = subprocess.check_output(['ip', 'addr', 'show', interface], encoding='utf-8', errors='ignore')
                    if 'state UP' in ip_output and 'inet ' in ip_output:
                        return interface
            except subprocess.CalledProcessError:
                pass

            # If that fails, try to find any interface that's up and has an IP
            ip_output = subprocess.check_output(['ip', 'addr'], encoding='utf-8', errors='ignore')
            current_interface = None
            for line in ip_output.split('\n'):
                if ':' in line and not line.startswith(' '):
                    current_interface = line.split(':')[1].strip()
                elif current_interface and 'state UP' in line and 'inet ' in line:
                    return current_interface

            # If still no interface found, fall back to the old method
            interfaces = self.get_network_interfaces()
            return interfaces[0] if interfaces else None

        except Exception as e:
            logging.error(f"Error getting active interface on Linux: {str(e)}")
            # Fallback to the old behavior
            interfaces = self.get_network_interfaces()
            return interfaces[0] if interfaces else None
        return None

    def set_dns(self, dns_ip: str = "127.0.0.1", interface: str = None) -> bool:
        if interface is None:
            interface = self.get_active_interface()
            if interface is None:
                logging.error("No active network interface found")
                return False

        try:
            # Update resolv.conf
            with open('/etc/resolv.conf', 'w') as f:
                f.write(f"nameserver {dns_ip}\n")
            logging.info(f"Successfully set DNS to {dns_ip} on Linux")
            return True
        except Exception as e:
            logging.error(f"Failed to set DNS on Linux: {str(e)}")
            return False

    def notify(self, title: str, message: str, notification_type: str = "info") -> None:
        """
        Send a system notification on Linux using notify-send.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error)
        """
        try:
            # Map notification type to urgency
            urgency = {
                "error": "critical",
                "warning": "normal",
                "info": "low"
            }.get(notification_type, "normal")

            # Use notify-send for Linux notifications
            subprocess.call([
                'notify-send',
                '--urgency', urgency,
                title,
                message
            ])
        except Exception as e:
            self.logger.error(f"Failed to send Linux notification: {str(e)}") 