import os
import time
import logging
import shutil
import subprocess
import psutil
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from weaviate.classes.query import Filter
from pathlib import Path

# Load environment variables
load_dotenv(find_dotenv())

# Set up logging configuration for this module
from memory_bear.utils.logging import setup_logging
setup_logging("INFO")

logger = logging.getLogger(__name__)

# Import database functions
from memory_bear.database import get_weaviate_client, get_or_create_collection


class WatcherTestBase:
    """
    Base class for watcher testing with common setup, teardown, and utilities.
    """

    def __init__(self):
        """
        Initialize the test base with Weaviate connection.
        """
        self.client = None
        self.collection = None
        self.server_process = None

        self.initial_obj_count = 0

        logger.info("WatcherTestBase initialized")

    def setup(self):
        """
        Set up the test environment with Weaviate connection and validation.
        """
        logger.info("Setting up WatcherTestBase...")

        try:
            # Start server
            self.start_server()
            
            # Connect to Weaviate
            logger.info("Connecting to Weaviate...")
            self.client = get_weaviate_client()
            self.collection = get_or_create_collection(self.client)
            logger.info("Weaviate connection established successfully")
            
            # Get initial object count for comparison
            try:
                response = self.collection.aggregate.over_all()
                self.initial_obj_count = response.total_count
                logger.info(f"Initial collection object count: {self.initial_obj_count}")
            except Exception as e:
                logger.warning(f"Could not get initial object count: {e}")
                self.initial_obj_count = 0
            
            logger.info("Setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    def teardown(self):
        """
        Clean up all test artifacts and close connections.
        """
        logger.info("Starting teardown cleanup...")
        
        # 1. Delete all files from NOTES_DIR (but preserve the directory)
        notes_dir = os.getenv('NOTES_DIR')
        try:
            logger.info(f"Deleting all files from {notes_dir}")
            # Delete all files and subdirectories, but keep the directory itself
            for item in Path(notes_dir).iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info(f"Successfully cleaned all files from {notes_dir}")
        except Exception as e:
            logger.error(f"Failed to clean notes directory {notes_dir}: {e}")
        
        # 2. Delete all objects from the test collection (preserves collection)
        if self.collection:
            try:
                logger.info("Deleting all objects from test collection...")
                self.collection.data.delete_many(
                    where=Filter.by_property("file_path").like("*")
                )
                logger.info("Successfully deleted all objects from test collection")
            except Exception as e:
                logger.error(f"Failed to delete objects from test collection: {e}")
        
        # 3. Close Weaviate connection
        if self.client:
            try:
                logger.info("Closing Weaviate client connection...")
                self.client.close()
                logger.info("Weaviate connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing Weaviate client: {e}")
        
        logger.info("Teardown cleanup completed")

    def inspect_collection(self, limit=10):
        """
        Inspect the current state of the collection for debugging purposes.
        
        Args:
            limit (int): Maximum number of objects to retrieve (default: 10)
            
        Returns:
            dict: Collection inspection results containing object count, sample objects, and metadata
        """
        if self.collection is None:
            logger.warning("Collection not initialized - cannot inspect")
            return {"error": "Collection not initialized"}
        
        try:
            # Get total object count
            response = self.collection.aggregate.over_all()
            total_count = response.total_count
            
            # Get sample objects
            objects = []
            if total_count > 0:
                query_result = self.collection.query.fetch_objects(limit=limit)
                for obj in query_result.objects:
                    objects.append({
                        "uuid": str(obj.uuid),
                        "properties": obj.properties
                    })
            
            inspection_result = {
                "collection_name": self.collection.name,
                "total_objects": total_count,
                "sample_objects": objects,
                "sample_count": len(objects)
            }
            
            logger.info(f"Collection inspection - Total objects: {total_count}")
            
            return inspection_result
            
        except Exception as e:
            logger.error(f"Failed to inspect collection: {e}")
            return {"error": str(e)}

    def create_test_file(self, filename, full_content):
        """
        Create a test file in the notes directory.
        
        Args:
            filename (str): Name of the file to create (without extension)
            full_content (str): Complete markdown content to write to the file (including frontmatter)
            
        Returns:
            str: Full path to the created file
            
        Raises:
            Exception: If file creation fails
        """
        # Get notes directory from environment
        notes_dir = os.getenv('NOTES_DIR')
        
        # Build full file path with .md extension
        file_path = os.path.join(notes_dir, f"{filename}.md")
        
        try:
            # Write complete markdown content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            logger.info(f"Successfully created test file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to create test file {file_path}: {e}")
            raise

    def modify_test_file(self, file_path, template_name="modified_test_note.md"):
        """
        Modify a test file using a template.
        
        Args:
            file_path (str): Path to the file to modify
            template_name (str): Name of the template file to use (default: "modified_test_note.md")
            
        Returns:
            str: Path to the modified file
            
        Raises:
            Exception: If file modification fails
        """
        try:
            # Get template path
            template_path = os.path.join(os.path.dirname(__file__), template_name)
            
            # Read template content
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Write content to target file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully modified test file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to modify test file {file_path}: {e}")
            raise

    def poll_for_object(self, file_path, should_exist=True, condition_func=None, timeout=10):
        """
        Poll for an object in Weaviate by file_path until conditions are met.
        
        Args:
            file_path (str): The file path to search for
            should_exist (bool): Whether the object should exist (True) or not exist (False)
            condition_func (callable): Optional function to check specific object properties
            timeout (int): Maximum seconds to poll (default: 10)
            
        Returns:
            Object if should_exist=True and found, None if should_exist=False and not found
            
        Raises:
            Exception: If polling times out without meeting conditions
        """
        logger.info(f"Polling for object: {file_path}, should_exist={should_exist}")
        
        for attempt in range(timeout):
            results = self.collection.query.fetch_objects(
                filters=Filter.by_property("file_path").equal(file_path),
                limit=10  # To catch potential duplicates
            )
            
            if should_exist:
                if results.objects:
                    # Check for duplicates (should never happen with unique file_path)
                    assert len(results.objects) == 1, f"Expected 1 object, found {len(results.objects)} for file_path: {file_path}"
                    
                    # Object exists, check condition if provided
                    if condition_func is None or condition_func(results.objects[0]):
                        logger.info(f"Found object after {attempt + 1} attempts")
                        return results.objects[0]
            else:
                # Deletion case - object should not exist
                if not results.objects:
                    logger.info(f"Object deleted after {attempt + 1} attempts")
                    return None
            
            time.sleep(1)
        
        # Handle timeout
        raise Exception(f"Polling timed out after {timeout} seconds - object not found or condition not met for {file_path}")
        
    def validate_object(self, actual_object, expected_data, skip_properties=None):
        """
        Validate an object from Weaviate against expected data.
        
        Args:
            actual_object: The object retrieved from Weaviate
            expected_data: Dictionary of expected properties
            skip_properties: List of property names to skip validation for
        """
        skip_properties = skip_properties or []
        actual_props = actual_object.properties
        
        # Core properties to validate
        core_properties = ['title', 'subject', 'content', 'file_path', 'tags', 'created_at', 'updated_at']
        
        # Validate core properties
        for prop in core_properties:
            if prop not in skip_properties and prop in expected_data:
                assert actual_props.get(prop) == expected_data[prop], \
                    f"{prop.replace('_', ' ').title()} mismatch: expected '{expected_data[prop]}', got '{actual_props.get(prop)}'"
        
        # UUID validation (automatic if present in expected_data)
        if 'uuid' in expected_data and 'uuid' not in skip_properties:
            assert str(actual_object.uuid) == str(expected_data['uuid']), \
                f"UUID mismatch: expected {expected_data['uuid']}, got {actual_object.uuid}"
        
        logger.info("✅ All validations passed!")
        
    def stop_server(self):
        """
        Stop the running server process.
        
        Raises:
            Exception: If server process not found
        """
        logger.info("Stopping server process...")
        
        # First try to stop our stored server process if it exists
        if self.server_process and self.server_process.poll() is None:
            try:
                logger.info(f"Stopping stored server process (PID: {self.server_process.pid})")
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                logger.info("Server stopped successfully")
                return
            except Exception as e:
                logger.warning(f"Could not stop stored server process: {e}")
        
        # Fallback: search for server process by command line
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline_list = proc.info['cmdline']
                if cmdline_list is None:
                    continue
                    
                cmdline = ' '.join(cmdline_list) if isinstance(cmdline_list, list) else str(cmdline_list)
                logger.debug(f"Checking process {proc.info['pid']}: {cmdline}")
                
                if 'main.py' in cmdline and '--test' in cmdline:
                    logger.info(f"Found server process (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait(timeout=10)
                    logger.info("Server stopped successfully")
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
        raise Exception("Server process not found")

    def start_server(self):
        """
        Start the server process and wait for initialization.
        
        Raises:
            Exception: If server fails to start
        """
        logger.info("Starting server process...")
        
        # Get the project root directory (3 levels up from this file)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Start server process using module execution to handle relative imports
        process = subprocess.Popen([
            'python', '-m', 'src.memory_bear.main', '--test'
        ], cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to initialize
        time.sleep(5)
        
        if process.poll() is None:
            logger.info(f"Server started successfully (PID: {process.pid})")
            self.server_process = process
        else:
            stdout, stderr = process.communicate()
            raise Exception(f"Failed to start server. Stdout: {stdout.decode()}, Stderr: {stderr.decode()}")
        