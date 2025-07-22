"""
Database package for Weaviate operations.
"""

from .client import get_weaviate_client
from .collections import get_or_create_collection
from .config import setup_ssl_certificates

__all__ = [
    "get_weaviate_client",
    "get_or_create_collection", 
    "setup_ssl_certificates",
] 