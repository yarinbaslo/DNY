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

    def get_network_interfaces(self) -> list:
        interfaces = []
        try:
            active_interface = subprocess.check_output(['route', 'get', 'default'], encoding='utf-8', errors='ignore')
            for line in active_interface.split('\n'):
                if 'interface:' in line:
                    interface_name = line.split(':')[1].strip()
                    services = subprocess.check_output(['networksetup', '-listallnetworkservices'], encoding='utf-8', errors='ignore')
                    for service in services.split('\n'):
                        if service.strip() and not service.startswith('*'):
                            service_info = subprocess.check_output(['networksetup', '-getinfo', service.strip()], encoding='utf-8', errors='ignore')
                            if interface_name in service_info:
                                interfaces.append(service.strip())
                                break
        except Exception as e:
            logging.error(f"Error getting network interfaces on macOS: {str(e)}")
        return interfaces

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
            # Fallback to the old behavior
            interfaces = self.get_network_interfaces()
            return interfaces[0] if interfaces else None

    def set_dns(self, dns_ip: str = "127.0.0.1", interface: str = None) -> bool:
        if interface is None:
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

    def notify(self, title: str, message: str, notification_type: str = "info") -> None:
        """
        Send a system notification on macOS using terminal-notifier.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error)
        """
        try:
            # Use terminal-notifier for macOS notifications
            subprocess.call([
                'terminal-notifier',
                '-title', title,
                '-message', message,
                '-sound', 'default'
            ])
        except Exception as e:
            self.logger.error(f"Failed to send macOS notification: {str(e)}") 