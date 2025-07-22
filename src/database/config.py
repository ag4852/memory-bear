"""
Database configuration utilities.
"""

import os
import logging
import certifi
from dotenv import load_dotenv, find_dotenv

# Load environment variables early (before any functions are called)
load_dotenv(find_dotenv())

# Get logger for this module
logger = logging.getLogger(__name__)


def setup_ssl_certificates():
    """
    Configure SSL certificates for Weaviate connection.
    Sets up SSL_CERT_FILE and SSL_CERT_DIR environment variables if not already set.
    """
    if not os.environ.get('SSL_CERT_FILE') or not os.environ.get('SSL_CERT_DIR'):
        logger.info("SSL_CERT_FILE or SSL_CERT_DIR not set, using certifi.where()")
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())
    else:
        logger.info("Using existing SSL_CERT_FILE and SSL_CERT_DIR") 