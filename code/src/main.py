import logging
import signal
import sys
from dns_manager import DNSManager

def signal_handler(sig, frame):
    logging.info("Received stop signal, stopping DNS forwarder...")
    forwarder.stop()
    sys.exit(0)

def main():
    # Configure logging to file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("dns_forwarder.log"),  # Log to a file
            logging.StreamHandler(sys.stdout)  # Also log to console
        ]
    )

    # Create and start DNS forwarder
    global forwarder
    forwarder = DNSManager()
    forwarder.start()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep the service running
    signal.pause()

if __name__ == "__main__":
    main() 
