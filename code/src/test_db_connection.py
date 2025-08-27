#!/usr/bin/env python3
"""
Test script to verify database connection and basic operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from config import DATABASE_CONFIG, get_system_info

def test_database_connection():
    """Test basic database connectivity and operations"""
    print("🔌 Testing Database Connection...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(**DATABASE_CONFIG)
        
        if not db_manager.connection:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful!")
        
        # Test user creation
        system_info = get_system_info()
        print(f"👤 Testing user creation for: {system_info['username']} ({system_info['os_type']})")
        
        user_id = db_manager.get_or_create_user(system_info['os_type'], system_info['username'])
        if user_id:
            print(f"✅ User ID: {user_id}")
        else:
            print("❌ Failed to create/get user")
            return False
        
        # Test domain creation/retrieval
        test_domain = "test.example.com"
        print(f"🌐 Testing domain operations for: {test_domain}")
        
        domain_id = db_manager.get_or_create_domain(test_domain, "test", False)
        if domain_id:
            print(f"✅ Domain ID: {domain_id}")
        else:
            print("❌ Failed to create/get domain")
            return False
        
        # Create test connection
        print("🔗 Creating test connection...")
        connection_id = db_manager.create_user_connection(
            user_id, "Test City", "Test Country", "192.168.1.1", "Test ISP"
        )
        if connection_id:
            print(f"✅ Connection ID: {connection_id}")
        else:
            print("❌ Failed to create connection")
            return False
        
        # Test query logging
        print("📝 Testing query logging...")
        db_manager.log_dns_query("8.8.8.8", False, 150, domain_id, connection_id, False)
        print("✅ Query logged successfully")
        
        # Test dashboard stats
        print("📊 Testing dashboard statistics...")
        stats = db_manager.get_dashboard_stats(user_id)
        if stats:
            print(f"✅ Stats retrieved: {len(stats)} metrics")
            for key, value in stats.items():
                if key != 'top_domains':  # Skip complex objects
                    print(f"   {key}: {value}")
        else:
            print("❌ Failed to get dashboard stats")
        
        # Clean up test data
        print("🧹 Cleaning up test data...")
        db_manager.end_user_connection(connection_id)
        
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

def main():
    """Main test function"""
    print("="*60)
    print(" Database Connection Test")
    print("="*60)
    
    print(f"🔧 Database Config:")
    print(f"   Host: {DATABASE_CONFIG['host']}")
    print(f"   Port: {DATABASE_CONFIG['port']}")
    print(f"   Database: {DATABASE_CONFIG['database']}")
    print(f"   User: {DATABASE_CONFIG['user']}")
    
    success = test_database_connection()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Database integration is working correctly!")
    else:
        print("💥 Database integration test failed!")
    print("="*60)

if __name__ == "__main__":
    main()
