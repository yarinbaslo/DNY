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