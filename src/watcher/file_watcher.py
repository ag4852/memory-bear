"""
File watcher implementation using watchdog to monitor markdown file changes.
"""

import os
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from database.utils import MarkdownOperations

# Get logger for this module
logger = logging.getLogger(__name__)


class FileWatcherHandler(FileSystemEventHandler):
    """
    File system event handler for markdown files.
    Handles file creation and modification events and indexes/updates files in Weaviate.
    """
    
    def __init__(self, memory_collection):
        """
        Initialize the file watcher handler.
        
        Args:
            memory_collection: Weaviate Memory collection instance
        """
        super().__init__()
        self.memory_collection = memory_collection
        self.md_ops = MarkdownOperations(memory_collection)
    
    def should_process_event(self, event) -> bool:
        """
        Check if this file event should be processed.
        
        Args:
            event: FileSystemEvent from watchdog
            
        Returns:
            True if event should be processed, False otherwise
        """
        # Skip directory events
        if event.is_directory:
            return False
        
        path = Path(event.src_path)
        
        # Only process .md files
        if path.suffix.lower() != '.md':
            return False
        
        # Skip hidden files (starting with .)
        if path.name.startswith('.'):
            return False
        
        # Skip temporary files
        temp_extensions = {'.tmp', '.swp', '.temp'}
        if any(path.name.endswith(ext) for ext in temp_extensions):
            return False
        
        # Skip editor temporary files (common patterns)
        if path.name.startswith('~') or path.name.endswith('~'):
            return False
        
        return True
    
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event: FileSystemEvent from watchdog
        """
        # Single check for all filtering logic
        if not self.should_process_event(event):
            logger.debug(f"Skipping event: {event.src_path}")
            return
        
        file_path = event.src_path
        logger.info(f"New markdown file detected: {file_path}")
        
        # Use MarkdownOperations to handle the indexing
        success = self.md_ops.index_file(file_path)
        
        if not success:
            logger.error(f"Failed to index new file: {file_path}")

    def on_modified(self, event):
        """
        Handle file modification events.
        
        Args:
            event: FileSystemEvent from watchdog
        """
        # Single check for all filtering logic
        if not self.should_process_event(event):
            logger.debug(f"Skipping event: {event.src_path}")
            return
        
        file_path = event.src_path
        logger.info(f"Modified markdown file detected: {file_path}")
        
        # Use MarkdownOperations to handle the update
        success = self.md_ops.update_file(file_path)
        
        if not success:
            logger.error(f"Failed to update modified file: {file_path}")

    def on_moved(self, event):
        """
        Handle file move/rename events.
        
        When a file is moved or renamed, we need to update the file_path property
        in Weaviate while preserving the same UUID and all other content.
        
        Args:
            event: FileSystemEvent from watchdog (has src_path and dest_path)
        """
        # TODO: Check if we should process both source and destination paths (not sure if this is needed)
        if not self.should_process_event(event):
            logger.debug(f"Skipping move event: {event.src_path}")
            return
        
        old_path = event.src_path
        new_path = event.dest_path
        logger.info(f"File move detected: {old_path} → {new_path}")
        
        # Use MarkdownOperations to handle the move
        success = self.md_ops.move_file(old_path, new_path)
        
        if not success:
            logger.error(f"Failed to move file: {old_path} → {new_path}")

    def on_deleted(self, event):
        """
        Handle file deletion events.
        
        When a file is deleted, we need to remove the corresponding object
        from Weaviate to keep the collection in sync with the file system.
        
        Args:
            event: FileSystemEvent from watchdog
        """
        if not self.should_process_event(event):
            logger.debug(f"Skipping delete event: {event.src_path}")
            return
        
        file_path = event.src_path
        logger.info(f"File deletion detected: {file_path}")
        
        # Use MarkdownOperations to handle the deletion
        success = self.md_ops.delete_file(file_path)
        
        if not success:
            logger.error(f"Failed to delete file: {file_path}")


class WatcherManager:
    """
    Manages the file watcher lifecycle and configuration.
    """
    
    def __init__(self, memory_collection):
        """
        Initialize the watcher manager.
        
        Args:
            memory_collection: Weaviate Memory collection instance
        """
        self.memory_collection = memory_collection
        self.observer = None
        self.handler = FileWatcherHandler(memory_collection)
    
    def start(self):
        """
        Start the file watcher.
        """
        
        # Get and validate notes directory
        notes_dir = os.getenv("NOTES_DIR")
        if not notes_dir:
            raise ValueError("NOTES_DIR environment variable not set")
        
        if not os.path.exists(notes_dir):
            raise FileNotFoundError(f"Notes directory does not exist: {notes_dir}")
        
        if not os.path.isdir(notes_dir):
            raise NotADirectoryError(f"NOTES_DIR is not a directory: {notes_dir}")
        
        # Create observer and set up recursive watching of the notes directory
        self.observer = Observer()
        self.observer.schedule(self.handler, notes_dir, recursive=True)
        self.observer.start()
        logger.info(f"File watcher started, monitoring: {notes_dir}")
    
    def stop(self):
        """
        Stop the file watcher.
        """
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("File watcher stopped")
    
    def is_running(self) -> bool:
        """
        Check if the file watcher is currently running.
        
        Returns:
            True if watcher is running, False otherwise
        """
        return self.observer is not None and self.observer.is_alive() 