import psutil
import subprocess
import re
import logging
import os
import platform
from .base import OSHandler

class WindowsHandler(OSHandler):
    def __init__(self):
        super().__init__()
        self.toaster = None
        if platform.system().lower() == 'windows':
            try:
                from win10toast import ToastNotifier
                self.toaster = ToastNotifier()
            except ImportError:
                logging.warning("win10toast not available, notifications will be logged only")

    def get_local_dns(self, _retry=False) -> str:
        try:
            output = subprocess.check_output(['ipconfig', '/all'], encoding='utf-8', errors='ignore')
            matches = re.findall(r'DNS Servers[^\d]*(\d+\.\d+\.\d+\.\d+)', output)
            if matches:
                dns = matches[0]
                if dns == '127.0.0.1' and not _retry:
                    logging.warning("Detected DNS is 127.0.0.1. Attempting to restore DNS to DHCP.")
                    if self.restore_dns_to_dhcp():
                        import time
                        time.sleep(2)  # allow DHCP settings to apply
                        return self.get_local_dns(_retry=True)
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
    
    def set_dns(self, dns_ips: list = ["127.0.0.1"]) -> bool:
        interface = self.get_active_interface()
        if interface is None:
            logging.error("No active network interface found")
            return False

        try:
            # Set the first DNS IP as static
            subprocess.run(
                f'netsh interface ipv4 set dns name="{interface}" static {dns_ips[0]}',
                shell=True,
                check=True
            )
            logging.info(f"Primary DNS for {interface} set to {dns_ips[0]}")

            # Add any additional DNS IPs as alternates
            for dns_ip in dns_ips[1:]:
                subprocess.run(
                    f'netsh interface ipv4 add dns name="{interface}" {dns_ip} index=2',
                    shell=True,
                    check=True
                )
                logging.info(f"Secondary DNS for {interface} set to {dns_ip}")
            
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set DNS: {e}")
            return False

    def restore_dns_to_dhcp(self) -> bool:
        interface = self.get_active_interface()
        if interface is None:
            logging.error("No active network interface found")
            return False

        try:
            subprocess.run(
                f'netsh interface ipv4 set dns name="{interface}" source=dhcp',
                shell=True,
                check=True
            )
            logging.info(f"Successfully restored DNS to DHCP on interface {interface}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to restore DNS to DHCP: {e}")
            return False

    def notify(self, title: str, message: str, notification_type: str = "info",
               urgency: str = "normal", timeout: int = 5000) -> None:
        """Send a system notification using win10toast on Windows, or log on other platforms."""
        try:
            if platform.system().lower() == 'windows' and self.toaster:
                # Convert timeout from milliseconds to seconds
                timeout_sec = timeout // 1000
                
                # Show the notification without icon
                self.toaster.show_toast(
                    title,
                    message,
                    duration=timeout_sec,
                    threaded=True  # Run in a separate thread to not block
                )
                logging.info(f"Notification sent: {title} - {message}")
            else:
                # On non-Windows platforms, just log the notification
                log_level = {
                    "info": logging.INFO,
                    "warning": logging.WARNING,
                    "error": logging.ERROR
                }.get(notification_type, logging.INFO)
                
                logging.log(log_level, f"{title}: {message}")
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")
            # Fallback to basic logging
            logging.info(f"{title}: {message}")