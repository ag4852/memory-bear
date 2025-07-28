"""
Weaviate collection management and schema operations.
"""

import logging
import os
from weaviate.classes.config import Configure, Property, DataType

# Get logger for this module
logger = logging.getLogger(__name__)


def get_or_create_collection(client):
    """
    Get or create the collection in Weaviate.
    Uses 'Memory' collection in normal mode, 'Bear' collection in test mode.
    """
    # Determine collection name based on TEST_MODE environment variable
    collection_name = "Bear" if os.getenv("TEST_MODE") == "True" else "Memory"
    
    try:
        # Try to get existing collection
        logger.info(f"Checking for existing {collection_name} collection...")
        collection = client.collections.get(collection_name)

        # Verify the collection actually exists by checking its schema
        try:
            config = collection.config.get()
            logger.info(f"Found existing {collection_name} collection with vectorizer: {config.vectorizer}")
        except Exception as schema_error:
            logger.warning(f"Collection reference exists but schema check failed: {schema_error}")
            # Fall through to create new collection
            raise Exception("Collection reference stale, need to recreate")
        
        return collection
            
    except Exception as e:
        # Create new collection if it doesn't exist
        logger.info(f"{collection_name} collection not found or stale, creating new one: {e}")
        try:
            # First ensure any stale collection is deleted
            try:
                client.collections.delete(collection_name)
                logger.info(f"Deleted stale {collection_name} collection")
            except Exception:
                logger.info(f"No stale collection to delete")
            
            collection = client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="subject", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="file_path", data_type=DataType.TEXT), 
                    Property(name="tags", data_type=DataType.TEXT_ARRAY),
                    Property(name="created_at", data_type=DataType.DATE),
                    Property(name="updated_at", data_type=DataType.DATE)
                ],
                vectorizer_config=Configure.Vectorizer.text2vec_huggingface(
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
            )
            
            return collection
        except Exception as create_error:
            logger.error(f"Failed to create {collection_name} collection: {create_error}")
            raise create_error


def get_or_create_cards_collection(client):
    """
    Get or create the cards collection in Weaviate.
    Uses 'MemoryCards' collection in normal mode, 'BearCards' collection in test mode.
    """
    # Determine collection name based on TEST_MODE environment variable
    collection_name = "BearCards" if os.getenv("TEST_MODE") == "True" else "MemoryCards"
    
    try:
        # Try to get existing collection
        logger.info(f"Checking for existing {collection_name} collection...")
        collection = client.collections.get(collection_name)

        # Verify the collection actually exists by checking its schema
        try:
            config = collection.config.get()
            logger.info(f"Found existing {collection_name} collection with vectorizer: {config.vectorizer}")
        except Exception as schema_error:
            logger.warning(f"Collection reference exists but schema check failed: {schema_error}")
            # Fall through to create new collection
            raise Exception("Collection reference stale, need to recreate")
        
        return collection
            
    except Exception as e:
        # Create new collection if it doesn't exist
        logger.info(f"{collection_name} collection not found or stale, creating new one: {e}")
        try:
            # First ensure any stale collection is deleted
            try:
                client.collections.delete(collection_name)
                logger.info(f"Deleted stale {collection_name} collection")
            except Exception:
                logger.info(f"No stale collection to delete")
            
            collection = client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="parent_note_uuid", data_type=DataType.TEXT),
                    Property(name="parent_note_title", data_type=DataType.TEXT),
                    Property(name="parent_note_subject", data_type=DataType.TEXT),
                    Property(name="parent_note_tags", data_type=DataType.TEXT_ARRAY),
                    Property(name="prompt_text", data_type=DataType.TEXT),
                    Property(name="fsrs_card_json", data_type=DataType.TEXT),
                    Property(name="due_date", data_type=DataType.DATE),
                    Property(
                        name="review_history", 
                        data_type=DataType.OBJECT_ARRAY,
                        nested_properties=[
                            Property(name="timestamp", data_type=DataType.DATE),
                            Property(name="fsrs_rating", data_type=DataType.INT),
                            Property(name="learning_summary", data_type=DataType.TEXT)
                        ]
                    ),
                    Property(name="deck_archived", data_type=DataType.BOOL),
                ],
                vectorizer_config=Configure.Vectorizer.text2vec_huggingface(
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
            )
            
            return collection
        except Exception as create_error:
            logger.error(f"Failed to create {collection_name} collection: {create_error}")
            raise create_error


