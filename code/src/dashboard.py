#!/usr/bin/env python3
"""
DNS Proxy Dashboard
Displays statistics and analytics from the collected DNS data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from config import DATABASE_CONFIG, get_system_info
import logging

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_stats(stats, user_info=None):
    """Print formatted statistics"""
    if user_info:
        print(f"\n📊 Statistics for User: {user_info['username']} ({user_info['os_type']})")
    else:
        print("\n📊 Overall System Statistics")
    
    print(f"🌐 Total Domains Accessed: {stats.get('total_domains', 0):,}")
    print(f"🔍 Total DNS Queries: {stats.get('total_queries', 0):,}")
    print(f"⚡ Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1f}%")
    print(f"🚫 Blocked Queries: {stats.get('blocked_queries', 0):,}")
    
    # Top domains
    top_domains = stats.get('top_domains', [])
    if top_domains:
        print("\n🏆 Top 10 Most Accessed Domains:")
        for i, domain_info in enumerate(top_domains, 1):
            print(f"  {i:2d}. {domain_info['domain']:<30} ({domain_info['count']:>5} queries)")

def print_user_connections(db_manager, user_id):
    """Print user connection history"""
    if not user_id:
        return
    
    print_header("User Connection History")
    
    try:
        cursor = db_manager.connection.cursor()
        cursor.execute("""
            SELECT city, country, ip_address, ISP, start_time, end_time
            FROM user_connections 
            WHERE user_id = %s 
            ORDER BY start_time DESC 
            LIMIT 10
        """, (user_id,))
        
        connections = cursor.fetchall()
        if connections:
            print(f"{'City':<15} {'Country':<15} {'IP Address':<15} {'ISP':<20} {'Start Time':<20} {'End Time':<20}")
            print("-" * 100)
            for conn in connections:
                city, country, ip, isp, start_time, end_time = conn
                end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'Active'
                print(f"{city or 'Unknown':<15} {country or 'Unknown':<15} {ip or 'Unknown':<15} "
                      f"{isp or 'Unknown':<20} {start_time.strftime('%Y-%m-%d %H:%M:%S'):<20} {end_time_str:<20}")
        else:
            print("No connection history found.")
        
        cursor.close()
    except Exception as e:
        print(f"Error fetching connection history: {e}")

def print_recent_queries(db_manager, user_id, limit=20):
    """Print recent DNS queries"""
    if not user_id:
        return
    
    print_header("Recent DNS Queries")
    
    try:
        cursor = db_manager.connection.cursor()
        cursor.execute("""
            SELECT d.domain, uq.dns_server_ip, uq.cache_hit, uq.query_response_time, 
                   uq.is_blocked, uq.timestamp
            FROM user_query uq
            JOIN domains d ON uq.domain_id = d.id
            JOIN user_connections uc ON uq.connection_id = uc.id
            WHERE uc.user_id = %s
            ORDER BY uq.timestamp DESC
            LIMIT %s
        """, (user_id, limit))
        
        queries = cursor.fetchall()
        if queries:
            print(f"{'Domain':<30} {'DNS Server':<15} {'Cache':<6} {'Time(ms)':<8} {'Blocked':<8} {'Timestamp':<20}")
            print("-" * 100)
            for query in queries:
                domain, dns_server, cache_hit, response_time, is_blocked, timestamp = query
                cache_str = "HIT" if cache_hit else "MISS"
                blocked_str = "YES" if is_blocked else "NO"
                time_str = f"{response_time}" if response_time else "N/A"
                print(f"{domain:<30} {dns_server:<15} {cache_str:<6} {time_str:<8} {blocked_str:<8} "
                      f"{timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20}")
        else:
            print("No query history found.")
        
        cursor.close()
    except Exception as e:
        print(f"Error fetching query history: {e}")

def main():
    """Main dashboard function"""
    print_header("DNS Proxy Dashboard")
    
    # Initialize database connection
    try:
        db_manager = DatabaseManager(**DATABASE_CONFIG)
        if not db_manager.connection:
            print("❌ Failed to connect to database. Please check your configuration.")
            return
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return
    
    try:
        # Get system information
        system_info = get_system_info()
        print(f"💻 System: {system_info['os_type']}")
        print(f"👤 User: {system_info['username']}")
        print(f"🖥️  Hostname: {system_info['hostname']}")
        
        # Get or create user
        user_id = db_manager.get_or_create_user(system_info['os_type'], system_info['username'])
        if not user_id:
            print("❌ Failed to create/get user from database")
            return
        
        # Get statistics
        print_header("Statistics")
        stats = db_manager.get_dashboard_stats(user_id)
        print_stats(stats, system_info)
        
        # Get overall system statistics
        overall_stats = db_manager.get_dashboard_stats()
        print_stats(overall_stats)
        
        # Show user connection history
        print_user_connections(db_manager, user_id)
        
        # Show recent queries
        print_recent_queries(db_manager, user_id)
        
        print_header("Dashboard Complete")
        
    except Exception as e:
        print(f"❌ Error in dashboard: {e}")
        logging.error(f"Dashboard error: {e}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
