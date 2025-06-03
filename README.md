# DNY - Dynamic Domain Name for You
*Computer Communication Workshop Project*

**Team Members:** Dana Haham, Noa Pinsler, Yarin Baslo

<div align="center">
<img width="376" alt="image" src="https://github.com/user-attachments/assets/16a7372c-19f0-4672-8989-763b15231429" />
</div>


## Project Overview

DNY (Dynamic Domain Name for You) is an intelligent DNS tool that automatically detects and bypasses DNS-based restrictions while maintaining system integrity. The tool provides seamless access to blocked websites through dynamic DNS server switching, combined with AI-powered content safety analysis. It operates transparently, requiring zero technical expertise from users.

---

### Docs

1. **Ideation and Design**
2. **Presentation**

---

### Key Value Propositions
- **Zero-Touch Operation**: Fully automated DNS switching without user intervention
- **Precision Targeting**: Only switches DNS for blocked requests, preserving global settings
- **Cross-Platform Support**: Compatible with Windows, macOS, and Linux
- **Intelligent Content Analysis**: AI-powered safety warnings for potentially harmful content
- **High Performance**: Sub-50ms response times with advanced caching

---

### Features

#### Intelligent DNS Proxy Service:
- Acts as a local DNS server intercepting all DNS queries on port 53.
- Ensures cross-platform compatibility (Windows, macOS, Linux).
- Provides intelligent DNS resolution.

#### Automatic Network Connection & Management:
- **Automatic Network Interface Detection**: Identifies active network interfaces for DNS interception.
- **Smart Interface Selection**: Chooses the most relevant interface for optimal performance.
- **Local DNS Discovery**: Automatically detects and utilizes the user's existing DNS servers as primary resolvers.
- **Seamless DNS Integration**: Adds an intelligent fallback layer without disrupting the user's original DNS configuration.

#### Automatic Block Detection:
- **Real-Time Monitoring**: Continuously monitors DNS resolution attempts to detect when a domain fails to resolve due to censorship or technical issues.
- **Multi-Condition Diagnosis**: Identifies various failure types, including no response, timeout, invalid or unreachable IP addresses, and determines if the issue is DNS-related.

#### Dynamic Switching & Fallback:
- Dynamically switches to alternative DNS servers when blocks are detected.
- Multi-tier fallback mechanism to ensure access even if primary fallback DNS servers fail.
- Server for monitoring fallback DNS servers.
- Offline operation support through a cache-based mechanism for faster access.

#### Ethical Content Analysis:
- Uses AI-powered large language models (LLMs) for real-time website safety assessment.
- Analyzes content before user access to provide warnings for potentially harmful, unethical, or unsafe sites.
- Risk level classification and clear warnings to maintain user safety and informed access.

#### High-Performance Caching System:
- Advanced caching for faster repeat queries.
- Thread-safe cache operations with FIFO eviction policy.

### Project Structure
```
DNY/
├── src/dny/               # Main application code
│   ├── dns/              # DNS components
│   ├── os_handlers/      # OS-specific handlers
│   ├── content/          # Content analysis
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── docs/                 # Documentation
├── config/               # Configuration files
├── scripts/              # Utility scripts
└── deployment/           # Deployment configurations
```
