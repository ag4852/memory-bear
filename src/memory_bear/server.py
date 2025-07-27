import logging
from mcp.server.fastmcp import FastMCP
from .database import get_weaviate_client, get_or_create_collection
from .database.collections import get_or_create_cards_collection
from .watcher import WatcherManager

# Set up logging
logger = logging.getLogger(__name__)

# Create the MCP server instance first so tools can import it
mcp = FastMCP("Memory Bear")

def setup_server():
    """Initialize and configure the MCP server"""
    
    # Store client and both collections
    mcp.weaviate_client = get_weaviate_client()
    mcp.collection = get_or_create_collection(mcp.weaviate_client)
    mcp.cards_collection = get_or_create_cards_collection(mcp.weaviate_client)
    
    # Perform initial sync before starting file watcher
    try:
        logger.info("Performing initial sync between filesystem and Weaviate...")
        from .watcher.sync import sync_notes
        
        # Run initial sync using MarkdownOperations directly (no handler needed)
        sync_result = sync_notes(mcp.collection)
        
        if sync_result["success"]:
            logger.info(f"Initial sync completed successfully: "
                       f"{sync_result['indexed_count']} indexed, "
                       f"{sync_result['modified_count']} updated, "
                       f"{sync_result['deleted_count']} deleted")
        else:
            logger.error(f"Initial sync failed: {sync_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error during initial sync: {e}")
        logger.warning("Server will continue with file watcher startup")
    
    # Initialize and start file watcher
    try:
        mcp.watcher_manager = WatcherManager(mcp.collection)
        mcp.watcher_manager.start()
        logger.info("File watcher initialized and started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize/start file watcher: {e}")
        logger.warning("Server will continue without file watching capabilities")
        mcp.watcher_manager = None  # Ensure it's None for the shutdown check

    # Import tools to register them with the server (now that mcp exists)
    from .tools import search_notes, create_study_note, find_best_match, edit_study_note, get_cards_overview, get_cards, create_cards_from_note  # This registers the @mcp.tool() decorated functions
    logger.info("Tools imported and registered")
        
    return mcp


def stop_server():
    """Stop the server and file watcher on shutdown"""
    logger.info("Shutting down MCP server...")
    
    # Stop file watcher
    if hasattr(mcp, 'watcher_manager') and mcp.watcher_manager.is_running():
        logger.info("Stopping file watcher...")
        try:
            mcp.watcher_manager.stop()
            logger.info("File watcher stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")
    
    # Close Weaviate client connection
    if hasattr(mcp, 'weaviate_client'):
        logger.info("Closing Weaviate client connection...")
        try:
            mcp.weaviate_client.close()
            logger.info("Weaviate client connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Weaviate client: {e}")
