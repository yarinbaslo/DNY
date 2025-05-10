import ipaddress
from typing import Tuple, Set

# Known block IPs (expand this list as needed)
KNOWN_BLOCK_IPS: Set[str] = {
    "127.0.0.1",
    "0.0.0.0",
    "192.168.0.1",
    "192.168.1.1",
    "203.98.7.65",  # Example of ISP redirect IP (replace with real cases)
}

def is_blocked_ip(ip_str: str) -> Tuple[bool, str]:
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

        # Check if it's localhost
        if ip.is_loopback:
            return True, "Loopback IP (127.0.0.1)"

        # Check if it's unspecified (0.0.0.0)
        if ip.is_unspecified:
            return True, "Unspecified IP (0.0.0.0)"

        # Check if it's in private IP ranges
        if ip.is_private:
            return True, f"Private IP range ({ip})"

        # Check if it's a multicast address
        if ip.is_multicast:
            return True, f"Multicast address ({ip})"

        # Check if it's a link-local address
        if ip.is_link_local:
            return True, f"Link-local address ({ip})"

        # Check if it's in reserved ranges
        if ip.is_reserved:
            return True, f"Reserved IP range ({ip})"

        # Check if it's in known block IPs
        if ip_str in KNOWN_BLOCK_IPS:
            return True, "Matched known block IP list"

        return False, "Looks okay"
    
    except ValueError as e:
        return False, f"Invalid IP format: {str(e)}"

def test_ip_blocker():
    """Test function to demonstrate the IP blocker functionality."""
    test_ips = [
        "127.0.0.1",
        "0.0.0.0",
        "192.168.1.1",
        "8.8.8.8",
        "203.98.7.65",
        "10.0.0.5",
        "1.1.1.1",
        "224.0.0.1",  # Multicast
        "169.254.1.1",  # Link-local
        "240.0.0.1",  # Reserved
        "invalid.ip"  # Invalid format
    ]

    print("Testing IP Blocker:")
    print("-" * 50)
    for ip in test_ips:
        blocked, reason = is_blocked_ip(ip)
        print(f"{ip:15} => {'BLOCKED' if blocked else 'OK':8} ({reason})")

if __name__ == "__main__":
    test_ip_blocker() 