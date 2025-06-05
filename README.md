# DNY - Dynamic Domain Name for You

<div align="center">
  <img width="376" alt="DNY Logo" src="https://github.com/user-attachments/assets/16a7372c-19f0-4672-8989-763b15231429" />
  
  [![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
</div>

> **Computer Communication Workshop Project**  
> **Team Members:** Dana Haham, Noa Pinsler, Yarin Baslo

## 🚀 Overview

DNY (Dynamic Domain Name for You) is an intelligent DNS tool that automatically detects and bypasses DNS-based restrictions while maintaining system integrity. The tool provides seamless access to blocked websites through dynamic DNS server switching, combined with AI-powered content safety analysis. It operates transparently, requiring zero technical expertise from users.

## ✨ Key Features

### 🔧 Intelligent DNS Proxy Service
- Acts as a local DNS server intercepting all DNS queries on port 53
- Cross-platform compatibility (Windows, macOS, Linux)
- Intelligent DNS resolution with sub-50ms response times

### 🌐 Automatic Network Management
- **Smart Interface Detection**: Automatically identifies active network interfaces
- **Local DNS Discovery**: Detects and utilizes existing DNS servers as primary resolvers
- **Seamless Integration**: Adds intelligent fallback without disrupting original DNS configuration

### 🛡️ Block Detection & Dynamic Switching
- **Real-Time Monitoring**: Continuously monitors DNS resolution attempts
- **Multi-Condition Diagnosis**: Identifies various failure types (timeout, invalid IP, unreachable addresses)
- **Dynamic Fallback**: Multi-tier fallback mechanism with alternative DNS servers
- **Offline Support**: Cache-based mechanism for faster access

### 🔍 Ethical Content Analysis
- AI-powered safety assessment using large language models (LLMs)
- Real-time website content analysis before user access
- Risk level classification with clear warnings
- Maintains user safety and informed access decisions

### ⚡ High-Performance Caching
- Advanced caching system for faster repeat queries
- Thread-safe cache operations with FIFO eviction policy
- Optimized for minimal latency and maximum throughput

## 📋 Prerequisites

- Python 3.8 or higher
- Administrator/root privileges (required for DNS interception)
- Internet connection for AI content analysis
- Supported operating systems: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

## 🛠️ Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/your-username/DNY.git
cd DNY

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## 🚀 Usage

### Basic Usage

```bash
# Start DNY service (requires administrator privileges)
sudo python -m dny.main

# Or use the installed command
sudo dny-start
```

### Logging

Enable verbose logging for debugging:
```bash
dny-start --log-level DEBUG
```


## 📁 Project Structure

```
DNY/
├── code/                          # Main application code
│   ├── DNSProxyServiceDeploy/    # Deployment configurations
│   ├── src/                      # Source code
│   │   ├── dns/                  # DNS resolution components
│   │   └── os_handlers/          # OS-specific handlers
│   └── tests/                    # Test suite
├── docs/                         # Documentation
├── .gitignore                    # Git ignore file
├── README.md                     # This file
├── requirements.txt              # Python dependencies
└── setup.py                     # Package setup
```

## 📖 Documentation

- [Abstract idea & High Level Architecture](https://docs.google.com/document/d/1vMAOhPR4wX_nsEkNH9xgcRl6WmOqgszwer-hzn650JI/edit?usp=sharing)
- [Presentation](https://docs.google.com/presentation/d/1wM4SkH57ZGyopNIGB6XlzAySyPkkMxcDJZOvJLJsQ7A/edit?usp=sharing)
