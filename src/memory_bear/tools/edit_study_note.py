"""
Edit study note tool implementation for Memory Bear.
"""

import logging
import os
from typing import List, Optional, Dict, Any

from ..server import mcp
from ..config import NOTES_DIR
from .prompts import get_prompt

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def edit_study_note(
    file_path: str,
    title: str,
    tags: Optional[List[str]] = None,
    recall_prompts: Optional[List[str]] = None,
    key_concepts: Optional[str] = None
) -> Dict[str, Any]:
    """
    Edit an existing study note with new content.
    
    Args:
        file_path: Path to the existing note file
        title: The title of the study note
        tags: Optional list of tags
        recall_prompts: Optional list of recall prompt strings
        key_concepts: Optional key concepts content (markdown formatted)
        
    Returns:
        Dictionary with success status and file path
    """
    get_prompt("EDIT_STUDY_NOTE_PROMPT")
    
    try:
        logger.info(f"Editing study note: '{title}' at {file_path}")
        
        # Import utility functions
        from ..utils.templates import populate_study_note_template
        from ..utils.files import write_study_note
        
        # Extract filename from file_path
        filename = os.path.splitext(os.path.basename(file_path))[0]
        
        # Populate template with new content (LLM provides merged content)
        content = populate_study_note_template(
            title=title,
            tags=tags,
            recall_prompts=recall_prompts,
            key_concepts=key_concepts
        )
        
        # Write file (overwrites existing)
        final_path = write_study_note(filename, content)
        
        logger.info(f"Successfully edited study note: {filename}.md")
        
        return {
            "success": True,
            "file_path": final_path,
            "action": "edited"
        }
        
    except Exception as e:
        logger.error(f"Error editing study note '{title}': {e}")
        return {
            "success": False,
            "error": str(e)
        }