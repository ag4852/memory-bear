"""
Search tool implementation for Memory Bear.
"""

import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from weaviate.exceptions import WeaviateQueryError, WeaviateTimeoutError
from weaviate.classes.query import Filter
from server import mcp
from .prompts import get_prompt

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def search_notes(query: str, ctx: Context, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    get_prompt("SEARCH_NOTES_PROMPT")

    weaviate_client = ctx.fastmcp.weaviate_client
    collection = ctx.fastmcp.collection

    logger.info(f"Weaviate client: {weaviate_client}")
    logger.info(f"Collection: {collection}")
    
    try:
        logger.info(f"Search requested for query: '{query}' with tags: {tags}")
        
        # TODO: move to a method on a WeaviateClient class
        # Build tag filters if specified (must have ALL tags)
        filters = None
        if tags:
            filters = Filter.by_property("tags").contains_all(tags)
        
        # Execute semantic search
        response = collection.query.near_text(
            query=query,
            limit=3, 
            return_metadata=['score'],
            filters=filters  
        ).objects
        
        # Format results for MCP response
        results = []
        for obj in response:

            props = obj.properties
            metadata = obj.metadata
            
            # Get confidence score (Weaviate returns distance, convert to similarity)
            distance = metadata.score if metadata.score is not None else 1.0
            confidence_score = max(0.0, 1.0 - distance)  # Convert distance to similarity
            
            # Truncate content if too long (prevent context overflow)
            content = props.get('content', '')
            if len(content) > 2000:  # Reasonable limit for MCP context
                content = content[:2000] + "..."
            
            result = {
                'title': props.get('title', 'Untitled'),
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