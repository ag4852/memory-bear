#!/usr/bin/env python3

import os
import sys
import logging

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Set up logging
from utils.logger_config import setup_logging
setup_logging("INFO")

logger = logging.getLogger(__name__)

# Set test mode before connecting to database
os.environ["TEST_MODE"] = "True"
os.environ["NOTES_DIR"] = os.getenv("TEST_NOTES_DIR")

from sync_test_base import SyncTestBase


def test_sync_workflow():
    """
    Test complete sync workflow with offline file operations.
    
    This test simulates a real-world scenario where:
    1. Files are created while the server is running (baseline)
    2. Server goes offline
    3. Various file operations happen while offline (create, modify, delete, move)
    4. Server comes back online
    5. All offline changes are synchronized to the database
    """
    
    sync_base = SyncTestBase()
    
    try:
        # Setup: Initialize Weaviate connection
        logger.info("Starting sync workflow test...")
        sync_base.setup()
        
        # Phase 1: Create baseline files (server running)
        logger.info("Phase 1: Setting up baseline files...")
        baseline_state = sync_base.setup_baseline_files(count=3)
        logger.info(f"Created {len(baseline_state)} baseline files with distinct content")
        
        # Phase 2: Stop server automatically
        logger.info("Phase 2: Stopping server for offline operations...")
        sync_base.stop_server()
        logger.info("Server stopped successfully")
        
        # Phase 3: Make offline changes (server stopped)
        logger.info("Phase 3: Making offline file system changes...")
        offline_changes = sync_base.make_offline_changes(baseline_state)
        
        # Log what changes were made
        logger.info("Offline changes summary:")
        logger.info(f"  - Created: {len(offline_changes['created'])} new files")
        logger.info(f"  - Modified: {len(offline_changes['modified'])} existing files")
        logger.info(f"  - Deleted: {len(offline_changes['deleted'])} files")
        logger.info(f"  - Moved: {len(offline_changes['moved'])} files")
        
        # Phase 4: Restart server automatically
        logger.info("Phase 4: Starting server to trigger sync...")
        sync_base.start_server()
        logger.info("Server started successfully")
        
        # Phase 5: Verify sync results (server running)
        logger.info("Phase 5: Verifying sync results...")
        sync_base.verify_sync_results(offline_changes, timeout=20)
        
        logger.info("Sync workflow test completed successfully!")
        logger.info("All offline file operations were properly synchronized to the database")
        
    except Exception as e:
        logger.error(f"Sync workflow test failed: {e}")
        logger.error("Check server logs for additional details")
        raise
        
    finally:
        # Ensure server is running for cleanup
        logger.info("Performing cleanup...")
        try:
            # Make sure server is running before teardown
            sync_base.start_server()
            logger.info("Server restarted for cleanup")
        except Exception as e:
            logger.warning(f"Could not restart server for cleanup: {e}")
        
        # Clean up test artifacts
        sync_base.teardown()
        logger.info("Cleanup completed")


def main():
    """Main entry point for sync workflow testing"""
    try:
        test_sync_workflow()
        logger.info("SYNC WORKFLOW TEST PASSED")
        
    except Exception as e:        
        logger.info("SYNC WORKFLOW TEST FAILED")
        logger.info(f"Error: {e}")
        logger.info("Check the logs above for detailed error information.")
        raise


if __name__ == "__main__":
    main() 