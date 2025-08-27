#!/usr/bin/env python3
"""
Test script to demonstrate network detection methods
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from config import DATABASE_CONFIG

def test_network_detection():
    """Test different network detection methods"""
    print("🌐 Testing Network Detection Methods...")
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(**DATABASE_CONFIG)
        
        if not db_manager.connection:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful!")
        
        # Test IP detection method
        print("\n📡 IP Address Detection:")
        print("-" * 50)
        
        # External IP (router's public IP)
        external_ip = db_manager.get_local_ip()
        print(f"🌍 External IP (Router): {external_ip}")
        
        # Geolocation from external IP
        print(f"\n📍 Geolocation from External IP ({external_ip}):")
        geo_info = db_manager.get_geolocation_info(external_ip)
        print(f"   City: {geo_info['city'] or 'Unknown'}")
        print(f"   Country: {geo_info['country'] or 'Unknown'}")
        print(f"   ISP: {geo_info['isp'] or 'Unknown'}")
        
        # Comprehensive network info
        print(f"\n🌐 Comprehensive Network Information:")
        print("-" * 50)
        network_info = db_manager.get_network_info()
        for key, value in network_info.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Network detection test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Network detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

def main():
    """Main test function"""
    print("="*60)
    print(" Network Detection Test")
    print("="*60)
    
    print("This test shows:")
    print("1. Your router's external IP address")
    print("2. Geolocation data (city, country, ISP)")
    print("3. Network information for database logging")
    
    success = test_network_detection()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Network detection is working!")
        print("   You can now see your router's external IP and geolocation data")
    else:
        print("💥 Network detection test failed!")
    print("="*60)

if __name__ == "__main__":
    main()
