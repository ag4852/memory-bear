"""
Smart synchronization functionality for keeping Weaviate in sync with filesystem.

This module provides functions to compare the filesystem state with Weaviate
and sync only the files that have changed, avoiding unnecessary re-indexing.
"""

import os
import glob
import logging
from pathlib import Path
from datetime import datetime, timezone
from weaviate.classes.query import Filter
from ..database.utils import MarkdownOperations

# Get logger for this module
logger = logging.getLogger(__name__)


def get_filesystem_files(notes_dir: str) -> dict[str, datetime]:
    """
    Get all markdown files from the filesystem with their modification times.
    
    Args:
        notes_dir: Path to the notes directory
        
    Returns:
        Dictionary mapping file_path to updated_at datetime for all .md files found
    """
    try:
        # Find all markdown files recursively
        pattern = os.path.join(notes_dir, "**", "*.md")
        md_files = glob.glob(pattern, recursive=True)
        
        filesystem_files = {}
        for file_path in md_files:
            try:
                # Get file modification time and convert to datetime with timezone
                mtime = os.path.getmtime(file_path)
                updated_at = datetime.fromtimestamp(mtime, tz=timezone.utc)
                
                filesystem_files[file_path] = updated_at
            except Exception as e:
                logger.warning(f"Error getting modification time for {file_path}: {e}")
                continue
        
        logger.info(f"Found {len(filesystem_files)} markdown files in filesystem")
        return filesystem_files
        
    except Exception as e:
        logger.error(f"Error scanning filesystem: {e}")
        return {}


def get_weaviate_files(memory_collection) -> dict[str, datetime]:
    """
    Get all indexed files from Weaviate with their updated timestamps.
    
    Args:
        memory_collection: Weaviate Memory collection instance
        
    Returns:
        Dictionary mapping file_path to updated_at datetime for all files currently indexed in Weaviate
    """
    try:
        # Query all objects and extract file_path and updated_at properties
        response = memory_collection.query.fetch_objects(
            return_properties=["file_path", "updated_at"],
            limit=10000  # Adjust based on expected number of files
        )
        
        weaviate_files = {}
        for obj in response.objects:
            try:
                file_path = obj.properties["file_path"]
                updated_at = obj.properties["updated_at"]
                weaviate_files[file_path] = updated_at
            except Exception as e:
                logger.warning(f"Error processing Weaviate object {obj.uuid}: {e}")
                continue
        
        logger.info(f"Found {len(weaviate_files)} files indexed in Weaviate")
        return weaviate_files
        
    except Exception as e:
        logger.error(f"Error querying Weaviate: {e}")
        return {}


def sync_notes(memory_collection) -> dict:
    """
    Synchronize notes between filesystem and Weaviate.
    
    This function performs a smart sync by comparing the filesystem state
    with Weaviate and only processing files that need to be updated.
    
    Args:
        memory_collection: Weaviate Memory collection instance
        
    Returns:
        Dictionary with sync results and statistics
    """
    logger.info("Starting smart sync process...")
    
    # Get notes directory
    notes_dir = os.getenv("NOTES_DIR")
    
    try:
        # Get all files from filesystem and Weaviate
        filesystem_files = get_filesystem_files(notes_dir)
        weaviate_files = get_weaviate_files(memory_collection)
        
        # Find new files (in filesystem but not in Weaviate)
        new_files = filesystem_files.keys() - weaviate_files.keys()
        
        # Find modified files (filesystem updated_at > weaviate updated_at)
        modified_files = [
            file_path for file_path in filesystem_files.keys() & weaviate_files.keys()
            if filesystem_files[file_path] > weaviate_files[file_path]
        ]
        
        # Find deleted files (in Weaviate but not in filesystem)
        deleted_files = weaviate_files.keys() - filesystem_files.keys()
        
        logger.info(f"Sync analysis: {len(filesystem_files)} filesystem files, "
                   f"{len(weaviate_files)} indexed files, {len(new_files)} new files, "
                   f"{len(modified_files)} modified files, {len(deleted_files)} deleted files")
        
        # Create MarkdownOperations instance for database operations
        md_ops = MarkdownOperations(memory_collection)
        
        # Process new files using MarkdownOperations
        indexed_count = 0
        indexed_failed = 0
        
        for file_path in new_files:
            success = md_ops.index_file(file_path)
            if success:
                indexed_count += 1
            else:
                indexed_failed += 1
        
        # Process modified files using MarkdownOperations
        modified_count = 0
        modified_failed = 0
        
        for file_path in modified_files:
            success = md_ops.update_file(file_path)
            if success:
                modified_count += 1
            else:
                modified_failed += 1
        
        # Process deleted files using MarkdownOperations
        deleted_count = 0
        deleted_failed = 0
        
        for file_path in deleted_files:
            success = md_ops.delete_file(file_path)
            if success:
                deleted_count += 1
            else:
                deleted_failed += 1
        
        logger.info(f"Sync complete: {indexed_count} files indexed, {indexed_failed} indexed failures, "
                   f"{modified_count} files updated, {modified_failed} update failures, "
                   f"{deleted_count} files deleted, {deleted_failed} delete failures")
        
        return {
            "success": True,
            "filesystem_files": len(filesystem_files),
            "weaviate_files": len(weaviate_files),
            "new_files": len(new_files),
            "modified_files": len(modified_files),
            "deleted_files": len(deleted_files),
            "indexed_count": indexed_count,
            "indexed_failed": indexed_failed,
            "modified_count": modified_count,
            "modified_failed": modified_failed,
            "deleted_count": deleted_count,
            "deleted_failed": deleted_failed
        }
        
    except Exception as e:
        logger.error(f"Error during sync process: {e}")
        return {"success": False, "error": str(e)} 