import os
from typing import Dict, Any

class Config:
    """Configuration class for DNS Proxy Service"""
    
    # Database configuration
    DATABASE_CONFIG = {
        'host': 'user-data-db.cx6uo4aykhw3.eu-north-1.rds.amazonaws.com',
        'port': 3306,
        'database': 'user_stats_db',
        'user': 'admin',
        'password': 'ADMINdny'
    }
    
    # DNS configuration
    DNS_CONFIG = {
        'local_port': 53,
        'listen_port': 53,
        'timeout': 5,  # seconds
        'max_cache_size': 1000,
        'cache_ttl': 300  # seconds
    }
    
    # Content checking configuration
    CONTENT_CHECK_CONFIG = {
        'api_key': os.getenv('OPENAI_API_KEY', ''),  # Get from environment variable
        'enabled': True,
        'timeout': 10  # seconds
    }
    
    # Default DNS servers (fallback when database is unavailable)
    DEFAULT_DNS_CONFIG = {
        'servers': [
            {'ip': '8.8.8.8', 'port': 53, 'name': 'Google Primary'},
            {'ip': '8.8.4.4', 'port': 53, 'name': 'Google Secondary'},
            {'ip': '1.1.1.1', 'port': 53, 'name': 'Cloudflare Primary'},
            {'ip': '1.0.0.1', 'port': 53, 'name': 'Cloudflare Secondary'},
        ]
    }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration"""
        return cls.DATABASE_CONFIG.copy()
    
    @classmethod
    def get_dns_config(cls) -> Dict[str, Any]:
        """Get DNS configuration"""
        return cls.DNS_CONFIG.copy()
    
    @classmethod
    def get_content_check_config(cls) -> Dict[str, Any]:
        """Get content checking configuration"""
        return cls.CONTENT_CHECK_CONFIG.copy()
    
    @classmethod
    def get_default_dns_config(cls) -> Dict[str, Any]:
        """Get default DNS servers configuration"""
        return cls.DEFAULT_DNS_CONFIG.copy()
    
    @classmethod
    def update_database_config(cls, **kwargs):
        """Update database configuration with new values"""
        cls.DATABASE_CONFIG.update(kwargs)
    
    @classmethod
    def update_dns_config(cls, **kwargs):
        """Update DNS configuration with new values"""
        cls.DNS_CONFIG.update(kwargs)
    
    @classmethod
    def update_content_check_config(cls, **kwargs):
        """Update content checking configuration with new values"""
        cls.CONTENT_CHECK_CONFIG.update(kwargs)
    
    @classmethod
    def update_default_dns_config(cls, **kwargs):
        """Update default DNS configuration with new values"""
        cls.DEFAULT_DNS_CONFIG.update(kwargs)
