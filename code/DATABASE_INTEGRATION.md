# Database Integration for DNS Proxy Service

This document explains how the DNS Proxy Service integrates with your MySQL database to collect and store DNS query data.

## Database Configuration

The service is configured to connect to your MySQL database with the following settings:

- **Host**: `user-data-db.cx6uo4aykhw3.eu-north-1.rds.amazonaws.com`
- **Port**: `3306`
- **Database**: `user_stats_db`
- **User**: `admin`
- **Password**: `ADMINdny`

## What Data is Collected

The service automatically collects and logs the following information to your database:

### 1. DNS Queries
- Query ID and timestamp
- Domain name being resolved
- Query type (A, AAAA, CNAME, etc.)
- Client IP address
- Response time in milliseconds
- DNS server used (primary or fallback)
- Cache hit/miss status
- Response status (success, timeout, error)

### 2. IP Addresses
- Domain name
- IP address (IPv4 or IPv6)
- Record type
- Whether the IP is blocked
- Block reason (if applicable)

### 3. Content Check Results
- Domain name
- Whether content is appropriate
- Reason for the determination
- API response time

### 4. DNS Server Performance
- DNS server address
- Response time
- Success/failure/timeout counts

### 5. Cache Statistics
- Cache hits and misses
- Cache size
- Cache evictions

## Configuration

The database logging can be controlled through the configuration file `src/config.py`. You can enable/disable specific logging features:

```python
PERFORMANCE_CONFIG = {
    'log_queries': True,           # Log DNS queries
    'log_ip_addresses': True,      # Log IP addresses
    'log_content_checks': True,    # Log content check results
    'log_dns_performance': True,   # Log DNS server performance
    'log_cache_stats': True,       # Log cache statistics
    'stats_interval': 300          # Log stats every 5 minutes
}
```

## Testing the Connection

Before running the main service, you can test the database connection:

```bash
cd code
python test_db_connection.py
```

This will verify that:
1. The database credentials are correct
2. The connection can be established
3. Basic queries can be executed

## Running the Service

Once the database connection is verified, you can run the DNS service normally:

```bash
cd code
python src/main.py
```

The service will automatically:
1. Connect to your database
2. Start collecting DNS data
3. Log all the information to your existing tables

## Database Tables

The service expects your database to have tables that can store the collected data. The exact table structure depends on your existing schema, but the service will attempt to insert data using the following field names:

- `timestamp` - When the event occurred
- `domain_name` - The domain being queried
- `ip_address` - IP address from DNS response
- `query_id` - Unique identifier for each DNS query
- `response_time_ms` - Response time in milliseconds
- `dns_server_used` - Which DNS server responded
- `is_primary_dns` - Whether it was the primary DNS
- `cache_hit` - Whether the response came from cache
- `response_status` - Success, timeout, or error

## Troubleshooting

### Connection Issues
- Verify the database credentials in `src/config.py`
- Ensure the database is accessible from your network
- Check if the MySQL server is running

### Permission Issues
- Ensure the `admin` user has INSERT permissions on your tables
- Check if the database exists and is accessible

### Performance Issues
- The database logging is designed to be non-blocking
- If database operations are slow, the DNS service will continue to function
- All database errors are logged but don't stop the DNS service

## Customization

You can customize what data is logged by modifying the `PERFORMANCE_CONFIG` in `src/config.py`. For example, to only log DNS queries:

```python
PERFORMANCE_CONFIG = {
    'log_queries': True,
    'log_ip_addresses': False,
    'log_content_checks': False,
    'log_dns_performance': False,
    'log_cache_stats': False
}
```

## Security Notes

- Database credentials are stored in plain text in the config file
- Consider using environment variables for production deployments
- The service only connects to the database, it doesn't create or modify table structures
- All database operations use parameterized queries to prevent SQL injection
