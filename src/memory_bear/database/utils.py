"""
Database utilities for markdown file operations.

This module provides classes to handle database operations for different file types,
separating database logic from event handling logic.
"""

import logging
from weaviate.classes.query import Filter
from ..utils.markdown import parse_md_file

# Get logger for this module
logger = logging.getLogger(__name__)


class MarkdownOperations:
    """
    Handles database operations for markdown files.
    
    This class encapsulates all Weaviate operations specific to markdown files,
    including indexing, updating, and deleting files from the collection.
    """
    
    def __init__(self, memory_collection):
        """
        Initialize markdown operations with a Weaviate collection.
        
        Args:
            memory_collection: Weaviate Memory collection instance
        """
        self.memory_collection = memory_collection
    
    def index_file(self, file_path: str) -> bool:
        """
        Parse and index a markdown file into Weaviate.
        
        Args:
            file_path: Path to the markdown file to index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Indexing markdown file: {file_path}")
            
            # Parse the markdown file (includes all metadata and timestamps)
            parsed_data = parse_md_file(file_path)
            
            # Insert into Weaviate
            self.memory_collection.data.insert({
                "title": parsed_data['title'],
                "content": parsed_data['content'],
                "file_path": parsed_data['file_path'],
                "tags": parsed_data['tags'],
                "created_at": parsed_data['created_at'],
                "updated_at": parsed_data['updated_at']
            })
            
            logger.info(f"Successfully indexed file: {parsed_data['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            return False
    
    def update_file(self, file_path: str) -> bool:
        """
        Find existing markdown file in Weaviate and update it with new content.
        
        Args:
            file_path: Path to the markdown file to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating markdown file: {file_path}")
            
            # Query Weaviate to find existing object by file_path
            response = self.memory_collection.query.fetch_objects(
                filters=Filter.by_property("file_path").equal(file_path),
                limit=1
            )
            
            if not response.objects:
                logger.warning(f"No existing object found in Weaviate for file: {file_path}")
                return False
            
            # Get the existing object's UUID
            existing_obj = response.objects[0]
            existing_uuid = existing_obj.uuid
            
            # Parse the modified file content
            parsed_data = parse_md_file(file_path)
            
            # Update the existing object with new content (same UUID)
            self.memory_collection.data.update(
                uuid=existing_uuid,
                properties={
                    "title": parsed_data['title'],
                    "content": parsed_data['content'],
                    "tags": parsed_data['tags'],
                    "updated_at": parsed_data['updated_at']
                    # Note: file_path and created_at remain unchanged
                }
            )
            
            logger.info(f"Successfully updated file: {parsed_data['title']} (UUID: {existing_uuid})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {e}")
            return False
    
    def move_file(self, old_path: str, new_path: str) -> bool:
        """
        Update the file path of an existing markdown file in Weaviate.
        
        When a file is moved or renamed, this updates only the file_path property
        while preserving all other content and the same UUID.
        
        Args:
            old_path: Original file path
            new_path: New file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Moving markdown file: {old_path} → {new_path}")
            
            # Query Weaviate to find existing object by old file_path
            response = self.memory_collection.query.fetch_objects(
                filters=Filter.by_property("file_path").equal(old_path),
                limit=1
            )
            
            if not response.objects:
                logger.warning(f"No existing object found in Weaviate for moved file: {old_path}")
                return False
            
            # Get the existing object's UUID
            existing_obj = response.objects[0]
            existing_uuid = existing_obj.uuid
            
            # Update the existing object with new file_path (same UUID, same content)
            self.memory_collection.data.update(
                uuid=existing_uuid,
                properties={
                    "file_path": new_path
                    # Note: All other properties (title, content, tags, created_at, updated_at) remain unchanged
                }
            )
            
            logger.info(f"Successfully updated file path: {old_path} → {new_path} (UUID: {existing_uuid})")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {old_path} → {new_path}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        Find and delete a markdown file from Weaviate.
        
        Args:
            file_path: Path to the markdown file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Deleting markdown file: {file_path}")
            
            # Query Weaviate to find existing object by file_path
            response = self.memory_collection.query.fetch_objects(
                filters=Filter.by_property("file_path").equal(file_path),
                limit=1
            )
            
            if not response.objects:
                logger.warning(f"No existing object found in Weaviate for file: {file_path}")
                return False
            
            # Get the existing object's UUID
            existing_obj = response.objects[0]
            existing_uuid = existing_obj.uuid
            
            # Delete the object from Weaviate
            self.memory_collection.data.delete_by_id(existing_uuid)
            
            logger.info(f"Successfully deleted file from Weaviate: {file_path} (UUID: {existing_uuid})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False 