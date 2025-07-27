"""
Create cards from note tool implementation for Memory Bear.
"""

import logging
from typing import Dict, Any

from mcp.server.fastmcp import Context
from weaviate.exceptions import WeaviateQueryError, WeaviateTimeoutError
from weaviate.classes.query import Filter
from ..server import mcp
from ..database.card_operations import CardOperations

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def create_cards_from_note(
    note_title: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Create flashcards from recall prompts in a specific note.
    
    Args:
        note_title: Exact title of the note to create cards from
        
    Returns:
        Dictionary with success status, message, and card creation details
    """
    
    try:
        logger.info(f"Creating cards from note: '{note_title}'")
        
        # Access collections from context
        collection = ctx.fastmcp.collection
        cards_collection = ctx.fastmcp.cards_collection
        
        # 1. Try exact title match first
        response = collection.query.fetch_objects(
            where=Filter.by_property("title").equal(note_title),
            limit=1
        )
        note = response.objects[0] if response.objects else None
        
        # 2. Fuzzy search fallback if no exact match
        if not note:
            # Use existing semantic search utility
            from ..utils.search import execute_semantic_search
            
            fuzzy_results = execute_semantic_search(
                collection=collection,
                query=note_title,
                limit=3  # Get top 3 for suggestions
            )
            
            if fuzzy_results:
                # Return suggestions for user confirmation
                suggestions = [r.properties['title'] for r in fuzzy_results]
                logger.info(f"No exact match for '{note_title}', found {len(suggestions)} suggestions")
                return {
                    "success": False,
                    "message": "No exact match found. Did you mean one of these?",
                    "suggestions": suggestions
                }
            else:
                # No matches at all
                logger.info(f"No matches found for '{note_title}'")
                return {
                    "success": False,
                    "message": "Note not found",
                    "searched_title": note_title
                }
        
        # 3. Check for existing cards
        existing_response = cards_collection.query.fetch_objects(
            where=Filter.by_property("parent_note_uuid").equal(str(note.uuid)),
            limit=1  # Just check if any exist
        )
        
        if existing_response.objects:
            # Count existing cards
            count_response = cards_collection.query.fetch_objects(
                where=Filter.by_property("parent_note_uuid").equal(str(note.uuid)),
                limit=1000  # Get all to count accurately
            )
            existing_count = len(count_response.objects)
            
            logger.info(f"Cards already exist for '{note_title}' ({existing_count} cards)")
            return {
                "success": False,
                "message": f"Cards already exist for '{note_title}'. Cannot create duplicates.",
                "cards_already_existed": True,
                "note_title": note_title,
                "existing_card_count": existing_count
            }
        
        # 4. Create cards using existing CardOperations
        card_ops = CardOperations(cards_collection)
        success = card_ops.create_cards_from_note(note)
        
        if success:
            # Count cards created (query again to get actual count)
            new_response = cards_collection.query.fetch_objects(
                where=Filter.by_property("parent_note_uuid").equal(str(note.uuid)),
                limit=50
            )
            cards_created = len(new_response.objects)
            
            logger.info(f"Successfully created {cards_created} cards from '{note_title}'")
            return {
                "success": True,
                "message": f"Successfully created {cards_created} cards from '{note_title}'",
                "cards_created": cards_created,
                "note_title": note_title,
                "next_action_hint": f'Use get_cards with deck_title="{note_title}" to study these cards'
            }
        else:
            logger.error(f"Failed to create cards from '{note_title}'")
            return {
                "success": False,
                "message": f"Failed to create cards from '{note_title}'",
                "note_title": note_title
            }
            
    except WeaviateQueryError as e:
        logger.error(f"Weaviate query error in create_cards_from_note: {e}")
        raise Exception(f"Card creation failed: {e}")
    except WeaviateTimeoutError as e:
        logger.error(f"Weaviate timeout during create_cards_from_note: {e}")
        raise Exception(f"Card creation timed out: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in create_cards_from_note: {e}")
        raise Exception(f"Card creation failed: {e}")