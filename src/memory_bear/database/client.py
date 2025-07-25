"""
Weaviate client connection management.
"""

import weaviate
import os
import logging
from .config import setup_ssl_certificates
from ..config import HUGGINGFACE_API_KEY

# Get logger for this module
logger = logging.getLogger(__name__)


def get_weaviate_client():
    """
    Create and return a Weaviate client connection.
    """
    # Setup SSL certificates
    setup_ssl_certificates()
    
    # Try to connect to existing instance first, then fall back to embedded
    try:
        client = weaviate.connect_to_local(
            port=8079, 
            grpc_port=50050,
            headers={
                "X-HuggingFace-Api-Key": HUGGINGFACE_API_KEY
            }
        )
        logger.info("Connected to existing Weaviate instance")
        return client
    except Exception as e:
        logger.info(f"No existing instance found, starting embedded: {e}")
        client = weaviate.connect_to_embedded(
            headers={
                "X-HuggingFace-Api-Key": HUGGINGFACE_API_KEY
            }
        )
        return client 