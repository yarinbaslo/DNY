import ipaddress
from typing import Tuple, Set, List, Callable
from dataclasses import dataclass

@dataclass
class BlockRule:
    """Represents a rule for blocking IP addresses."""
    name: str
    check_func: Callable[[ipaddress.IPv4Address], bool]
    reason_template: str

class IPBlocker:
    """Handles IP address blocking logic."""
    
    def __init__(self):
        self.known_block_ips: Set[str] = {
            "127.0.0.1",
            "0.0.0.0",
            "192.168.0.1",
            "192.168.1.1",
            "203.98.7.65",  # Example of ISP redirect IP
        }
        self._setup_rules()

    def _setup_rules(self) -> None:
        """Initialize the blocking rules."""
        self.rules: List[BlockRule] = [
            BlockRule(
                name="loopback",
                check_func=lambda ip: ip.is_loopback,
                reason_template="Loopback IP ({ip})"
            ),
            BlockRule(
                name="unspecified",
                check_func=lambda ip: ip.is_unspecified,
                reason_template="Unspecified IP ({ip})"
            ),
            BlockRule(
                name="private",
                check_func=lambda ip: ip.is_private,
                reason_template="Private IP range ({ip})"
            ),
            BlockRule(
                name="multicast",
                check_func=lambda ip: ip.is_multicast,
                reason_template="Multicast address ({ip})"
            ),
            BlockRule(
                name="link_local",
                check_func=lambda ip: ip.is_link_local,
                reason_template="Link-local address ({ip})"
            ),
            BlockRule(
                name="reserved",
                check_func=lambda ip: ip.is_reserved,
                reason_template="Reserved IP range ({ip})"
            ),
        ]

    def add_blocked_ip(self, ip: str) -> None:
        """Add an IP to the known blocked IPs list."""
        self.known_block_ips.add(ip)

    def remove_blocked_ip(self, ip: str) -> None:
        """Remove an IP from the known blocked IPs list."""
        self.known_block_ips.discard(ip)

    def is_blocked_ip(self, ip_str: str) -> Tuple[bool, str]:
        """
        Check if an IP address should be blocked based on various criteria.
        
        Args:
            ip_str (str): The IP address to check in string format
            
        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: True if the IP should be blocked, False otherwise
                - str: Reason for the decision
        """
        try:
            ip = ipaddress.ip_address(ip_str)

            # Check all rules
            for rule in self.rules:
                if rule.check_func(ip):
                    return True, rule.reason_template.format(ip=ip)
                
            # Check known blocked IPs
            if ip_str in self.known_block_ips:
                return True, "Matched known block IP list"

            return False, "Looks okay"
        
        except ValueError as e:
            return False, f"Invalid IP format: {str(e)}"


