import frontmatter
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


def parse_md_file(file_path: str) -> Dict:
    """
    Parse a markdown file to extract title, tags, content, and file metadata.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Dictionary containing title, tags, content, file_path, created_at, and updated_at
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    # Extract metadata
    title = post.metadata.get('title')
    tags = post.metadata.get('tags', [])
    content = post.content
    
    # Fallback: use filename if no title in frontmatter
    if not title:
        title = os.path.splitext(os.path.basename(file_path))[0]
    
    # Get file timestamps with timezone info
    file_stat = os.stat(file_path)
    created_at = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)  
    updated_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
    
    return {
        'title': title,
        'tags': tags,
        'content': content,
        'file_path': file_path,
        'created_at': created_at,
        'updated_at': updated_at
    } 