"""
Study cards tool implementation for Memory Bear.
"""

import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from weaviate.exceptions import WeaviateQueryError, WeaviateTimeoutError
from ..server import mcp
from ..database.card_operations import CardOperations

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def get_cards(
    ctx: Context,
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None,
    deck_title: Optional[str] = None,
    date_filter: str = "today"
) -> Dict[str, Any]:
    """
    Get actual cards for study session with LLM coaching data.
    
    Args:
        subject: Filter by specific subject
        tags: Filter by tags - must contain ALL specified tags (AND logic)  
        deck_title: Filter by specific note/deck title
        date_filter: "overdue", "today", "this_week", "all"
        
    Returns:
        Raw data with up to 50 cards with full details for study session
    """
    
    try:
        logger.info(f"Study cards requested with filters: subject={subject}, tags={tags}, deck_title={deck_title}, date_filter={date_filter}")
        
        # Access cards collection from context
        cards_collection = ctx.fastmcp.cards_collection
        
        # Initialize CardOperations
        card_ops = CardOperations(cards_collection)
        
        # Get study cards data
        result = card_ops.get_cards(subject, tags, deck_title, date_filter)
        
        logger.info(f"Study cards completed: {result['total_cards']} cards returned")
        return result
        
    except WeaviateQueryError as e:
        logger.error(f"Weaviate query error in study cards: {e}")
        raise Exception(f"Study cards query failed: {e}")
    except WeaviateTimeoutError as e:
        logger.error(f"Weaviate timeout during study cards: {e}")
        raise Exception(f"Study cards timed out: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in study cards: {e}")
        raise Exception(f"Study cards failed: {e}")