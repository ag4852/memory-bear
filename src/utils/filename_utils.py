"""
Filename creation and validation utilities for Memory Bear.
"""

import os
import re
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


def create_filename(title: str, notes_dir: str) -> str:
    """
    Format a title into a unique filesystem-safe filename.
    
    Args:
        title: The original title string
        notes_dir: Directory to check for filename conflicts
        
    Returns:
        Unique formatted filename (without .md extension)
        
    Process:
    1. Format title: spaces→underscores, remove special chars, lowercase, truncate to 30 chars
    2. Check for conflicts and add -1, -2, etc. if needed
    """
    if not title or not title.strip():
        base_filename = "Untitled"
    else:
        # Format title: strip → replace spaces → remove special chars → lowercase → truncate
        base_filename = re.sub(r'[^a-zA-Z0-9_-]', '', title.strip().replace(" ", "_")).lower()[:30]
        if not base_filename:
            base_filename = "Untitled"
    
    # Check for conflicts and find unique filename
    return get_unique_filename(base_filename, notes_dir)


def get_unique_filename(base_filename: str, notes_dir: str) -> str:
    """
    Validate a filename by adding -1, -2, etc. if conflicts exist.
    
    Args:
        base_filename: The desired filename (without .md extension)
        notes_dir: Directory to check for conflicts
        
    Returns:
        Unique filename (without .md extension)
    """
    # Check if base name is available
    file_path = os.path.join(notes_dir, f"{base_filename}.md")
    if not os.path.exists(file_path):
        return base_filename
    
    # Try sequential numbers
    counter = 1
    while True:
        candidate = f"{base_filename}_{counter}"
        file_path = os.path.join(notes_dir, f"{candidate}.md")
        if not os.path.exists(file_path):
            return candidate
        counter += 1 