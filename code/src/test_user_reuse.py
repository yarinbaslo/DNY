#!/usr/bin/env python3
"""
Test script to demonstrate user session reuse
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from config import DATABASE_CONFIG, get_system_info

def test_user_reuse():
    """Test that user session is created once and reused"""
    print("🔄 Testing User Session Reuse...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(**DATABASE_CONFIG)
        
        if not db_manager.connection:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful!")
        
        # Get system information
        system_info = get_system_info()
        print(f"👤 Testing for user: {system_info['username']} ({system_info['os_type']})")
        
        # First user creation
        print("\n🔄 First user creation...")
        user_id_1 = db_manager.get_or_create_user(system_info['os_type'], system_info['username'])
        if user_id_1:
            print(f"✅ First user - User ID: {user_id_1}")
        else:
            print("❌ First user creation failed")
            return False
        
        # Second user creation (should reuse existing user)
        print("\n🔄 Second user creation (should reuse)...")
        user_id_2 = db_manager.get_or_create_user(system_info['os_type'], system_info['username'])
        if user_id_2:
            print(f"✅ Second user - User ID: {user_id_2}")
        else:
            print("❌ Second user creation failed")
            return False
        
        # Verify user IDs are the same
        if user_id_1 == user_id_2:
            print("✅ User reused successfully - IDs are identical")
        else:
            print("❌ User not reused - IDs are different")
            return False
        
        # Create connection for testing
        connection_id = db_manager.create_user_connection(
            user_id_1, "Test City", "Test Country", "192.168.1.1", "Test ISP"
        )
        if connection_id:
            print(f"✅ Connection created: {connection_id}")
        else:
            print("❌ Failed to create connection")
            return False
        
        # Test multiple operations using the same session
        print("\n🔄 Testing multiple operations with same session...")
        
        # Create a test domain
        domain_id = db_manager.get_or_create_domain("reuse.test.com", "test", False)
        if domain_id:
            print(f"✅ Domain created: {domain_id}")
        else:
            print("❌ Failed to create domain")
            return False
        
        # Log multiple queries using the same connection
        for i in range(3):
            db_manager.log_dns_query("8.8.8.8", False, 100 + i, domain_id, connection_id, False)
            print(f"✅ Query {i+1} logged")
        
        # Get stats to verify data is being collected
        stats = db_manager.get_dashboard_stats(user_id_1)
        if stats:
            print(f"✅ Stats retrieved: {stats.get('total_queries', 0)} total queries")
        
        print("\n✅ All user reuse tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ User reuse test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

def main():
    """Main test function"""
    print("="*60)
    print(" User Session Reuse Test")
    print("="*60)
    
    print("This test verifies that:")
    print("1. User is created only once")
    print("2. Subsequent calls reuse the same user")
    print("3. Multiple operations work with the same user")
    print("4. No duplicate users are created")
    
    success = test_user_reuse()
    
    print("\n" + "="*60)
    if success:
        print("🎉 User reuse is working correctly!")
        print("   The system now creates users once and reuses them!")
    else:
        print("💥 User reuse test failed!")
    print("="*60)

if __name__ == "__main__":
    main()
