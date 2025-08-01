"""
Create study note tool implementation for Memory Bear.
"""

import logging
from typing import List, Optional, Dict, Any

from ..server import mcp
from ..config import NOTES_DIR
from .prompts import get_prompt

# Set up logging
logger = logging.getLogger(__name__)

@mcp.tool()
async def create_study_note(
    title: str,
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None,
    recall_prompts: Optional[List[str]] = None,
    key_concepts: Optional[str] = None
) -> Dict[str, Any]:
    get_prompt("CREATE_STUDY_NOTE_PROMPT")
    try:
        logger.info(f"Creating study note with title: '{title}'")
        
        # Import utility functions
        from ..utils.files import create_filename, write_study_note
        from ..utils.templates import populate_study_note_template
        
        # Validate title and get unique filename
        filename = create_filename(title, NOTES_DIR)
        
        # Populate template with content
        content = populate_study_note_template(
            title=title,
            subject=subject,
            tags=tags,
            recall_prompts=recall_prompts,
            key_concepts=key_concepts
        )
        
        # Write file to notes directory
        file_path = write_study_note(filename, content)
        
        logger.info(f"Successfully created study note: {filename}.md")
        
        return {
            "success": True,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error creating study note '{title}': {e}")
        return {
            "success": False,
            "file_path": "",
            "error": str(e)
        } 