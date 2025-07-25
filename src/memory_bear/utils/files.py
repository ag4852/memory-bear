"""
File utilities for Memory Bear.
Combines filename creation and file writing functionality.
"""

import os
import re
import logging
from typing import List
from ..config import NOTES_DIR

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
        # Build full file path using centralized config
        file_path = os.path.join(NOTES_DIR, f"{filename}.md")
        
        logger.info(f"Writing study note to: {file_path}")
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Successfully created study note: {filename}.md")
        return file_path
        
    except Exception as e:
        logger.error(f"Error writing study note {filename}: {e}")
        raise e


def calculate_match_score(
    semantic_score: float, 
    existing_tags: List[str], 
    new_tags: List[str], 
    content: str
) -> float:
    """
    Calculate match score for determining edit vs create decision.
    
    Args:
        semantic_score: Semantic similarity score from Weaviate (0.0-1.0)
        existing_tags: Tags from existing note
        new_tags: Tags for new content
        content: Content of existing note
        
    Returns:
        Final weighted score (0.0-1.0) for edit decision
        
    Formula:
        final_score = semantic_similarity * 0.6 + tag_overlap_ratio * 0.3 + length_factor * 0.1
    """
    try:
        # Calculate word count from content
        word_count = len(content.split()) if content else 0
        
        # Tag overlap calculation
        existing_set = set(existing_tags) if existing_tags else set()
        new_set = set(new_tags) if new_tags else set()
        shared_tags = existing_set & new_set
        all_tags = existing_set | new_set
        tag_overlap_ratio = len(shared_tags) / len(all_tags) if all_tags else 0
        
        # Length factor (shorter notes are better edit candidates)
        if word_count < 200:
            length_factor = 0.1
        elif word_count < 400:
            length_factor = 0.05
        else:
            length_factor = 0.0
            
        # Final weighted score
        final_score = semantic_score * 0.6 + tag_overlap_ratio * 0.3 + length_factor * 0.1
        
        logger.debug(f"Match score calculation: semantic={semantic_score:.3f}, "
                    f"tag_overlap={tag_overlap_ratio:.3f}, length_factor={length_factor:.3f}, "
                    f"final={final_score:.3f}")
        
        return final_score
        
    except Exception as e:
        logger.error(f"Error calculating match score: {e}")
        return 0.0