# Database Integration Guide

This document explains how to use the new database integration features in the DNS Proxy application.

## Overview

The DNS Proxy now automatically logs all DNS queries, user connections, and domain access patterns to a MySQL database. This provides comprehensive analytics and monitoring capabilities.

## Database Schema

The application creates and manages the following tables:

### 1. Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    os_type VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
- Tracks each user who uses the DNS proxy
- Automatically created based on system information

### 2. Domains Table
```sql
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    is_unethical BOOLEAN DEFAULT FALSE
);
```
- Stores all domains accessed through the proxy
- Tracks domain categorization and ethical status

### 3. User Connections Table
```sql
CREATE TABLE user_connections (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    city VARCHAR(100),
    country VARCHAR(100),
    ip_address VARCHAR(50),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    ISP VARCHAR(100)
);
```
- Records each time a user connects to a new network
- Automatically detects location and ISP information

### 4. User Query Table
```sql
CREATE TABLE user_query (
    id SERIAL PRIMARY KEY,
    dns_server_ip VARCHAR(50) NOT NULL,
    cache_hit BOOLEAN,
    query_response_time INT,
    domain INT REFERENCES domains(id),
    connection_id INT REFERENCES user_connections(id),
    is_blocked BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
- Logs every DNS query made by users
- Tracks performance metrics and blocking status

## Configuration

### Database Settings
The database connection is configured in `src/config.py`:

```python
DATABASE_CONFIG = {
    'host': 'user-data-db.cx6uo4aykhw3.eu-north-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'user_stats_db',
    'user': 'admin',
    'password': 'ADMINdny'
}
```

### Environment Variables
You can override database settings using environment variables:

```bash
export DNY_DB_HOST="your-db-host"
export DNY_DB_PORT="3306"
export DNY_DB_NAME="your-db-name"
export DNY_DB_USER="your-username"
export DNY_DB_PASSWORD="your-password"
```

## Features

### User Session Management
The system now uses a more efficient approach to user management:

- **Single Initialization**: User and connection records are created only once when the application starts
- **Session Reuse**: Subsequent operations reuse the same user ID and connection ID
- **No Duplicates**: Prevents creation of multiple user records for the same system
- **Efficient Logging**: All DNS queries are logged using the established session

### Connection Management
The database connection is now managed efficiently:

- **Single Connection**: Database connection established once during initialization
- **Connection Reuse**: All operations use the same connection without reconnecting
- **Smart Health Checks**: Connection health verified only when necessary
- **Automatic Recovery**: Reconnection only occurs when connection is actually lost
- **Performance Monitoring**: Connection status and performance metrics available

### Automatic Data Collection
- **User Session Management**: Creates user records once and reuses them throughout the session
- **Connection Monitoring**: Tracks network changes and location information
- **Query Logging**: Records every DNS query with performance metrics
- **Domain Analysis**: Builds a comprehensive database of accessed domains

### Performance Metrics
- **Response Times**: Measures DNS resolution performance
- **Cache Efficiency**: Tracks cache hit/miss rates
- **Server Performance**: Monitors primary vs. fallback DNS server usage
- **Blocking Statistics**: Counts blocked queries and domains

### Geolocation Features
- **IP Detection**: Automatically detects local IP addresses
- **Location Services**: Uses ip-api.com for city/country/ISP information
- **Network Tracking**: Monitors network changes and connection history

## Usage

### Starting the Service
The database integration is automatic when you start the DNS proxy:

```bash
cd code/src
python main.py
```

The system will:
1. Connect to the database
2. Create necessary tables
3. Initialize user session (creates user and connection once)
4. Start monitoring the current network connection
5. Log all DNS queries automatically using the established session

### Viewing Statistics
Use the dashboard to view collected data:

```bash
cd code/src
python dashboard.py
```

The dashboard shows:
- User-specific statistics
- Overall system metrics
- Connection history
- Recent DNS queries
- Top accessed domains

### Testing Database Connection
Test the database setup:

```bash
cd code/src
python test_db_connection.py
```

This script verifies:
- Database connectivity
- Table creation
- Basic operations
- Data insertion and retrieval

### Testing Connection Efficiency
Test the improved connection management:

```bash
cd code/src
python3 test_connection_efficiency.py
```

This script verifies:
- Single connection establishment
- Connection reuse across operations
- No unnecessary reconnections
- Performance improvements

## Data Analysis Examples

### User Activity Patterns
```sql
-- Get user's daily DNS query patterns
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as queries,
    AVG(query_response_time) as avg_response_time
FROM user_query uq
JOIN user_connections uc ON uq.connection_id = uc.id
WHERE uc.user_id = 1
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

### Domain Access Analysis
```sql
-- Find most accessed domains by user
SELECT 
    d.domain,
    COUNT(*) as access_count,
    AVG(uq.query_response_time) as avg_response_time
FROM user_query uq
JOIN domains d ON uq.domain = d.id
JOIN user_connections uc ON uq.connection_id = uc.id
WHERE uc.user_id = 1
GROUP BY d.domain
ORDER BY access_count DESC
LIMIT 20;
```

### Network Performance
```sql
-- Compare DNS server performance
SELECT 
    dns_server_ip,
    COUNT(*) as queries,
    AVG(query_response_time) as avg_response_time,
    COUNT(CASE WHEN cache_hit = TRUE THEN 1 END) as cache_hits
FROM user_query
GROUP BY dns_server_ip
ORDER BY avg_response_time;
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify database credentials in `config.py`
   - Check network connectivity to database host
   - Ensure database server is running

2. **Permission Errors**
   - Verify database user has CREATE, INSERT, SELECT permissions
   - Check if database exists and is accessible

3. **Table Creation Issues**
   - Ensure MySQL version supports all data types
   - Check for conflicting table names

### Debug Mode
Enable detailed logging by setting log level to DEBUG in `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Security Considerations

- Database credentials are stored in plain text in `config.py`
- Consider using environment variables for production deployments
- The application only connects to the specified database
- No sensitive DNS query content is stored, only metadata

## Performance Impact

- Minimal overhead: ~1-2ms per query for database logging
- **Single connection establishment**: Database connection created once and reused
- **Efficient connection management**: No unnecessary reconnections
- **Connection health monitoring**: Smart health checks only when needed
- Asynchronous logging to prevent blocking DNS resolution
- Efficient indexing on frequently queried fields

## Future Enhancements

- Real-time dashboard with web interface
- Advanced analytics and reporting
- Machine learning for domain categorization
- Integration with external threat intelligence feeds
- Automated blocking based on historical patterns
