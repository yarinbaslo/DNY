#!/usr/bin/env python3
"""
Test script to verify database connection and AI integration
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database_manager import DatabaseManager
from config import Config

def test_database_connection():
    """Test the database connection and AI integration"""
    try:
        # Get database configuration
        db_config = Config.get_database_config()
        print(f"Attempting to connect to database:")
        print(f"  Host: {db_config['host']}")
        print(f"  Port: {db_config['port']}")
        print(f"  Database: {db_config['database']}")
        print(f"  User: {db_config['user']}")
        
        # Create database manager
        db_manager = DatabaseManager(**db_config)
        
        # Test persistent connection
        if db_manager.connection and db_manager.connection.is_connected():
            print("✅ Database connection successful!")
            print(f"✅ User ID: {db_manager.current_user_id}")
            print(f"✅ Connection ID: {db_manager.current_connection_id}")
            
            # Test a simple query
            cursor = db_manager.connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Database version: {version[0]}")
            cursor.close()
            
            # Test domain creation
            domain_id = db_manager.get_or_create_domain("test.example.com", "test")
            print(f"✅ Created/found domain ID: {domain_id}")
            
            # Test DNS query logging
            db_manager.dns_query(
                domain_name="test.example.com",
                dns_server_ip="8.8.8.8",
                cache_hit=False,
                response_time_ms=50,
                is_blocked=False
            )
            print("✅ Logged test DNS query")
            
            # Test AI content checking domain creation
            ai_domain_id = db_manager.get_or_create_domain(
                domain_name="suspicious.example.com",
                category="ai_analysis_high",
                is_unethical=True
            )
            print(f"✅ Created AI-analyzed domain ID: {ai_domain_id}")
            
            # Close connection
            db_manager.close()
            print("✅ Connection closed successfully")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database connection: {e}")
        return False

if __name__ == "__main__":
    print("Testing Database Connection and AI Integration...")
    success = test_database_connection()
    
    if success:
        print("\n🎉 Database connection test passed!")
        print("\n📊 What gets logged to your database:")
        print("  • User sessions (OS, username, location)")
        print("  • DNS queries (domain, server, response time, cache hits)")
        print("  • AI content analysis (when OpenAI API is used)")
        print("  • Domain categorization (risk levels, ethics flags)")
        print("  • Blocked domains and reasons")
        sys.exit(0)
    else:
        print("\n💥 Database connection test failed!")
        sys.exit(1)
