import pytest
import time
import threading
from unittest.mock import patch
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dns_cache import DNSCache


class TestDNSCache:
    """Test cases for DNSCache class."""

    def test_init_default_values(self):
        """Test DNSCache initialization with default values."""
        cache = DNSCache()
        assert cache.max_size == 1000
        assert cache.ttl == 300
        assert cache.cache == {}

    def test_init_custom_values(self):
        """Test DNSCache initialization with custom values."""
        cache = DNSCache(max_size=500, ttl=600)
        assert cache.max_size == 500
        assert cache.ttl == 600
        assert cache.cache == {}

    def test_set_and_get_basic(self):
        """Test basic set and get operations."""
        cache = DNSCache()
        question = b"test_question"
        response = b"test_response"
        
        cache.set(question, response)
        result = cache.get(question)
        
        assert result == response

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = DNSCache()
        result = cache.get(b"nonexistent")
        assert result is None

    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = DNSCache(ttl=1)  # 1 second TTL
        question = b"test_question"
        response = b"test_response"
        
        cache.set(question, response)
        assert cache.get(question) == response
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get(question) is None

    def test_max_size_limit(self):
        """Test that cache respects max_size limit with FIFO eviction."""
        cache = DNSCache(max_size=2)
        
        # Add first entry
        cache.set(b"question1", b"response1")
        assert cache.get(b"question1") == b"response1"
        
        # Add second entry
        cache.set(b"question2", b"response2")
        assert cache.get(b"question1") == b"response1"
        assert cache.get(b"question2") == b"response2"
        
        # Add third entry - should evict first
        cache.set(b"question3", b"response3")
        assert cache.get(b"question1") is None  # Evicted
        assert cache.get(b"question2") == b"response2"
        assert cache.get(b"question3") == b"response3"

    def test_update_existing_entry(self):
        """Test updating an existing cache entry."""
        cache = DNSCache()
        question = b"test_question"
        
        cache.set(question, b"response1")
        assert cache.get(question) == b"response1"
        
        cache.set(question, b"response2")
        assert cache.get(question) == b"response2"

    def test_thread_safety(self):
        """Test that cache operations are thread-safe."""
        cache = DNSCache(max_size=100)
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(10):
                    question = f"question_{thread_id}_{i}".encode()
                    response = f"response_{thread_id}_{i}".encode()
                    cache.set(question, response)
                    result = cache.get(question)
                    results.append((thread_id, i, result == response))
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0, f"Thread safety test failed with errors: {errors}"
        assert len(results) == 50  # 5 threads * 10 operations each
        assert all(success for _, _, success in results)

    def test_expired_entry_cleanup(self):
        """Test that expired entries are cleaned up when accessed."""
        cache = DNSCache(ttl=1)
        question = b"test_question"
        response = b"test_response"
        
        cache.set(question, response)
        assert len(cache.cache) == 1
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Access should trigger cleanup
        result = cache.get(question)
        assert result is None
        assert len(cache.cache) == 0

    @patch('time.time')
    def test_time_mocking(self, mock_time):
        """Test cache behavior with mocked time."""
        mock_time.return_value = 1000
        
        cache = DNSCache(ttl=300)
        question = b"test_question"
        response = b"test_response"
        
        cache.set(question, response)
        assert cache.get(question) == response
        
        # Advance time beyond TTL
        mock_time.return_value = 1400  # 400 seconds later
        assert cache.get(question) is None

    def test_empty_cache_operations(self):
        """Test operations on empty cache."""
        cache = DNSCache()
        
        # Get from empty cache
        assert cache.get(b"anything") is None
        
        # Cache should still be empty
        assert len(cache.cache) == 0

    def test_large_data_handling(self):
        """Test cache with larger data payloads."""
        cache = DNSCache()
        
        # Create large question and response
        large_question = b"x" * 1000
        large_response = b"y" * 5000
        
        cache.set(large_question, large_response)
        result = cache.get(large_question)
        
        assert result == large_response
        assert len(result) == 5000 