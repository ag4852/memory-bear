"""
Search tool implementation for Memory Bear.
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
async def search_notes(
    query: str, 
    ctx: Context, 
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    get_prompt("SEARCH_NOTES_PROMPT")

    weaviate_client = ctx.fastmcp.weaviate_client
    collection = ctx.fastmcp.collection

    logger.info(f"Weaviate client: {weaviate_client}")
    logger.info(f"Collection: {collection}")
    
    try:
        logger.info(f"Search requested for query: '{query}' with subject: {subject}, tags: {tags}")
        
        # Import and use shared search logic
        from ..utils.search import execute_semantic_search
        
        # Execute semantic search using shared helper
        response = execute_semantic_search(
            collection=collection,
            query=query,
            subject=subject,
            tags=tags,
            limit=3  # Internal default
        )
        
        # Format results for MCP response
        results = []
        for obj in response:

            props = obj.properties
            metadata = obj.metadata
            
            # Get confidence score (Weaviate returns distance, convert to similarity)
            distance = metadata.score if metadata.score is not None else 1.0
            confidence_score = max(0.0, 1.0 - distance)  # Convert distance to similarity
            
            # Get full content (no truncation)
            content = props.get('content', '')
            
            result = {
                'title': props.get('title', 'Untitled'),
                'subject': props.get('subject', 'General'),
                'content': content,
                'file_path': props.get('file_path', ''),
                'tags': props.get('tags', []),
                'confidence_score': round(confidence_score, 3)
            }
            results.append(result)
        
        logger.info(f"Found {len(results)} results for query: '{query}'")
        return results
        
    except WeaviateQueryError as e:
        logger.error(f"Weaviate query error: {e}")
        raise Exception(f"Search query failed: {e}")
    except WeaviateTimeoutError as e:
        logger.error(f"Weaviate timeout during search: {e}")
        raise Exception(f"Search timed out: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise Exception(f"Search failed: {e}") 