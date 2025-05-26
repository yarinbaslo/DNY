# DNY - Dynamic Domain Name for You
## Presentation Charts & Diagrams

---

## 1. SYSTEM ARCHITECTURE CHARTS

### 1.1 Connecting to Computer (Finding Free Network Cards)

```mermaid
flowchart TD
    A[DNY Service Start] --> B{Detect Operating System}
    B -->|Windows| C[WindowsHandler]
    B -->|macOS| D[MacOSHandler] 
    B -->|Linux| E[LinuxHandler]
    
    C --> F[Use psutil to scan interfaces]
    D --> G[Use networksetup commands]
    E --> H[Use ip route commands]
    
    F --> I[Find Wi-Fi/WLAN interfaces]
    G --> J[Query network services]
    H --> K[Check interface status]
    
    I --> L{Interface has IPv4?}
    J --> M{Service connected?}
    K --> N{Interface UP + IP?}
    
    L -->|Yes| O[Select Active Interface]
    M -->|Yes| O
    N -->|Yes| O
    
    L -->|No| P[Try next interface]
    M -->|No| P
    N -->|No| P
    
    O --> Q[Configure DNS on Interface]
    P --> R{More interfaces?}
    R -->|Yes| I
    R -->|No| S[Error: No active interface]
```

**Key Components:**
- **Cross-platform detection**: Windows (psutil), macOS (networksetup), Linux (ip commands)
- **Interface validation**: IPv4 address presence, UP status, connectivity
- **Automatic selection**: First available active interface

---

### 1.2 Automatic Disconnection & Restoration

```mermaid
sequenceDiagram
    participant U as User
    participant DNY as DNY Service
    participant OS as OS Handler
    participant DNS as DNS Server
    
    U->>DNY: Stop Service (Ctrl+C)
    DNY->>DNS: Stop DNS Server
    DNS->>DNS: Close socket connections
    DNS->>DNY: Server stopped
    
    DNY->>OS: Restore DNS to DHCP
    OS->>OS: Execute platform command
    Note over OS: Windows: netsh set dns source=dhcp<br/>macOS: networksetup -setdnsservers<br/>Linux: restore /etc/resolv.conf
    
    OS->>DNY: DNS restored
    DNY->>U: Notification: "DNS restored to automatic"
    DNY->>DNY: Cleanup resources
    DNY->>U: Service stopped gracefully
```

---

### 1.3 Finding DNS Server

```mermaid
flowchart LR
    A[Start DNS Detection] --> B{Operating System}
    
    B -->|Windows| C[ipconfig /all]
    B -->|macOS| D[scutil --dns + /etc/resolv.conf]
    B -->|Linux| E[/etc/resolv.conf]
    
    C --> F[Parse DNS Servers regex]
    D --> G[Extract nameserver entries]
    E --> H[Read nameserver lines]
    
    F --> I{DNS = 127.0.0.1?}
    G --> J[Primary DNS Found]
    H --> J
    
    I -->|Yes| K[Restore DHCP & Retry]
    I -->|No| J
    
    K --> C
    J --> L[Store as Primary DNS]
    L --> M[Set Fallback: 8.8.8.8]
    
    M --> N[DNS Configuration Complete]
    
    style J fill:#90EE90
    style N fill:#87CEEB
```

---

### 1.4 Creating Service Architecture

```mermaid
graph TB
    subgraph "DNY Service Architecture"
        A[main.py] --> B[DNSManager]
        B --> C[OSHandlerFactory]
        B --> D[NotificationManager]
        B --> E[DNSResolver]
        B --> F[DNSServer]
        
        C --> G[WindowsHandler]
        C --> H[MacOSHandler]
        C --> I[LinuxHandler]
        
        E --> J[DNSCache]
        E --> K[IPBlocker]
        E --> L[ContentChecker]
        
        F --> M[Socket Listener :53]
        F --> N[Thread Pool]
        
        L --> O[OpenAI GPT-3.5]
        L --> P[BeautifulSoup Parser]
        
        D --> Q[System Notifications]
    end
    
    subgraph "External Dependencies"
        R[Primary DNS Server]
        S[Fallback DNS: 8.8.8.8]
        T[OpenAI API]
        U[Target Websites]
    end
    
    E -.-> R
    E -.-> S
    L -.-> T
    L -.-> U
    
    style B fill:#FFB6C1
    style E fill:#98FB98
    style F fill:#87CEFA
```

---

### 1.5 Server Operation Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant DS as DNS Server
    participant DR as DNS Resolver
    participant Cache as DNS Cache
    participant PD as Primary DNS
    participant FS as Fallback Server
    participant WD as Working DNS
    participant CC as Content Checker
    
    C->>DS: DNS Query (domain.com)
    DS->>DR: Resolve Query
    
    DR->>Cache: Check Cache
    Cache-->>DR: Cache Miss
    
    DR->>PD: Query Primary DNS
    PD-->>DR: Timeout/Block
    
    DR->>FS: Request Working DNS List
    FS-->>DR: Active DNS Servers + Performance Metrics
    
    DR->>WD: Query Best Available DNS
    WD-->>DR: DNS Response
    
    DR->>DR: Validate IPs (IPBlocker)
    DR->>CC: Check Domain Content
    CC-->>DR: Content Analysis Result
    
    DR->>Cache: Store Response
    DR-->>DS: Return Response
    DS-->>C: DNS Response
    
    Note over FS: Maintains real-time list of:<br/>• Working DNS servers<br/>• Performance metrics<br/>• Availability status
    Note over CC: AI-powered content analysis<br/>Risk assessment<br/>Ethical validation
```

---

### 1.6 Cache System Architecture

```mermaid
graph TD
    A[DNS Query] --> B{Cache Check}
    B -->|Hit| C[Return Cached Response]
    B -->|Miss| D[Forward to DNS Resolver]
    
    D --> E[Get DNS Response]
    E --> F[Store in Cache]
    F --> G[Return Response]
    
    subgraph "Cache Management"
        H[TTL: 5 minutes]
        I[Max Size: 1000 entries]
        J[FIFO Eviction]
        K[Thread-Safe Operations]
    end
    
    F --> H
    F --> I
    I --> J
    F --> K
    
    subgraph "Cache Warming"
        L[Popular Domains]
        M[Pre-fetch on Start]
        N[Background Refresh]
    end
    
    style C fill:#90EE90
    style G fill:#90EE90
    style H fill:#FFE4B5
```

---

### 1.7 Block Detection Mechanism

```mermaid
flowchart TD
    A[DNS Response Received] --> B[Parse DNS Packet]
    B --> C{Answer Count > 0?}
    C -->|No| D[Block Detected: No Answers]
    C -->|Yes| E[Extract IP Addresses]
    
    E --> F[Validate Each IP]
    F --> G{IP Validation}
    
    G -->|Loopback| H[Block: 127.0.0.1]
    G -->|Private| I[Block: 192.168.x.x]
    G -->|Link-Local| J[Block: 169.254.x.x]
    G -->|Reserved| K[Block: Reserved Range]
    G -->|Known Block List| L[Block: ISP Redirect]
    G -->|Valid| M[Allow Response]
    
    H --> N[Switch to Fallback DNS]
    I --> N
    J --> N
    K --> N
    L --> N
    
    M --> O[Return Valid Response]
    N --> P[Retry with Alternative DNS]
    
    style D fill:#FFB6C1
    style H fill:#FFB6C1
    style I fill:#FFB6C1
    style J fill:#FFB6C1
    style K fill:#FFB6C1
    style L fill:#FFB6C1
    style O fill:#90EE90
```

---

### 1.8 Block Resolution Process

```mermaid
sequenceDiagram
    participant U as User Request
    participant DS as DNS Server
    participant PD as Primary DNS
    participant BD as Block Detector
    participant FD as Fallback DNS
    participant N as Notifier
    
    U->>DS: Request blocked-site.com
    DS->>PD: Query Primary DNS
    PD-->>DS: Blocked Response (127.0.0.1)
    
    DS->>BD: Validate Response
    BD->>BD: Check IP against rules
    BD-->>DS: Block Detected
    
    DS->>FD: Query Fallback DNS (8.8.8.8)
    FD-->>DS: Valid Response (Real IP)
    
    DS->>BD: Validate Fallback Response
    BD-->>DS: Valid Response
    
    DS->>N: Notify DNS Switch
    N-->>U: "Switched to Google DNS"
    
    DS-->>U: Return Valid Response
    
    Note over BD: Block Detection Rules:<br/>• Loopback IPs<br/>• Private ranges<br/>• Known redirect IPs<br/>• Reserved ranges
```

---

### 1.9 AI Content Analysis

```mermaid
graph TB
    A[Domain Request] --> B[Extract Domain Name]
    B --> C{Content Check Enabled?}
    C -->|No| D[Skip Analysis]
    C -->|Yes| E[Validate Domain Format]
    
    E --> F[Check robots.txt]
    F --> G[Fetch Website Content]
    G --> H[Parse HTML Content]
    
    H --> I[Extract Key Information]
    I --> J[Title & Meta Description]
    I --> K[Main Content Text]
    I --> L[SSL Certificate Status]
    
    J --> M[Prepare AI Prompt]
    K --> M
    L --> M
    
    M --> N[Send to GPT-3.5]
    N --> O[Receive Risk Analysis]
    
    O --> P{Risk Level}
    P -->|Low| Q[Allow Access]
    P -->|Medium| R[Warn User]
    P -->|High| S[Block & Alert]
    
    R --> T[Show Warning Notification]
    S --> U[Show Block Notification]
    
    style Q fill:#90EE90
    style R fill:#FFE4B5
    style S fill:#FFB6C1
    style N fill:#87CEEB
```

---

### 1.10 Notification System

```mermaid
graph LR
    subgraph "Notification Events"
        A[DNS Change]
        B[Service Status]
        C[Content Warning]
        D[Error Alert]
        E[Block Detection]
    end
    
    subgraph "Notification Manager"
        F[Event Handler]
        G[Message Formatter]
        H[OS Router]
    end
    
    subgraph "Platform Handlers"
        I[Windows: win10toast]
        J[macOS: osascript]
        K[Linux: notify-send]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    G --> H
    
    H -->|Windows| I
    H -->|macOS| J
    H -->|Linux| K
    
    I --> L[Toast Notification]
    J --> M[System Alert]
    K --> N[Desktop Notification]
    
    style F fill:#98FB98
    style L fill:#87CEEB
    style M fill:#87CEEB
    style N fill:#87CEEB
```

---

## 2. SUPER ARCHITECTURE CHART

```mermaid
graph TB
    subgraph "User Layer"
        U1[Web Browser]
        U2[Applications]
        U3[System Processes]
    end
    
    subgraph "DNY Service Layer"
        D1[DNS Manager]
        D2[Local DNS Server :53]
        D3[Request Router]
        D4[Response Validator]
    end
    
    subgraph "Intelligence Layer"
        I1[DNS Cache<br/>TTL: 5min<br/>Size: 1000]
        I2[IP Blocker<br/>Rules Engine]
        I3[Content Checker<br/>AI Analysis]
        I4[Notification System]
    end
    
    subgraph "OS Integration Layer"
        O1[Network Interface<br/>Management]
        O2[DNS Configuration<br/>Control]
        O3[System Notifications]
        O4[Service Management]
    end
    
    subgraph "External Services"
        E1[Primary DNS<br/>ISP/Local]
        E2[Fallback DNS Server<br/>Working DNS Registry]
        E3[OpenAI API<br/>Content Analysis]
        E4[Target Websites]
    end
    
    U1 --> D2
    U2 --> D2
    U3 --> D2
    
    D2 --> D3
    D3 --> D4
    D1 --> D2
    
    D3 --> I1
    D4 --> I2
    D3 --> I3
    D1 --> I4
    
    D1 --> O1
    D1 --> O2
    I4 --> O3
    D1 --> O4
    
    D3 -.-> E1
    D3 -.-> E2
    I3 -.-> E3
    I3 -.-> E4
    
    style D1 fill:#FFB6C1
    style I1 fill:#98FB98
    style I2 fill:#87CEFA
    style I3 fill:#DDA0DD
    style O2 fill:#F0E68C
```

---

## 3. ROBUSTNESS FEATURES

### 3.1 DNS Server Robustness

```mermaid
graph TD
    A[DNS Server Start] --> B[Socket Creation]
    B --> C[Port 53 Binding]
    C --> D{Binding Success?}
    D -->|No| E[Retry with SO_REUSEADDR]
    D -->|Yes| F[Start Listening Loop]
    
    E --> G{Retry Success?}
    G -->|No| H[Error: Port in use]
    G -->|Yes| F
    
    F --> I[Accept Connections]
    I --> J[Thread Pool Handler]
    J --> K[Process Request]
    K --> L{Request Valid?}
    
    L -->|No| M[Log Error & Continue]
    L -->|Yes| N[Forward to Resolver]
    
    M --> I
    N --> O[Get Response]
    O --> P{Response Valid?}
    P -->|No| Q[Return Error Response]
    P -->|Yes| R[Send to Client]
    
    Q --> I
    R --> I
    
    subgraph "Error Handling"
        S[Socket Timeout: 10s]
        T[Connection Cleanup]
        U[Resource Management]
        V[Exception Logging]
    end
    
    style F fill:#90EE90
    style H fill:#FFB6C1
    style S fill:#FFE4B5
```

### 3.2 Comprehensive Testing

```mermaid
graph LR
    subgraph "Test Categories"
        A[Unit Tests<br/>292 lines]
        B[Integration Tests<br/>417 lines]
        C[DNS Resolution Tests<br/>394 lines]
        D[Content Checker Tests<br/>364 lines]
        E[Cache Tests<br/>176 lines]
        F[OS Handler Tests<br/>417 lines]
    end
    
    subgraph "Test Coverage"
        G[DNS Manager: 403 lines]
        H[Notification: 316 lines]
        I[IP Blocker: 270 lines]
        J[Main Module: 292 lines]
    end
    
    subgraph "Test Features"
        K[Mock Objects]
        L[Error Simulation]
        M[Platform Testing]
        N[Thread Safety]
        O[Performance Tests]
    end
    
    A --> K
    B --> L
    C --> M
    D --> N
    E --> O
    
    style A fill:#98FB98
    style B fill:#87CEEB
    style C fill:#DDA0DD
    style D fill:#F0E68C
```

### 3.3 Cross-Platform Port Management

```mermaid
flowchart TD
    A[Service Start] --> B{Check Platform}
    
    B -->|Windows| C[Windows Service<br/>NSSM Integration]
    B -->|macOS| D[LaunchDaemon<br/>plist Configuration]
    B -->|Linux| E[systemd Service<br/>Unit File]
    
    C --> F[Port 53 Binding<br/>Admin Rights Required]
    D --> G[Port 53 Binding<br/>sudo Required]
    E --> H[Port 53 Binding<br/>root/CAP_NET_BIND_SERVICE]
    
    F --> I[Windows Firewall<br/>Exception]
    G --> J[macOS Network<br/>Permission]
    H --> K[Linux iptables<br/>Configuration]
    
    I --> L[Service Registration<br/>Auto-start]
    J --> M[Launch Agent<br/>User Session]
    K --> N[systemctl enable<br/>Boot Start]
    
    style C fill:#87CEEB
    style D fill:#98FB98
    style E fill:#DDA0DD
```

### 3.4 Watchdog & Health Monitoring

```mermaid
sequenceDiagram
    participant W as Watchdog
    participant S as DNS Service
    participant H as Health Check
    participant N as Notifier
    participant OS as OS Handler
    
    loop Every 30 seconds
        W->>S: Health Check Ping
        S-->>W: Service Status
        
        alt Service Healthy
            W->>H: Log Health Status
        else Service Unresponsive
            W->>N: Alert: Service Down
            W->>S: Attempt Restart
            
            alt Restart Success
                W->>N: Alert: Service Restored
            else Restart Failed
                W->>OS: System Notification
                W->>W: Escalate to Admin
            end
        end
    end
    
    Note over W: Monitors:<br/>• Socket availability<br/>• Response times<br/>• Memory usage<br/>• Error rates
```

### 3.5 Fallback DNS Server Architecture

```mermaid
graph TB
    subgraph "Fallback DNS Server"
        A[DNS Registry Service]
        B[Health Monitor]
        C[Performance Tracker]
        D[Load Balancer]
    end
    
    subgraph "DNS Server Pool"
        E[Google DNS<br/>8.8.8.8]
        F[Cloudflare<br/>1.1.1.1]
        G[Quad9<br/>9.9.9.9]
        H[OpenDNS<br/>208.67.222.222]
        I[ISP DNS Servers]
        J[Custom DNS Servers]
    end
    
    subgraph "Monitoring Data"
        K[Response Time<br/>< 50ms]
        L[Availability<br/>> 99%]
        M[Success Rate<br/>> 95%]
        N[Geographic Location]
        O[Content Filtering]
    end
    
    A --> B
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I
    B --> J
    
    C --> K
    C --> L
    C --> M
    C --> N
    C --> O
    
    D --> A
    K --> D
    L --> D
    M --> D
    
    style A fill:#87CEEB
    style B fill:#98FB98
    style D fill:#DDA0DD
```

### 3.6 Fallback Mechanisms

```mermaid
graph TD
    A[DNS Request] --> B[Primary DNS]
    B --> C{Response OK?}
    C -->|Yes| D[Validate Response]
    C -->|No| E[Query Fallback Server]
    
    D --> F{Valid IPs?}
    F -->|Yes| G[Return Response]
    F -->|No| E
    
    E --> H[Fallback DNS Server<br/>Working DNS Registry]
    H --> I[Get Active DNS List]
    I --> J[Select Best DNS Server<br/>Based on Performance]
    
    J --> K{DNS Server Available?}
    K -->|Yes| L[Query Selected DNS]
    K -->|No| M[Try Next DNS in List]
    
    L --> N{Response OK?}
    N -->|Yes| O[Validate Response]
    N -->|No| P[Mark DNS as Failed]
    
    O --> Q{Valid IPs?}
    Q -->|Yes| R[Return Response]
    Q -->|No| P
    
    P --> S[Update Server Status]
    S --> M
    
    M --> T{More DNS Servers?}
    T -->|Yes| L
    T -->|No| U[Return Error]
    
    style G fill:#90EE90
    style R fill:#98FB98
    style H fill:#87CEEB
    style U fill:#FFB6C1
```

### 3.7 Automatic Network Restoration

```mermaid
flowchart LR
    A[Service Stop Signal] --> B[Graceful Shutdown]
    B --> C[Stop DNS Server]
    C --> D[Close Socket Connections]
    D --> E[Restore Original DNS]
    
    E --> F{Platform Check}
    F -->|Windows| G[netsh set dns source=dhcp]
    F -->|macOS| H[networksetup -setdnsservers auto]
    F -->|Linux| I[restore /etc/resolv.conf backup]
    
    G --> J{Restoration Success?}
    H --> J
    I --> J
    
    J -->|Yes| K[Notify: DNS Restored]
    J -->|No| L[Retry Restoration]
    
    L --> M{Retry Count < 3?}
    M -->|Yes| E
    M -->|No| N[Alert: Manual Intervention Required]
    
    K --> O[Service Stopped Successfully]
    N --> P[Log Error & Exit]
    
    style O fill:#90EE90
    style P fill:#FFB6C1
```

### 3.8 Advanced Cache Management

```mermaid
graph TB
    subgraph "Cache Operations"
        A[DNS Cache<br/>Max: 1000 entries<br/>TTL: 5 minutes]
        B[Thread-Safe Access<br/>Mutex Locks]
        C[FIFO Eviction<br/>Memory Management]
    end
    
    subgraph "Cache Warming"
        D[Popular Domains<br/>Pre-loading]
        E[Background Refresh<br/>Before Expiry]
        F[Predictive Caching<br/>Usage Patterns]
    end
    
    subgraph "Hit/Miss Analytics"
        G[Hit Rate Tracking]
        H[Miss Pattern Analysis]
        I[Performance Metrics]
        J[Cache Optimization]
    end
    
    subgraph "Space Management"
        K[Memory Monitoring]
        L[Size Limits]
        M[Cleanup Triggers]
        N[Compression Options]
    end
    
    A --> B
    A --> C
    A --> D
    D --> E
    E --> F
    
    A --> G
    G --> H
    H --> I
    I --> J
    
    A --> K
    K --> L
    L --> M
    M --> N
    
    style A fill:#98FB98
    style G fill:#87CEEB
    style K fill:#DDA0DD
```

### 3.9 Docker Deployment (Future)

```mermaid
graph TB
    subgraph "Docker Architecture"
        A[Dockerfile<br/>Python 3.9 Alpine]
        B[Multi-stage Build<br/>Optimize Size]
        C[Health Checks<br/>Container Monitoring]
    end
    
    subgraph "Container Features"
        D[Privileged Mode<br/>Port 53 Access]
        E[Volume Mounts<br/>Config & Logs]
        F[Environment Variables<br/>API Keys]
    end
    
    subgraph "Orchestration"
        G[Docker Compose<br/>Service Definition]
        H[Kubernetes<br/>Deployment YAML]
        I[Auto-restart Policy<br/>Always]
    end
    
    A --> D
    B --> E
    C --> F
    
    D --> G
    E --> H
    F --> I
    
    style A fill:#87CEEB
    style G fill:#98FB98
    style H fill:#DDA0DD
```

### 3.10 External Logging

```mermaid
flowchart LR
    A[DNY Service] --> B[Internal Logger]
    B --> C{Log Level}
    
    C -->|DEBUG| D[Debug.log]
    C -->|INFO| E[Info.log]
    C -->|WARNING| F[Warning.log]
    C -->|ERROR| G[Error.log]
    
    D --> H[Local File System]
    E --> H
    F --> H
    G --> H
    
    H --> I[Log Rotation<br/>Daily/Size-based]
    I --> J[Compressed Archives<br/>7-day retention]
    
    B --> K[External Syslog<br/>Optional]
    K --> L[Remote Log Server]
    K --> M[SIEM Integration]
    
    B --> N[Structured Logging<br/>JSON Format]
    N --> O[ELK Stack<br/>Elasticsearch]
    N --> P[Monitoring Tools<br/>Grafana]
    
    style B fill:#98FB98
    style H fill:#87CEEB
    style L fill:#DDA0DD
```

### 3.11 Disruption Handling & Recovery

```mermaid
sequenceDiagram
    participant S as DNY Service
    participant M as Monitor
    participant R as Recovery
    participant N as Notifier
    participant U as User
    
    S->>M: Regular Health Ping
    
    Note over S: Network Disruption Occurs
    
    M->>M: Detect Service Failure
    M->>R: Trigger Recovery Process
    
    R->>R: Analyze Failure Type
    
    alt Network Interface Down
        R->>R: Wait for Interface Recovery
        R->>S: Restart Service
    else DNS Port Conflict
        R->>R: Kill Conflicting Process
        R->>S: Rebind Port 53
    else System DNS Corruption
        R->>R: Restore DNS Backup
        R->>S: Reconfigure Service
    end
    
    R->>N: Recovery Status
    N->>U: "Service Restored"
    
    S->>M: Resume Health Pings
    
    Note over R: Recovery Strategies:<br/>• Automatic restart<br/>• Port conflict resolution<br/>• DNS configuration repair<br/>• Network interface recovery
```

---

## 4. KEY METRICS & PERFORMANCE

### Performance Indicators
- **DNS Resolution Time**: < 50ms average
- **Cache Hit Rate**: > 80% target
- **Service Uptime**: 99.9% availability
- **Memory Usage**: < 100MB footprint
- **Thread Pool**: 10 concurrent connections
- **Error Rate**: < 0.1% failed requests

### Robustness Features
- **Multi-platform Support**: Windows, macOS, Linux
- **Automatic Failover**: 3-tier DNS fallback
- **Self-healing**: Automatic service recovery
- **Comprehensive Testing**: 2,500+ lines of tests
- **Graceful Degradation**: Service continues with reduced features
- **Resource Management**: Automatic cleanup and optimization

---

*This presentation covers the complete DNY system architecture with emphasis on robustness, reliability, and cross-platform compatibility.* 