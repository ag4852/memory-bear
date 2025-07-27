"""
Cards overview tool implementation for Memory Bear.
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
async def get_cards_overview(
    ctx: Context,
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None, 
    date_filter: str = "today",
    view: str = "subject_notes"
) -> Dict[str, Any]:
    """
    Get overview of cards due for study with flexible grouping.
    
    Args:
        subject: Filter by specific subject (e.g. "Mathematics")
        tags: Filter by tags - must contain ALL specified tags (AND logic)
        date_filter: "overdue", "today", "this_week", "all" 
        view: "subjects", "subject_notes", "tag_subjects"
        
    Returns:
        Raw data with grouped counts for study planning
    """
    
    try:
        logger.info(f"Cards overview requested with filters: subject={subject}, tags={tags}, date_filter={date_filter}, view={view}")
        
        # Access cards collection from context
        cards_collection = ctx.fastmcp.cards_collection
        
        # Initialize CardOperations
        card_ops = CardOperations(cards_collection)
        
        # Get overview data
        result = card_ops.get_cards_overview(subject, tags, date_filter, view)
        
        logger.info(f"Cards overview completed: {result['total_due_cards']} cards found")
        return result
        
    except WeaviateQueryError as e:
        logger.error(f"Weaviate query error in cards overview: {e}")
        raise Exception(f"Cards overview query failed: {e}")
    except WeaviateTimeoutError as e:
        logger.error(f"Weaviate timeout during cards overview: {e}")
        raise Exception(f"Cards overview timed out: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in cards overview: {e}")
        raise Exception(f"Cards overview failed: {e}")