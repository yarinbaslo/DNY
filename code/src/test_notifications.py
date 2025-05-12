import logging
from os_handlers.factory import OSHandlerFactory

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_notifications():
    # Create OS handler
    handler = OSHandlerFactory.create_handler()
    
    # Test different types of notifications
    notifications = [
        ("Test Info", "This is an info notification", "info"),
        ("Test Warning", "This is a warning notification", "warning"),
        ("Test Error", "This is an error notification", "error")
    ]
    
    for title, message, type_ in notifications:
        print(f"\nTesting {type_} notification...")
        handler.notify(title, message, notification_type=type_)

if __name__ == "__main__":
    test_notifications() 