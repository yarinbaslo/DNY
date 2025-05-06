# DNS Notification System

A system for monitoring and notifying about DNS-related events.

## Requirements

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the setup script to install system dependencies:
```bash
python setup.py
```

This will automatically install required system packages:
- On macOS: terminal-notifier (for notifications)
- On Linux: libnotify-bin (for notifications)
- On Windows: win10toast (for notifications)

## Usage

Run the test script to verify notifications are working:
```bash
python test.py
```

You should see a notification appear on your screen.

## Troubleshooting

### macOS Notifications
If notifications aren't appearing:
1. Make sure terminal-notifier is installed: `brew install terminal-notifier`
2. Check System Preferences > Notifications to ensure your terminal app has notification permissions
3. Run `python setup.py` to verify the installation

### Linux Notifications
If notifications aren't appearing:
1. Make sure libnotify-bin is installed: `sudo apt-get install libnotify-bin`
2. Run `python setup.py` to verify the installation

### Windows Notifications
If notifications aren't appearing:
1. Make sure win10toast is installed: `pip install win10toast`
2. Run `python setup.py` to verify the installation 