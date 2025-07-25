"""
Find best match tool implementation for Memory Bear.
"""

import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from weaviate.exceptions import WeaviateQueryError, WeaviateTimeoutError
from ..server import mcp
from .prompts import get_prompt

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def find_best_match(
    query: str,
    ctx: Context,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Find the top semantic match and determine if it should be edited.
    
    Args:
        query: Search query string
        ctx: MCP context containing Weaviate client and collection
        tags: Optional list of tags to filter by
        
    Returns:
        Dictionary with match decision and existing note details
    """
    get_prompt("FIND_BEST_MATCH_PROMPT")
    
    weaviate_client = ctx.fastmcp.weaviate_client
    collection = ctx.fastmcp.collection

    logger.info(f"Weaviate client: {weaviate_client}")
    logger.info(f"Collection: {collection}")
    
    try:
        logger.info(f"Finding best match for query: '{query}' with tags: {tags}")
        
        # Import utilities
        from ..utils.search import execute_semantic_search
        from ..utils.files import calculate_match_score
        
        # Get only the top semantic match
        search_results = execute_semantic_search(
            collection=collection,
            query=query,
            tags=tags,
            limit=1  # Only get the best semantic match
        )
        
        # If no results found
        if not search_results:
            logger.info("No existing notes found for matching")
            return {
                'should_edit': False,
                'existing_note': None,
                'final_score': 0.0,
                'decision_reason': 'No existing notes found'
            }
        
        # Process the top match
        obj = search_results[0]
        props = obj.properties
        metadata = obj.metadata
        
        # Get semantic score
        distance = metadata.score if metadata.score is not None else 1.0
        semantic_score = max(0.0, 1.0 - distance)  # Convert distance to similarity
        
        # Calculate final match score
        final_score = calculate_match_score(
            semantic_score=semantic_score,
            existing_tags=props.get('tags', []),
            new_tags=tags or [],
            content=props.get('content', '')
        )
        
        # Format existing note for context
        existing_note = {
            'title': props.get('title', 'Untitled'),
            'content': props.get('content', ''),
            'file_path': props.get('file_path', ''),
            'tags': props.get('tags', []),
            'semantic_score': round(semantic_score, 3),
            'final_score': round(final_score, 3)
        }
        
        # Decision threshold: 0.6
        if final_score >= 0.6:
            logger.info(f"Good match found (score: {final_score:.3f}) - recommending edit")
            return {
                'should_edit': True,
                'existing_note': existing_note,
                'final_score': round(final_score, 3),
                'decision_reason': f'Good match found (score: {final_score:.3f})'
            }
        else:
            logger.info(f"Match score too low (score: {final_score:.3f}) - recommending create")
            return {
                'should_edit': False,
                'existing_note': existing_note,  # Still provide for context
                'final_score': round(final_score, 3),
                'decision_reason': f'Match score too low (score: {final_score:.3f})'
            }
            
    except WeaviateQueryError as e:
        logger.error(f"Weaviate query error: {e}")
        raise Exception(f"Best match search failed: {e}")
    except WeaviateTimeoutError as e:
        logger.error(f"Weaviate timeout during search: {e}")
        raise Exception(f"Best match search timed out: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during best match search: {e}")
        raise Exception(f"Best match search failed: {e}")