#!/usr/bin/env python3

import argparse
import logging
import atexit
import os
from dotenv import load_dotenv
from utils.logger_config import setup_logging


def main():
    """Main entry point for Memory-Bear"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Memory-Bear...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Memory-Bear MCP Server")
    parser.add_argument(
        "--server", 
        action="store_true", 
        help="Start the MCP server"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the file watcher test"
    )
    
    args = parser.parse_args()

    if args.server:
        logger.info("MCP server starting...")

    elif args.test:
        os.environ["TEST_MODE"] = "True"
        os.environ["NOTES_DIR"] = os.getenv("TEST_NOTES_DIR")
        logger.info("MCP test server starting...")

    else:
        parser.print_help()
        logger.info("Use --server to start MCP server or --test to start test MCP server")
        return

    # Common setup for both server and test modes
    from server import setup_server, stop_server
    atexit.register(stop_server)
    
    # Initialize server after environment variables are set
    setup_server()
    
    # Start the server
    from server import mcp
    mcp.run()


if __name__ == "__main__":
    main() 