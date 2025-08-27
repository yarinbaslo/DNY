import os
import platform
import getpass

# Database Configuration
DATABASE_CONFIG = {
    'host': 'user-data-db.cx6uo4aykhw3.eu-north-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'user_stats_db',
    'user': 'admin',
    'password': 'ADMINdny'
}

# Application Configuration
APP_CONFIG = {
    'cache_ttl': 300,  # 5 minutes
    'cache_max_size': 1000,
    'dns_timeout': 5,  # seconds
    'geolocation_timeout': 5,  # seconds
}

# Get system information
def get_system_info():
    """Get current system information"""
    return {
        'os_type': platform.system(),
        'username': getpass.getuser(),
        'hostname': platform.node()
    }

# Environment-specific overrides
if os.getenv('DNY_DB_HOST'):
    DATABASE_CONFIG['host'] = os.getenv('DNY_DB_HOST')

if os.getenv('DNY_DB_PORT'):
    DATABASE_CONFIG['port'] = int(os.getenv('DNY_DB_PORT'))

if os.getenv('DNY_DB_NAME'):
    DATABASE_CONFIG['database'] = os.getenv('DNY_DB_NAME')

if os.getenv('DNY_DB_USER'):
    DATABASE_CONFIG['user'] = os.getenv('DNY_DB_USER')

if os.getenv('DNY_DB_PASSWORD'):
    DATABASE_CONFIG['password'] = os.getenv('DNY_DB_PASSWORD')
