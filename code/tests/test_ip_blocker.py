import pytest
import ipaddress
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ip_blocker import IPBlocker, BlockRule


class TestBlockRule:
    """Test cases for BlockRule dataclass."""

    def test_block_rule_creation(self):
        """Test BlockRule creation and attributes."""
        rule = BlockRule(
            name="test_rule",
            check_func=lambda ip: ip.is_loopback,
            reason_template="Test reason: {ip}"
        )
        
        assert rule.name == "test_rule"
        assert rule.reason_template == "Test reason: {ip}"
        
        # Test the check function
        loopback_ip = ipaddress.IPv4Address("127.0.0.1")
        assert rule.check_func(loopback_ip) is True
        
        normal_ip = ipaddress.IPv4Address("8.8.8.8")
        assert rule.check_func(normal_ip) is False


class TestIPBlocker:
    """Test cases for IPBlocker class."""

    def test_init(self):
        """Test IPBlocker initialization."""
        blocker = IPBlocker()
        
        # Check that known block IPs are set
        expected_ips = {
            "127.0.0.1",
            "0.0.0.0", 
            "192.168.0.1",
            "192.168.1.1",
            "203.98.7.65"
        }
        assert blocker.known_block_ips == expected_ips
        
        # Check that rules are set up
        assert len(blocker.rules) == 6
        rule_names = [rule.name for rule in blocker.rules]
        expected_names = ["loopback", "unspecified", "private", "multicast", "link_local", "reserved"]
        assert rule_names == expected_names

    def test_add_blocked_ip(self):
        """Test adding IPs to the blocked list."""
        blocker = IPBlocker()
        initial_count = len(blocker.known_block_ips)
        
        blocker.add_blocked_ip("1.2.3.4")
        assert "1.2.3.4" in blocker.known_block_ips
        assert len(blocker.known_block_ips) == initial_count + 1
        
        # Adding the same IP again shouldn't increase count
        blocker.add_blocked_ip("1.2.3.4")
        assert len(blocker.known_block_ips) == initial_count + 1

    def test_remove_blocked_ip(self):
        """Test removing IPs from the blocked list."""
        blocker = IPBlocker()
        
        # Add an IP first
        blocker.add_blocked_ip("1.2.3.4")
        assert "1.2.3.4" in blocker.known_block_ips
        
        # Remove it
        blocker.remove_blocked_ip("1.2.3.4")
        assert "1.2.3.4" not in blocker.known_block_ips
        
        # Removing non-existent IP should not raise error
        blocker.remove_blocked_ip("5.6.7.8")  # Should not raise

    def test_is_blocked_ip_loopback(self):
        """Test blocking of loopback addresses."""
        blocker = IPBlocker()
        
        is_blocked, reason = blocker.is_blocked_ip("127.0.0.1")
        assert is_blocked is True
        assert "Loopback IP" in reason
        
        is_blocked, reason = blocker.is_blocked_ip("127.0.0.2")
        assert is_blocked is True
        assert "Loopback IP" in reason

    def test_is_blocked_ip_unspecified(self):
        """Test blocking of unspecified addresses."""
        blocker = IPBlocker()
        
        is_blocked, reason = blocker.is_blocked_ip("0.0.0.0")
        assert is_blocked is True
        assert "Unspecified IP" in reason

    def test_is_blocked_ip_private(self):
        """Test blocking of private IP ranges."""
        blocker = IPBlocker()
        
        private_ips = [
            "192.168.1.1",
            "192.168.0.100", 
            "10.0.0.1",
            "172.16.0.1",
            "172.31.255.254"
        ]
        
        for ip in private_ips:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is True, f"IP {ip} should be blocked"
            assert "Private IP range" in reason

    def test_is_blocked_ip_multicast(self):
        """Test blocking of multicast addresses."""
        blocker = IPBlocker()
        
        multicast_ips = [
            "224.0.0.1",
            "239.255.255.255"
        ]
        
        for ip in multicast_ips:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is True, f"IP {ip} should be blocked"
            assert "Multicast address" in reason

    def test_is_blocked_ip_link_local(self):
        """Test blocking of link-local addresses."""
        blocker = IPBlocker()
        
        link_local_ips = [
            "169.254.1.1",
            "169.254.255.254"
        ]
        
        for ip in link_local_ips:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is True, f"IP {ip} should be blocked"
            assert "Link-local address" in reason

    def test_is_blocked_ip_reserved(self):
        """Test blocking of reserved addresses."""
        blocker = IPBlocker()
        
        # Test some reserved ranges
        reserved_ips = [
            "240.0.0.1",  # Reserved for future use
            "255.255.255.255"  # Broadcast
        ]
        
        for ip in reserved_ips:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is True, f"IP {ip} should be blocked"
            assert "Reserved IP range" in reason

    def test_is_blocked_ip_known_list(self):
        """Test blocking of IPs in known block list."""
        blocker = IPBlocker()
        
        # Test default known blocked IPs
        known_blocked = ["203.98.7.65"]  # This one isn't caught by other rules
        
        for ip in known_blocked:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is True, f"IP {ip} should be blocked"
            assert "Matched known block IP list" in reason

    def test_is_blocked_ip_valid_public(self):
        """Test that valid public IPs are not blocked."""
        blocker = IPBlocker()
        
        public_ips = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "208.67.222.222", # OpenDNS
            "74.125.224.72"   # Google
        ]
        
        for ip in public_ips:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is False, f"IP {ip} should not be blocked"
            assert reason == "Looks okay"

    def test_is_blocked_ip_invalid_format(self):
        """Test handling of invalid IP formats."""
        blocker = IPBlocker()
        
        invalid_ips = [
            "not.an.ip",
            "256.256.256.256",
            "192.168.1",
            "192.168.1.1.1",
            "",
            "abc.def.ghi.jkl"
        ]
        
        for ip in invalid_ips:
            is_blocked, reason = blocker.is_blocked_ip(ip)
            assert is_blocked is False, f"Invalid IP {ip} should return False"
            assert "Invalid IP format" in reason

    def test_rule_priority(self):
        """Test that rules are checked in order and first match wins."""
        blocker = IPBlocker()
        
        # 127.0.0.1 should match loopback rule first, not known block list
        is_blocked, reason = blocker.is_blocked_ip("127.0.0.1")
        assert is_blocked is True
        assert "Loopback IP" in reason
        assert "Matched known block IP list" not in reason

    def test_ipv6_addresses(self):
        """Test that IPv6 addresses are handled correctly."""
        blocker = IPBlocker()
        
        # IPv6 loopback
        is_blocked, reason = blocker.is_blocked_ip("::1")
        assert is_blocked is True
        assert "Loopback IP" in reason
        
        # IPv6 unspecified
        is_blocked, reason = blocker.is_blocked_ip("::")
        assert is_blocked is True
        assert "Unspecified IP" in reason

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        blocker = IPBlocker()
        
        # Test boundary of private ranges
        is_blocked, reason = blocker.is_blocked_ip("192.167.255.255")
        assert is_blocked is False  # Just outside private range
        
        is_blocked, reason = blocker.is_blocked_ip("192.168.0.0")
        assert is_blocked is True   # Start of private range
        
        # Test multicast boundary
        is_blocked, reason = blocker.is_blocked_ip("223.255.255.255")
        assert is_blocked is False  # Just before multicast
        
        is_blocked, reason = blocker.is_blocked_ip("224.0.0.0")
        assert is_blocked is True   # Start of multicast

    def test_custom_blocked_ip_management(self):
        """Test adding and removing custom blocked IPs."""
        blocker = IPBlocker()
        
        # Add a custom IP
        custom_ip = "1.2.3.4"
        blocker.add_blocked_ip(custom_ip)
        
        is_blocked, reason = blocker.is_blocked_ip(custom_ip)
        assert is_blocked is True
        assert "Matched known block IP list" in reason
        
        # Remove the custom IP
        blocker.remove_blocked_ip(custom_ip)
        
        is_blocked, reason = blocker.is_blocked_ip(custom_ip)
        assert is_blocked is False
        assert reason == "Looks okay" 