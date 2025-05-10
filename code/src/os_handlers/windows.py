import subprocess
import re
import logging
from .base import OSHandler

class WindowsHandler(OSHandler):
    def get_local_dns(self) -> str:
        try:
            output = subprocess.check_output(['ipconfig', '/all'], encoding='utf-8', errors='ignore')
            matches = re.findall(r'DNS Servers[^\d]*(\d+\.\d+\.\d+\.\d+)', output)
            if matches:
                dns = matches[0]
                logging.info("Found local DNS from ipconfig: %s", dns)
                return dns
        except Exception as e:
            logging.error("Error detecting local DNS: %s", str(e))
        return '8.8.8.8'

    def get_network_interfaces(self) -> list:
        interfaces = []
        try:
            output = subprocess.check_output(['ipconfig'], encoding='utf-8', errors='ignore')
            current_interface = None
            for line in output.split('\n'):
                if 'adapter' in line.lower():
                    current_interface = line.split(':')[0].strip()
                elif 'IPv4' in line and current_interface:
                    interfaces.append(current_interface)
                    current_interface = None
        except Exception as e:
            logging.error(f"Error getting network interfaces on Windows: {str(e)}")
        return interfaces

    def get_active_interface(self) -> str:
        try:
            # Get interface states
            output = subprocess.check_output(['netsh', 'interface', 'show', 'interface'], encoding='utf-8', errors='ignore')
            active_interfaces = []
            
            # Parse the output to find connected interfaces
            for line in output.split('\n'):
                if 'Connected' in line:
                    # Extract interface name (it's the last part of the line)
                    interface_name = line.strip().split()[-1]
                    active_interfaces.append(interface_name)
            
            # Get all interfaces with IPv4 addresses
            all_interfaces = self.get_network_interfaces()
            
            # Return the first interface that is both active and has an IPv4 address
            for interface in all_interfaces:
                if interface in active_interfaces:
                    return interface
                    
            # If no active interface found, return the first one with IPv4 as fallback
            return all_interfaces[0] if all_interfaces else None
            
        except Exception as e:
            logging.error(f"Error getting active interface on Windows: {str(e)}")
            # Fallback to the old behavior
            interfaces = self.get_network_interfaces()
            return interfaces[0] if interfaces else None

    def set_dns(self, dns_ip: str = "127.0.0.1", interface: str = None) -> bool:
        if interface is None:
            output = subprocess.check_output(['ipconfig'], encoding='utf-8', errors='ignore')
            interfaces = re.findall(r'(\S+):\s+.IPv4.:\s*(\d+\.\d+\.\d+\.\d+)', output)
            if interfaces:
                interface = interfaces[0][0]
                logging.info(f"Found active interface: {interface}")
            else:
                logging.error("No active network interface found on Windows.")
                return False

        try:
            result = subprocess.run(
                ["netsh", "interface", "ip", "set", "dns", f'name={interface}', "static", dns_ip],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                logging.error(f"Failed to set DNS: {result.stderr}")
                return False

            logging.info(f"Successfully set DNS to {dns_ip} on Windows for interface {interface}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set DNS on Windows: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error setting DNS on Windows: {str(e)}")
            return False

    def notify(self, title: str, message: str, notification_type: str = "info") -> None:
        """
        Send a system notification on Windows using win10toast.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error)
        """
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=5,  # Show for 5 seconds
                threaded=True  # Run in a separate thread
            )
        except Exception as e:
            self.logger.error(f"Failed to send Windows notification: {str(e)}") 