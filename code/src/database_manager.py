import pymysql
import logging
import socket
import requests
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading

class DatabaseManager:
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.lock = threading.Lock()
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True,
                charset='utf8mb4'
            )
            logging.info(f"Successfully connected to database {self.database} on {self.host}:{self.port}")
        except pymysql.Error as err:
            logging.error(f"Failed to connect to database: {err}")
            self.connection = None





    def _ensure_connection(self):
        """Ensure database connection is active, reconnect only if necessary"""
        if not self.connection:
            logging.info("No database connection, connecting...")
            self._connect()
            return
        
        # Only check connection health if we're about to use it
        try:
            # Simple ping to check if connection is alive
            self.connection.ping(reconnect=False)
        except Exception:
            logging.info("Database connection lost, reconnecting...")
            self._connect()

    def is_connected(self) -> bool:
        """Check if database connection is healthy"""
        if not self.connection:
            return False
        
        try:
            self.connection.ping(reconnect=False)
            return True
        except Exception:
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging"""
        if not self.connection:
            return {"status": "disconnected"}
        
        try:
            return {
                "status": "connected",
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "user": self.user,
                "connection_id": getattr(self.connection, '_connection_id', 'unknown')
            }
        except Exception:
            return {"status": "error"}

    def get_or_create_user(self, os_type: str, username: str) -> Optional[int]:
        """Get existing user or create new one, returns user ID"""
        if not self.connection:
            return None

        cursor = self.connection.cursor()
        try:
            # Try to find existing user
            cursor.execute(
                "SELECT id FROM users WHERE os_type = %s AND username = %s",
                (os_type, username)
            )
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create new user
                cursor.execute(
                    "INSERT INTO users (os_type, username) VALUES (%s, %s)",
                    (os_type, username)
                )
                return cursor.lastrowid
        except pymysql.Error as err:
            logging.error(f"Error in get_or_create_user: {err}")
            return None
        finally:
            cursor.close()

    def get_or_create_domain(self, domain: str, category: str = None, is_unethical: bool = False) -> Optional[int]:
        """Get existing domain or create new one, returns domain ID"""
        if not self.connection:
            return None

        cursor = self.connection.cursor()
        try:
            # Try to find existing domain
            cursor.execute("SELECT id FROM domains WHERE domain = %s", (domain,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create new domain
                cursor.execute(
                    "INSERT INTO domains (domain, category, is_unethical) VALUES (%s, %s, %s)",
                    (domain, category, is_unethical)
                )
                return cursor.lastrowid
        except pymysql.Error as err:
            logging.error(f"Error in get_or_create_domain: {err}")
            return None
        finally:
            cursor.close()

    def create_user_connection(self, user_id: int, city: str = None, country: str = None, 
                             ip_address: str = None, isp: str = None) -> Optional[int]:
        """Create a new user connection record, returns connection ID"""
        if not self.connection:
            return None

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO user_connections 
                   (user_id, city, country, ip_address, ISP) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, city, country, ip_address, isp)
            )
            return cursor.lastrowid
        except pymysql.Error as err:
            logging.error(f"Error creating user connection: {err}")
            return None
        finally:
            cursor.close()

    def end_user_connection(self, connection_id: int):
        """Mark a user connection as ended"""
        if not self.connection:
            return

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "UPDATE user_connections SET end_time = CURRENT_TIMESTAMP WHERE id = %s",
                (connection_id,)
            )
        except pymysql.Error as err:
            logging.error(f"Error ending user connection: {err}")
        finally:
            cursor.close()

    def log_dns_query(self, dns_server_ip: str, cache_hit: bool, query_response_time: int,
                     domain_id: int, connection_id: int, is_blocked: bool = False):
        """Log a DNS query to the database"""
        if not self.connection:
            return

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO user_query 
                   (dns_server_ip, cache_hit, query_response_time, domain_id, connection_id, is_blocked) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (dns_server_ip, cache_hit, query_response_time, domain_id, connection_id, is_blocked)
            )
        except pymysql.Error as err:
            logging.error(f"Error logging DNS query: {err}")
        finally:
            cursor.close()

    def get_geolocation_info(self, ip_address: str) -> Dict[str, str]:
        """Get geolocation information for an IP address"""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'city': data.get('city', ''),
                    'country': data.get('country', ''),
                    'isp': data.get('isp', '')
                }
        except Exception as e:
            logging.warning(f"Failed to get geolocation for {ip_address}: {e}")
        
        return {'city': '', 'country': '', 'isp': ''}

    def get_local_ip(self) -> str:
        """Get the router's external IP address (simplified)"""
        try: 



    def get_network_info(self) -> Dict[str, str]:
        """Get comprehensive network information including ISP details"""
        # Get external IP (router's public IP)
        external_ip = self.get_local_ip()
        
        # Get geolocation from external IP
        geo_info = self.get_geolocation_info(external_ip)
        
        network_info = {
            'external_ip': external_ip,
            'isp': geo_info.get('isp', 'Unknown'),
            'city': geo_info.get('city', 'Unknown'),
            'country': geo_info.get('country', 'Unknown')
        }
        
        return network_info

    def get_dashboard_stats(self, user_id: int = None) -> Dict[str, Any]:
        """Get aggregated statistics for dashboard"""
        if not self.connection:
            return {}

        cursor = self.connection.cursor()
        try:
            stats = {}
            
            # Total domains accessed
            if user_id:
                cursor.execute(
                    """SELECT COUNT(DISTINCT d.domain) 
                       FROM user_query uq 
                       JOIN domains d ON uq.domain_id = d.id 
                       JOIN user_connections uc ON uq.connection_id = uc.id 
                       WHERE uc.user_id = %s""", (user_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM domains")
            stats['total_domains'] = cursor.fetchone()[0]

            # Total queries
            if user_id:
                cursor.execute(
                    """SELECT COUNT(*) 
                       FROM user_query uq 
                       JOIN user_connections uc ON uq.connection_id = uc.id 
                       WHERE uc.user_id = %s""", (user_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM user_query")
            stats['total_queries'] = cursor.fetchone()[0]

            # Cache hit rate
            if user_id:
                cursor.execute(
                    """SELECT 
                           COUNT(CASE WHEN cache_hit = TRUE THEN 1 END) as hits,
                           COUNT(*) as total
                       FROM user_query uq 
                       JOIN user_connections uc ON uq.connection_id = uc.id 
                       WHERE uc.user_id = %s""", (user_id,)
                )
            else:
                cursor.execute(
                    """SELECT 
                           COUNT(CASE WHEN cache_hit = TRUE THEN 1 END) as hits,
                           COUNT(*) as total
                       FROM user_query"""
                )
            result = cursor.fetchone()
            if result[1] > 0:
                stats['cache_hit_rate'] = (result[0] / result[1]) * 100
            else:
                stats['cache_hit_rate'] = 0

            # Blocked queries
            if user_id:
                cursor.execute(
                    """SELECT COUNT(*) 
                       FROM user_query uq 
                       JOIN user_connections uc ON uq.connection_id = uc.id 
                       WHERE uq.is_blocked = TRUE AND uc.user_id = %s""", (user_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM user_query WHERE is_blocked = TRUE")
            stats['blocked_queries'] = cursor.fetchone()[0]

            # Top domains
            if user_id:
                cursor.execute(
                    """SELECT d.domain, COUNT(*) as access_count
                       FROM user_query uq 
                       JOIN domains d ON uq.domain_id = d.id 
                       JOIN user_connections uc ON uq.connection_id = uc.id 
                       WHERE uc.user_id = %s 
                       GROUP BY d.domain 
                       ORDER BY access_count DESC 
                       LIMIT 10""", (user_id,)
                )
            else:
                cursor.execute(
                    """SELECT d.domain, COUNT(*) as access_count
                       FROM user_query uq 
                       JOIN domains d ON uq.domain_id = d.id 
                       GROUP BY d.domain 
                       ORDER BY access_count DESC 
                       LIMIT 10"""
                )
            stats['top_domains'] = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]

            return stats

        except pymysql.Error as err:
            logging.error(f"Error getting dashboard stats: {err}")
            return {}
        finally:
            cursor.close()

    def close(self):
        """Close database connection"""
        try:
            if self.connection and self.connection.open:
                self.connection.close()
                logging.info("Database connection closed")
        except Exception as e:
            logging.warning(f"Error closing database connection: {e}")
