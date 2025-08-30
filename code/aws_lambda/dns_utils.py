import logging
import dns.resolver
import pymysql  # MySQL client

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def is_dns_server_valid(ip_address):
    """
    Checks if a DNS server is responsive.
    """
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ip_address]
    resolver.timeout = 2
    resolver.lifetime = 2
    try:
        resolver.resolve('google.com', 'A')
        logger.info(f"DNS server {ip_address} is valid.")
        return True
    except Exception as e:
        logger.warning(f"DNS server {ip_address} is NOT valid. Reason: {e}")
        return False

def clean_invalid_dns(connection):
    """
    Checks each DNS IP in dns_servers and updates is_active column.
    """
    logger.info("Starting DNS cleanup process...")

    with connection.cursor() as cursor:
        # Fetch all DNS IPs
        cursor.execute("SELECT primary_ip FROM dns_providers")
        dns_servers = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(dns_servers)} DNS servers to check.")

        # Check each DNS server and update status
        for ip in dns_servers:
            active_flag = 'T' if is_dns_server_valid(ip) else 'F'
            cursor.execute(
                "UPDATE dns_providers SET is_active = %s WHERE primary_ip = %s",
                (active_flag, ip)
            )

        connection.commit()

    logger.info("DNS cleanup process finished.")
