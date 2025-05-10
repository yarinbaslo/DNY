import logging
from dns_forwarder import DNSForwarder

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create and start DNS forwarder
    forwarder = DNSForwarder()
    try:
        forwarder.start()
    except KeyboardInterrupt:
        logging.info("DNS Forwarder stopped by user")
    except Exception as e:
        logging.error(f"DNS Forwarder stopped due to error: {str(e)}")

if __name__ == "__main__":
    main() 