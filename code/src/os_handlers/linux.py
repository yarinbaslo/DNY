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
            logging.error("Error reading resolv.conf: %s", str(e))
        return '8.8.8.8'

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

            return None

        except Exception as e:
            logging.error(f"Error getting active interface on Linux: {str(e)}")
            return None

    def set_dns(self, dns_ip: str = "127.0.0.1") -> bool:
        interface = self.get_active_interface()
        if interface is None:
            logging.error("No active network interface found")
            return False
        
        try:
            resolv_conf = "/etc/resolv.conf"
            with open(resolv_conf, "w") as f:
                f.write(f"nameserver {dns_ip}\n")
            logging.info(f"Successfully set DNS to {dns_ip} on Linux")
            return True
        except Exception as e:
            logging.error(f"Failed to set DNS on Linux: {str(e)}")
            return False 