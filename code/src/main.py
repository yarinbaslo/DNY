import logging
from dns_manager import DNSManager

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create and start DNS forwarder
    forwarder = DNSManager()
    try:
        forwarder.start()
    except KeyboardInterrupt:
        logging.info("DNS Forwarder stopped by user")
        forwarder.stop()  # Ensure we stop the forwarder when interrupted
    except Exception as e:
        logging.error("DNS Forwarder stopped due to error: %s", str(e))
        forwarder.stop()  # Also stop the forwarder on any other error
    finally:
        # Make sure we always stop the forwarder, even if an unexpected error occurs
        if forwarder:
            forwarder.stop()

if __name__ == "__main__":
    main() 