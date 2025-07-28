"""
Update card tool implementation for Memory Bear.
"""

import logging
from typing import Dict, Any

from mcp.server.fastmcp import Context
from weaviate.exceptions import WeaviateQueryError, WeaviateTimeoutError
from ..server import mcp
from ..database.card_operations import CardOperations

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def update_card(
    ctx: Context,
    card_uuid: str,
    fsrs_rating: int,
    learning_summary: str
) -> Dict[str, Any]:
    """
    Update a card after review with FSRS scheduling and learning summary.
    
    Args:
        card_uuid: UUID of the card to update
        fsrs_rating: User rating (1=Again, 2=Hard, 3=Good, 4=Easy)
        learning_summary: Brief reflection of the learning session
        
    Returns:
        Dictionary with success status and updated card details
    """
    
    try:
        logger.info(f"Card update requested: {card_uuid}, rating={fsrs_rating}")
        
        # Access cards collection from context
        cards_collection = ctx.fastmcp.cards_collection
        
        # Initialize CardOperations
        card_ops = CardOperations(cards_collection)
        
        # Update card with FSRS scheduling
        result = card_ops.update_card(card_uuid, fsrs_rating, learning_summary)
        
        logger.info(f"Card update completed: {result['success']}")
        return result
        
    except WeaviateQueryError as e:
        logger.error(f"Weaviate query error in update card: {e}")
        raise Exception(f"Card update query failed: {e}")
    except WeaviateTimeoutError as e:
        logger.error(f"Weaviate timeout during card update: {e}")
        raise Exception(f"Card update timed out: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in card update: {e}")
        raise Exception(f"Card update failed: {e}")