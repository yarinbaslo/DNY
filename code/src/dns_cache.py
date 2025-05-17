import time
from threading import Lock

class DNSCache:
    def __init__(self, max_size=1000, ttl=300):
        """
        :param max_size: Max number of cached entries
        :param ttl: Time to live for each cache entry (in seconds)
        """
        self.cache = {}  # question -> (response, expire_time)
        self.max_size = max_size
        self.ttl = ttl
        self.lock = Lock()

    def get(self, question):
        """
        Get cached response for a DNS question
        """
        with self.lock:
            entry = self.cache.get(question)
            if not entry:
                return None
            response, expire_time = entry
            if time.time() > expire_time:
                del self.cache[question]
                return None
            return response

    def set(self, question, response):
        """
        Store DNS response in cache
        """
        with self.lock:
            # Limit size
            if len(self.cache) >= self.max_size:
                self.cache.pop(next(iter(self.cache)))  # FIFO eviction
            self.cache[question] = (response, time.time() + self.ttl)
