import platform
from .base import OSHandler
from .linux import LinuxHandler
from .macos import MacOSHandler
from .windows import WindowsHandler

class OSHandlerFactory:
    @staticmethod
    def create_handler() -> OSHandler:
        """Create the appropriate OS handler based on the current operating system."""
        system = platform.system().lower()
        
        handlers = {
            'linux': LinuxHandler,
            'darwin': MacOSHandler,
            'windows': WindowsHandler
        }
        
        handler_class = handlers.get(system)
        if handler_class is None:
            raise NotImplementedError(f"Unsupported operating system: {system}")
            
        return handler_class() 