"""
Exception classes for Memory Bear tools.
"""

class MemoryBearError(Exception):
    """Base exception for Memory Bear business logic errors"""
    pass

class DatabaseConnectionError(MemoryBearError):
    """Raised when unable to connect to Weaviate"""
    pass

class SearchError(MemoryBearError):
    """Raised when search operation fails"""
    pass 