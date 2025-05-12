import subprocess
import re
import logging
from .base import OSHandler

class MacOSHandler(OSHandler):
    def get_local_dns(self) -> str:
        try:
            # Try resolv.conf first
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        dns = line.split()[1]
                        logging.info("Found local DNS in resolv.conf: %s", dns)
                        return dns

            # Fallback to scutil
            output = subprocess.check_output(['scutil', '--dns'], encoding='utf-8', errors='ignore')
            match = re.search(r'nameserver\[0\] : (\d+\.\d+\.\d+\.\d+)', output)
            if match:
                dns = match.group(1)
                logging.info("Found local DNS from scutil: %s", dns)
                return dns
        except Exception as e:
            logging.error("Error detecting local DNS: %s", str(e))
        return '8.8.8.8'

    def get_active_interface(self) -> str:
        try:
            # Get the default route interface
            route_output = subprocess.check_output(['route', 'get', 'default'], encoding='utf-8', errors='ignore')
            default_interface = None
            for line in route_output.split('\n'):
                if 'interface:' in line:
                    default_interface = line.split(':')[1].strip()
                    break
            
            if not default_interface:
                logging.error("No default route interface found")
                return None
                
            # Get all network services
            services_output = subprocess.check_output(['networksetup', '-listallnetworkservices'], encoding='utf-8', errors='ignore')
            active_services = []
            
            # Check each service's status
            for service in services_output.split('\n'):
                service = service.strip()
                if service and not service.startswith('*'):  # Skip disabled services
                    try:
                        # Get service info to check if it matches our default interface
                        service_info = subprocess.check_output(['networksetup', '-getinfo', service], encoding='utf-8', errors='ignore')
                        if default_interface in service_info:
                            # Check if the service is actually connected
                            status = subprocess.check_output(['networksetup', '-getinfo', service], encoding='utf-8', errors='ignore')
                            if 'IP address' in status and 'IPv4' in status:
                                active_services.append(service)
                    except subprocess.CalledProcessError:
                        continue
            
            # Return the first active service that matches our default interface
            return active_services[0] if active_services else None
            
        except Exception as e:
            logging.error(f"Error getting active interface on macOS: {str(e)}")
            return None

    def set_dns(self, dns_ip: str = "127.0.0.1") -> bool:
        interface = self.get_active_interface()
        if interface is None:
            logging.error("No active network interface found")
            return False

        try:
            subprocess.run(["networksetup", "-setdnsservers", interface, dns_ip], check=True)
            logging.info(f"Successfully set DNS to {dns_ip} on macOS for interface {interface}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set DNS on macOS: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error setting DNS on macOS: {str(e)}")
            return False 
        
    def notify(self, title: str, message: str, notification_type: str = "info",
               urgency: str = "normal", timeout: int = 5000) -> None:
        """Send a system notification using terminal-notifier if available, otherwise osascript."""
        try:
            # Map notification type to sound
            sounds = {
                "info": "Glass",
                "warning": "Basso",
                "error": "Funk"
            }
            sound = sounds.get(notification_type, "Glass")

            # Escape special characters in title and message
            title_escaped = title.replace('"', '\\"')
            message_escaped = message.replace('"', '\\"')

            # Try terminal-notifier first
            try:
                result = subprocess.run([
                    "terminal-notifier",
                    "-title", title,
                    "-message", message,
                    "-sound", sound
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    logging.info(f"Notification sent with terminal-notifier: {title} - {message}")
                    return
                else:
                    logging.warning(f"terminal-notifier failed: {result.stderr}")
            except FileNotFoundError:
                logging.info("terminal-notifier not found, falling back to osascript.")

            # Fallback to AppleScript (osascript)
            script = f'display notification "{message_escaped}" with title "{title_escaped}" sound name "{sound}"'
            result = subprocess.run(['osascript', '-e', script], 
                                 capture_output=True, 
                                 text=True, 
                                 check=True)
            if result.stderr:
                logging.warning(f"Notification warning: {result.stderr}")
            logging.info(f"Notification sent with osascript: {title} - {message}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to send notification: {str(e)}")
            if hasattr(e, 'stderr') and e.stderr:
                logging.error(f"Error details: {e.stderr}")
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")