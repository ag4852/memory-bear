#!/usr/bin/env python3

import os
import time
import logging
from datetime import datetime
from watcher_test_base import WatcherTestBase
from memory_bear.utils.markdown import parse_md_file
from weaviate.classes.query import Filter

# Set up logging
logger = logging.getLogger(__name__)

# Set test mode before connecting to database
os.environ["TEST_MODE"] = "True"
os.environ["NOTES_DIR"] = os.getenv("TEST_NOTES_DIR")

# Global test base instance for all tests in this workflow
test_base = None

def test_file_creation():
    """Test file creation and watcher indexing"""
    
    # Read template and create test file
    test_md_path = os.path.join(os.path.dirname(__file__), "test_note.md")
    with open(test_md_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
        
    file_path = test_base.create_test_file("test_note", template_content)
    logger.info(f"Created test file: {file_path}")
    
    # Parse expected data and wait for file watcher processing
    expected_data = parse_md_file(file_path)
    logger.info(f"Testing file creation for: '{expected_data['title']}' with {len(expected_data.get('tags', []))} tags")
    
    # Poll and validate indexed object
    indexed_object = test_base.poll_for_object(file_path, should_exist=True)
    test_base.validate_object(indexed_object, expected_data)
    
    logger.info(f"✅ File creation test passed - indexed {len(indexed_object.properties['content'])} characters")
    
    return file_path

def test_file_modification(file_path):
    """Test file modification and watcher indexing"""
    
    # Modify file using helper method
    test_base.modify_test_file(file_path)
    
    # Parse expected data after modification
    expected_data = parse_md_file(file_path)
    logger.info(f"Modified file to: '{expected_data['title']}' with {len(expected_data.get('tags', []))} tags")
    
    # Poll and validate modified object (skip created_at)
    updated_object = test_base.poll_for_object(
        file_path, 
        should_exist=True, 
        condition_func=lambda obj: obj.properties.get('title', '') == expected_data['title']
    )
    test_base.validate_object(updated_object, expected_data, skip_properties=['created_at'])
    
    logger.info(f"✅ File modification test passed - updated {len(updated_object.properties['content'])} characters")

def test_file_move(file_path):
    """Test file move and watcher indexing"""
    
    # Create subdirectory and prepare move destination
    notes_dir = os.getenv('NOTES_DIR')
    moved_dir = os.path.join(notes_dir, "Moved")
    os.makedirs(moved_dir, exist_ok=True)
    logger.info(f"Created moved directory: {moved_dir}")
    
    filename = os.path.basename(file_path)
    new_file_path = os.path.join(moved_dir, filename)
    logger.info(f"New file path: {new_file_path}")
    
    # Get expected object properties and uuid before move
    results = test_base.collection.query.fetch_objects(
        filters=Filter.by_property("file_path").equal(file_path),
        limit=1
    )
    expected_data = results.objects[0].properties
    expected_data['uuid'] = results.objects[0].uuid
    expected_data['file_path'] = new_file_path
    
    # Move the file
    import shutil
    shutil.move(file_path, new_file_path)
    logger.info(f"Moved file to: {new_file_path}")
    
    # Poll and validate moved object (UUID should be preserved)
    moved_object = test_base.poll_for_object(new_file_path, should_exist=True)
    test_base.validate_object(moved_object, expected_data)
    
    logger.info(f"✅ File move test passed - UUID preserved: {moved_object.uuid}")
    
    return new_file_path

def test_file_deletion(file_path):
    """Test file deletion and watcher cleanup"""
    
    # Delete the file from filesystem
    os.remove(file_path)
    logger.info(f"Deleted file: {file_path}")
    
    # Poll to verify file is removed from Weaviate
    test_base.poll_for_object(file_path, should_exist=False)
    
    logger.info("✅ File deletion test passed - removed from both filesystem and Weaviate")

def main():
    """Test file creation and watcher indexing workflow"""
    
    global test_base
    
    # Create test base instance for all tests
    test_base = WatcherTestBase()
    
    try:
        # Setup: Initialize Weaviate connection and file watcher
        logger.info("Setting up test environment...")
        test_base.setup()
        
        file_path = test_file_creation()
        test_file_modification(file_path)
        moved_file_path = test_file_move(file_path)
        test_file_deletion(moved_file_path)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise
        
    finally:
        # Cleanup: Remove test files and Weaviate objects
        logger.info("Cleaning up test environment...")
        test_base.teardown()
        logger.info("Test completed")

if __name__ == "__main__":
    main() 