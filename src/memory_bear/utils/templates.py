"""
Template utilities for Memory Bear.
Combines template loading and population functionality.
"""

import os
import logging
from typing import List, Optional

# Get logger for this module
logger = logging.getLogger(__name__)


def load_template(template_name: str) -> str:
    """
    Load a template file from the src/templates directory.
    
    Args:
        template_name: Name of the template file (e.g., "study_note_template.md")
        
    Returns:
        Template content as string
    """
    try:
        # Build absolute path to template file
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to get to src/, then into templates/
        src_dir = os.path.dirname(current_dir)
        template_path = os.path.join(src_dir, "templates", template_name)
        
        logger.info(f"Loading template: {template_path}")
        
        # Read template content
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Successfully loaded template: {template_name}")
        return content
        
    except Exception as e:
        logger.error(f"Error loading template {template_name}: {e}")
        raise e


def populate_study_note_template(
    title: str,
    subject: Optional[str] = None,
    tags: Optional[List[str]] = None,
    recall_prompts: Optional[List[str]] = None,
    key_concepts: Optional[str] = None
) -> str:
    """
    Populate the study note template with provided content.
    
    Args:
        title: The title of the study note
        subject: Optional subject (defaults to "General")
        tags: Optional list of tags
        recall_prompts: Optional list of recall prompt strings
        key_concepts: Optional key concepts content (markdown formatted)
        
    Returns:
        Complete markdown content ready to write to file
    """
    logger.info(f"Populating template for note: '{title}'")
    
    # Load the template
    template = load_template("study_note_template.md")
    
    # Format subject (use provided or default to "General")
    formatted_subject = subject if subject else "General"
    
    # Format tags (use as-is or empty list)
    formatted_tags = tags if tags else []
    
    # Format recall prompts as bulleted list or empty string
    formatted_prompts = "\n".join([f"- {prompt}" for prompt in recall_prompts]) if recall_prompts else ""
    
    # Use key concepts as-is or empty string
    formatted_concepts = key_concepts if key_concepts else ""
    
    # Populate template
    content = template.format(
        title=title,
        subject=formatted_subject,
        tags=formatted_tags,
        recall_prompts=formatted_prompts,
        key_concepts=formatted_concepts
    )
    
    logger.info(f"Template populated successfully for '{title}'")
    return content