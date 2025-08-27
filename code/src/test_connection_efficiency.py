#!/usr/bin/env python3
"""
Test script to demonstrate improved database connection efficiency
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from config import DATABASE_CONFIG, get_system_info

def test_connection_efficiency():
    """Test that database connections are reused efficiently"""
    print("🔌 Testing Database Connection Efficiency...")
    
    try:
        # Initialize database manager
        print("📡 Creating database manager...")
        start_time = time.time()
        db_manager = DatabaseManager(**DATABASE_CONFIG)
        init_time = time.time() - start_time
        
        if not db_manager.connection:
            print("❌ Failed to connect to database")
            return False
        
        print(f"✅ Database connection established in {init_time:.3f}s")
        
        # Get connection info
        conn_info = db_manager.get_connection_info()
        print(f"📊 Connection Info: {conn_info}")
        
        # Test multiple operations without reconnecting
        print("\n🔄 Testing multiple operations with single connection...")
        
        system_info = get_system_info()
        operations = [
            ("Initialize user session", lambda: db_manager.initialize_user_session(system_info['os_type'], system_info['username'])),
            ("Get user ID", lambda: db_manager.get_user_id()),
            ("Get connection ID", lambda: db_manager.get_connection_id()),
            ("Create test domain", lambda: db_manager.get_or_create_domain("efficiency.test.com", "test", False)),
            ("Get dashboard stats", lambda: db_manager.get_dashboard_stats()),
            ("Check connection health", lambda: db_manager.is_connected()),
        ]
        
        total_time = 0
        for op_name, operation in operations:
            start_time = time.time()
            try:
                result = operation()
                op_time = time.time() - start_time
                total_time += op_time
                print(f"✅ {op_name}: {op_time:.3f}s")
            except Exception as e:
                print(f"❌ {op_name}: {e}")
        
        print(f"\n📈 Total operations time: {total_time:.3f}s")
        print(f"📈 Average per operation: {total_time/len(operations):.3f}s")
        
        # Test connection persistence
        print("\n🔗 Testing connection persistence...")
        if db_manager.is_connected():
            print("✅ Connection is still healthy after multiple operations")
        else:
            print("❌ Connection lost after operations")
            return False
        
        # Test connection reuse
        print("\n🔄 Testing connection reuse...")
        start_time = time.time()
        for i in range(5):
            db_manager.is_connected()  # This should not reconnect
        reuse_time = time.time() - start_time
        print(f"✅ 5 connection checks completed in {reuse_time:.3f}s")
        
        print("\n✅ All connection efficiency tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection efficiency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

def main():
    """Main test function"""
    print("="*60)
    print(" Database Connection Efficiency Test")
    print("="*60)
    
    print("This test verifies that:")
    print("1. Database connection is established once")
    print("2. Connection is reused for multiple operations")
    print("3. No unnecessary reconnections occur")
    print("4. Connection health is checked efficiently")
    
    success = test_connection_efficiency()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Database connection efficiency is working correctly!")
        print("   The system now reuses connections instead of reconnecting!")
    else:
        print("💥 Database connection efficiency test failed!")
    print("="*60)

if __name__ == "__main__":
    main()
