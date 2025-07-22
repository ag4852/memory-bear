"""
Template population utilities for Memory Bear.
"""

import logging
from typing import List, Optional
from utils.template_loader import load_template

# Get logger for this module
logger = logging.getLogger(__name__)


def populate_study_note_template(
    title: str,
    tags: Optional[List[str]] = None,
    recall_prompts: Optional[List[str]] = None,
    key_concepts: Optional[str] = None
) -> str:
    """
    Populate the study note template with provided content.
    
    Args:
        title: The title of the study note
        tags: Optional list of tags
        recall_prompts: Optional list of recall prompt strings
        key_concepts: Optional key concepts content (markdown formatted)
        
    Returns:
        Complete markdown content ready to write to file
    """
    logger.info(f"Populating template for note: '{title}'")
    
    # Load the template
    template = load_template("study_note_template.md")
    
    # Format tags (use as-is or empty list)
    formatted_tags = tags if tags else []
    
    # Format recall prompts as bulleted list or empty string
    formatted_prompts = "\n".join([f"- {prompt}" for prompt in recall_prompts]) if recall_prompts else ""
    
    # Use key concepts as-is or empty string
    formatted_concepts = key_concepts if key_concepts else ""
    
    # Populate template
    content = template.format(
        title=title,
        tags=formatted_tags,
        recall_prompts=formatted_prompts,
        key_concepts=formatted_concepts
    )
    
    logger.info(f"Template populated successfully for '{title}'")
    return content 