"""
File writing utilities for Memory Bear.
"""

import os
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


def write_study_note(filename: str, content: str) -> str:
    """
    Write study note content to a markdown file in the notes directory.
    
    Args:
        filename: The filename (without .md extension)
        content: Complete markdown content to write
        
    Returns:
        Full path to the created file
        
    Raises:
        Exception: If file writing fails
    """
    try:
        # Get notes directory from environment
        notes_dir = os.getenv("NOTES_DIR")
        
        # Build full file path
        file_path = os.path.join(notes_dir, f"{filename}.md")
        
        logger.info(f"Writing study note to: {file_path}")
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully created study note: {filename}.md")
        return file_path
        
    except Exception as e:
        logger.error(f"Error writing study note {filename}: {e}")
        raise e 