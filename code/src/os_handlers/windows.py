import psutil
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

    def get_active_interface(self) -> str:
        try:
             # Loop through all network interfaces
            for interface, addrs in psutil.net_if_addrs().items():
            # Check for Wi-Fi interfaces
                if "Wi-Fi" in interface or "WLAN" in interface:
                    # Check if the interface has an IPv4 address (use 2 for AF_INET)
                    for addr in addrs:
                        if addr.family == 2:  # 2 corresponds to AF_INET (IPv4)
                            # Return the interface name if it has an IPv4 address
                            return interface
            return None
            
        except Exception as e:
            logging.error(f"Error getting active interface on Windows: {str(e)}")
            return None

    def set_dns(self, dns_ip: str = "127.0.0.1") -> bool:
     
        interface = self.get_active_interface()
        if interface is None:
            logging.error("No active network interface found")
            return False
        
        try:
            # Change DNS server to 127.0.0.1 for the given interface using netsh
            subprocess.run(
                f'netsh interface ipv4 set dns name="{interface}" static {dns_ip}',
                shell=True,
                check=True
            )
            print(f"DNS for {interface} set to localhost (127.0.0.1)")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set DNS: {e}")
            return False

        logging.info(f"Successfully set DNS to {dns_ip} on Windows for interface {interface}")
        return True