# DNY - Dynamic Domain Name for You

<div align="center">
  <img width="376" alt="DNY Logo" src="https://github.com/user-attachments/assets/16a7372c-19f0-4672-8989-763b15231429" />
  
  [![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
  [![MySQL](https://img.shields.io/badge/MySQL-8.x-blue.svg)](https://mysql.com)
  [![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20RDS-orange.svg)](https://aws.amazon.com)
  [![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5%20Turbo-green.svg)](https://openai.com)
  [![Grafana](https://img.shields.io/badge/Grafana-Dashboard-blue.svg)](https://grafana.com)
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

### 📊 Comprehensive Monitoring Dashboards
- **Grafana Integration**: Interactive dashboards for real-time system monitoring
- **Inner Stats Dashboard**: Detailed performance metrics and system health monitoring
- **User Surf Patterns Dashboard**: Analytics on browsing patterns and DNS query insights

### 💾 Robust Data Storage
- **Database Management**: Centralized data storage for users, DNS queries and cache entries
- **Persistent Storage**: Maintains historical data for analysis and AI Insights
- **Data Integrity**: Ensures reliable storage of DNS resolution patterns and user preferences

### 🔔 Intelligent Notification System
- **Real-Time Alerts**: Instant notifications for system events and warnings
- **User-Friendly Messaging**: Clear, actionable notifications for system status updates


## 📖 Documentation

- [Abstract idea & High Level Architecture](https://docs.google.com/document/d/1vMAOhPR4wX_nsEkNH9xgcRl6WmOqgszwer-hzn650JI/edit?usp=sharing)
- [Presentation](https://docs.google.com/presentation/d/1AtuN2-Qll6NSADQBEKt9p-TmCLhxsIl0xbgi3fFuFaQ/edit?usp=sharing)
