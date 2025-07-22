"""
Template loading utility for Memory Bear.
"""

import os
import logging

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