import subprocess
import sys
import platform

def check_terminal_notifier():
    """Check if terminal-notifier is installed, install if not."""
    try:
        # Check if terminal-notifier is installed
        subprocess.run(['terminal-notifier', '-help'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print("✓ terminal-notifier is already installed")
        return True
    except FileNotFoundError:
        print("terminal-notifier not found. Attempting to install...")
        try:
            # Check if Homebrew is installed
            subprocess.run(['brew', '--version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
            
            # Install terminal-notifier using Homebrew
            subprocess.run(['brew', 'install', 'terminal-notifier'], 
                         check=True)
            print("✓ terminal-notifier installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print("Error installing terminal-notifier:", str(e))
            return False
        except FileNotFoundError:
            print("Error: Homebrew is not installed. Please install Homebrew first:")
            print("  /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False

def setup():
    """Run all setup tasks."""
    if platform.system() != 'Darwin':
        print("Note: terminal-notifier is only required on macOS")
        return True

    return check_terminal_notifier()

if __name__ == "__main__":
    if setup():
        print("Setup completed successfully!")
    else:
        print("Setup failed. Please check the errors above.")
        sys.exit(1) 