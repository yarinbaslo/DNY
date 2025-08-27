import mysql.connector
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
import platform
import getpass
import socket
import requests

class DatabaseManager:
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        """
        Initialize database connection with the provided credentials
        
        Args:
            host: Database hostname
            port: Database port
            database: Database name
            user: Database username
            password: Database password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.lock = threading.Lock()
        self.current_user_id = None
        self.current_connection_id = None
        self._initialize_connection()
        self._initialize_user_session()
    
    def _initialize_connection(self):
        """Initialize persistent database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True,
                charset='utf8mb4',
                use_unicode=True,
                connection_timeout=10
            )
            logging.info("Database connection established successfully")
            
        except mysql.connector.Error as err:
            logging.error(f"Database connection failed: {err}")
            self.connection = None
    
    def _ensure_connection(self):
        """Ensure database connection is active, reconnect if necessary"""
        with self.lock:
            try:
                if not self.connection or not self.connection.is_connected():
                    logging.info("Reconnecting to database...")
                    self._initialize_connection()
                return self.connection
            except Exception as e:
                logging.error(f"Failed to ensure database connection: {e}")
                return None
    
    def _get_location_info(self):
        """Get user's location information"""
        try:
            # Get public IP and location info
            response = requests.get('http://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip_address': data.get('ip', 'unknown'),
                    'region': data.get('region', 'unknown'),
                    'country': data.get('country_name', 'unknown'),
                    'isp': data.get('org', 'unknown')
                }
        except Exception as e:
            logging.warning(f"Could not get location info: {e}")
        
        # Fallback to local IP
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            return {
                'ip_address': local_ip,
                'region': 'unknown',
                'country': 'unknown',
                'isp': 'unknown'
            }
        except:
            return {
                'ip_address': 'unknown',
                'region': 'unknown',
                'country': 'unknown',
                'isp': 'unknown'
            }
    
    def _initialize_user_session(self):
        """Initialize user session - create user and connection records"""
        connection = self._ensure_connection()
        if not connection:
            return
        
        try:
            # Get system information
            os_type = platform.system()
            username = getpass.getuser()
            
            # Check if user exists
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE os_type = %s AND username = %s",
                (os_type, username)
            )
            user_result = cursor.fetchone()
            
            if user_result:
                self.current_user_id = user_result[0]
                logging.info(f"Found existing user ID: {self.current_user_id}")
            else:
                # Create new user
                cursor.execute(
                    "INSERT INTO users (os_type, username) VALUES (%s, %s)",
                    (os_type, username)
                )
                self.current_user_id = cursor.lastrowid
                logging.info(f"Created new user ID: {self.current_user_id}")
            
            # Create connection record
            location_info = self._get_location_info()
            cursor.execute("""
                INSERT INTO user_connections (user_id, region, country, ip_address, ISP) 
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.current_user_id,
                location_info['region'],
                location_info['country'],
                location_info['ip_address'],
                location_info['isp']
            ))
            
            self.current_connection_id = cursor.lastrowid
            logging.info(f"Created connection ID: {self.current_connection_id}")
            
            cursor.close()
            
        except mysql.connector.Error as err:
            logging.error(f"Error initializing user session: {err}")
    
    def get_or_create_domain(self, domain_name: str, category: str = None, is_unethical: bool = False) -> Optional[int]:
        """Get domain ID or create new domain record"""
        connection = self._ensure_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            
            # Check if domain exists
            cursor.execute("SELECT id FROM domains WHERE domain = %s", (domain_name,))
            result = cursor.fetchone()
            
            if result:
                domain_id = result[0]
                logging.debug(f"Found existing domain ID {domain_id} for {domain_name}")
            else:
                # Create new domain
                cursor.execute(
                    "INSERT INTO domains (domain, category, is_unethical) VALUES (%s, %s, %s)",
                    (domain_name, category, is_unethical)
                )
                domain_id = cursor.lastrowid
                logging.debug(f"Created new domain ID {domain_id} for {domain_name}")
            
            cursor.close()
            return domain_id
            
        except mysql.connector.Error as err:
            logging.error(f"Error getting/creating domain: {err}")
            return None
    
    def dns_query(self, domain_name: str, dns_server_ip: str, cache_hit: bool, 
                     is_blocked: bool = False):
        """
        Log a DNS query to the database
        
        Args:
            domain_name: The domain being queried
            dns_server_ip: IP of the DNS server that responded
            cache_hit: Whether this was a cache hit
            is_blocked: Whether the query was blocked
        """
        if not self.current_connection_id:
            logging.warning("No active connection session - cannot log DNS query")
            return
        
        connection = self._ensure_connection()
        if not connection:
            return
        
        try:
            # Get or create domain
            domain_id = self.get_or_create_domain(domain_name)
            if not domain_id:
                logging.error(f"Could not get domain ID for {domain_name}")
                return
            
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO user_query 
                (dns_server_ip, cache_hit, domain, connection_id, is_blocked)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                dns_server_ip,
                cache_hit,
                domain_id,
                self.current_connection_id,
                is_blocked
            ))
            
            logging.debug(f"Logged DNS query for domain: {domain_name}")
            cursor.close()
            
        except mysql.connector.Error as err:
            logging.error(f"Error logging DNS query: {err}")
    
    def end_user_session(self):
        """End the current user session"""
        if not self.current_connection_id:
            return
        
        connection = self._ensure_connection()
        if not connection:
            return
        
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE user_connections SET end_time = NOW() WHERE id = %s",
                (self.current_connection_id,)
            )
            logging.info(f"Ended user session for connection ID: {self.current_connection_id}")
            cursor.close()
            
        except mysql.connector.Error as err:
            logging.error(f"Error ending user session: {err}")
    
    def close(self):
        """Close database connection"""
        self.end_user_session()
        
        with self.lock:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None
                logging.info("Database connection closed")