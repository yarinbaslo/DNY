# DNY (Dynamic Domain Name for You) - High Level Architecture

## Overview
DNY is a sophisticated DNS proxy service that provides intelligent DNS resolution with AI-powered content filtering, caching, and cross-platform compatibility.

---

## 1. What are the system main components?

### Core System Components

```
DNY Service Architecture
├── DNS Manager (Central Orchestrator)
├── DNS Server (Local Port 53 Listener)
├── DNS Resolver (Query Processing Engine)
├── Content Checker (AI-Powered Analysis)
├── DNS Cache (Performance Optimization)
├── IP Blocker (Security Layer)
├── OS Handlers (Platform Abstraction)
└── Notification Manager (User Communication)
```

### Component Details

**1. DNS Manager (`dns_manager.py`)**
- Central orchestrator for all DNS operations
- Service lifecycle management (start/stop/restart)
- Cross-platform DNS configuration management
- Integration with OS-specific handlers

**2. DNS Server (`dns/server.py`)**
- Local DNS server listening on port 53
- Multi-threaded request handling
- UDP protocol implementation
- 10-second socket timeout with 512-byte buffer

**3. DNS Resolver (`dns/resolver.py`)**
- Core DNS resolution engine
- Primary DNS server querying
- Response validation and filtering
- Fallback DNS server integration
- Cache integration for performance

**4. Content Checker (`content_checker.py`)**
- AI-powered website content analysis
- OpenAI GPT-3.5 Turbo integration
- Web content scraping and parsing
- Risk assessment scoring
- SSL certificate validation

**5. DNS Cache (`dns/cache.py`)**
- High-performance caching layer
- 1000 entries maximum capacity
- 5-minute default TTL
- FIFO eviction policy
- Thread-safe operations

**6. IP Blocker (`ip_blocker.py`)**
- Security layer for IP filtering
- Blocks loopback, private, and reserved IP ranges
- Custom blocklist support
- Performance-optimized validation

**7. OS Handlers**
- **Windows Handler**: Uses `netsh` commands, requires admin privileges
- **macOS Handler**: Uses `networksetup`, requires sudo privileges  
- **Linux Handler**: Direct `/etc/resolv.conf` manipulation, requires root

**8. Notification Manager (`notification_manager.py`)**
- Cross-platform user notifications
- Windows: win10toast library
- macOS: osascript AppleScript
- Linux: notify-send desktop notifications

---

## 2. What is the back-end technology?

### Core Technology Stack

**Programming Language**
- **Python 3.9+** - Primary development language

**DNS Processing**
- **Custom UDP Socket Implementation** - Direct socket programming for DNS packet handling
- **Threading & ThreadPoolExecutor** - Concurrent request processing
- **Socket Configuration** - SO_REUSEADDR for port reuse

**AI Integration**
- **OpenAI GPT-3.5 Turbo API** - Content analysis and risk assessment
- **REST API Communication** - HTTP requests to OpenAI services

**Web Scraping & Content Analysis**
- **BeautifulSoup4** - HTML parsing and content extraction
- **Requests Library** - HTTP client for web content fetching
- **SSL/TLS Support** - Certificate validation and secure connections

**System Integration**
- **psutil** - System and process utilities
- **Platform-specific Commands** - OS-level DNS configuration
  - Windows: `netsh` commands
  - macOS: `networksetup` commands
  - Linux: Direct file manipulation

**Data Management**
- **In-Memory Caching** - Fast DNS response caching
- **File-based Configuration** - JSON/YAML configuration files
- **Logging Framework** - Structured logging with rotation

**Concurrency & Performance**
- **Multi-threading** - Concurrent DNS request handling
- **Thread Pools** - Managed thread execution
- **Asynchronous Operations** - Non-blocking I/O where applicable
- **Resource Management** - Automatic cleanup and resource pooling

**Security**
- **Input Validation** - DNS query and response validation
- **IP Range Filtering** - Network security controls
- **Privilege Management** - OS-level permission handling
- **API Key Management** - Secure credential storage

**Testing Framework**
- **unittest** - Python standard testing framework
- **Mock Objects** - Comprehensive mocking for unit tests
- **Integration Testing** - Cross-component testing
- **Platform Testing** - OS-specific functionality validation

---

## 3. What is the front-end technology?

### Front-end Architecture

**Command Line Interface (CLI)**
- **Python CLI Framework** - Command-line argument parsing
- **Interactive Commands** - Start, stop, restart, status operations
- **Configuration Management** - CLI-based configuration updates
- **Real-time Status Display** - Service health and performance metrics

**Cross-Platform Notifications**
- **Native OS Notifications** - Platform-specific notification systems
- **Toast Notifications (Windows)** - win10toast library integration
- **AppleScript Notifications (macOS)** - Native macOS notification center
- **Desktop Notifications (Linux)** - notify-send integration

**Logging and Monitoring Interface**
- **Structured Log Output** - Formatted log messages with levels
- **Real-time Log Streaming** - Live log monitoring capabilities
- **Performance Metrics Display** - Cache hit rates, response times
- **Error Reporting** - Detailed error messages and stack traces


---

## Data Flow Architecture

```
Client Request → DNS Server (Port 53) → Cache Lookup → DNS Resolver → Content Checker → Response Validation → Client Response
                                    ↓                        ↓                    ↓
                                Cache Storage         AI Analysis        IP Blocking
                                    ↓                        ↓                    ↓
                            Performance Metrics    Risk Assessment    Security Logging
```

### Request Processing Flow

1. **Client DNS Query** - Application requests domain resolution
2. **Local Interception** - DNY server captures request on port 53
3. **Cache Check** - Look for existing cached response
4. **Primary Resolution** - Forward to configured DNS server if cache miss
5. **Content Analysis** - AI-powered safety assessment of domain
6. **IP Validation** - Security filtering of resolved IP addresses
7. **Response Delivery** - Return validated response to client
8. **Cache Storage** - Store response for future requests
9. **Logging & Metrics** - Record performance and security data

---

## Deployment Architecture

### Local Deployment
- **Single Machine Installation** - All components on one system
- **Service-based Architecture** - Background service operation
- **OS Integration** - Native system service registration
- **Automatic Startup** - Boot-time service initialization

### Network Architecture
- **Local DNS Server** - Binds to localhost:53
- **Upstream DNS Integration** - Configurable primary/fallback servers
- **Content Analysis Network** - External API communication
- **Security Filtering** - Local IP blocking and validation

### Security Architecture
- **Privilege Separation** - Minimal required permissions
- **Network Isolation** - Local-only DNS binding
- **API Security** - Secure external service communication
- **Configuration Protection** - Secure credential storage

---

## Technology Rationale

### Why Python?
- **Cross-platform Compatibility** - Runs on Windows, macOS, Linux
- **Rich Ecosystem** - Extensive libraries for DNS, networking, AI
- **Rapid Development** - Fast prototyping and iteration
- **Community Support** - Large developer community and resources

### Why Custom DNS Implementation?
- **Performance Control** - Optimized for specific use cases
- **Feature Integration** - Seamless AI and security integration
- **Flexibility** - Custom filtering and routing capabilities
- **Learning Opportunity** - Deep understanding of DNS protocols

### Why AI Integration?
- **Intelligent Filtering** - Context-aware content analysis
- **Adaptive Security** - Dynamic threat assessment
- **User Safety** - Proactive harmful content detection
- **Future-proofing** - Scalable AI-powered features

---

This architecture provides a solid foundation for intelligent DNS management with room for future enhancements and enterprise-grade features. 