"""
Shared search utilities for Memory Bear.
Provides common Weaviate search functionality used by multiple tools.
"""

import logging
from typing import List, Optional
from weaviate.classes.query import Filter

# Get logger for this module
logger = logging.getLogger(__name__)


def execute_semantic_search(
    collection, 
    query: str,
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None, 
    limit: int = 3
) -> List:
    """
    Shared Weaviate search logic used by multiple tools.
    
    Args:
        collection: Weaviate collection instance
        query: Search query string
        subject: Optional subject to filter by
        tags: Optional list of tags to filter by (must have ALL tags)
        limit: Maximum number of results to return
        
    Returns:
        List of Weaviate objects with properties and metadata
        
    Raises:
        Exception: If search query fails
    """
    try:
        logger.info(f"Executing semantic search for query: '{query}' with subject: {subject}, tags: {tags}, limit: {limit}")
        
        # Build filters
        filters = None
        if subject:
            filters = Filter.by_property("subject").equal(subject)
        if tags:
            tag_filter = Filter.by_property("tags").contains_all(tags)
            filters = filters & tag_filter if filters else tag_filter
        
        # Execute semantic search
        response = collection.query.near_text(
            query=query,
            limit=limit, 
            return_metadata=['score'],
            filters=filters  
        ).objects
        
        logger.info(f"Search returned {len(response)} results")
        return response
        
    except Exception as e:
        logger.error(f"Error executing semantic search: {e}")
        raise e