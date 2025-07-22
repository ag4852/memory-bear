"""
Tool prompts for Memory Bear MCP server tools.
"""

import os

# Load tags from environment variables once at module level
CONTENT_TAGS = os.getenv("CONTENT_TAGS", "").split(",")
CLASS_TAGS = os.getenv("CLASS_TAGS", "").split(",") if os.getenv("CLASS_TAGS") else []

CREATE_STUDY_NOTE_PROMPT = """
Create a structured study note from the current conversation for active recall and knowledge retention.

Call this when the user asks to create a study note from the conversation.

Args:
    title: Create a specific, descriptive title that captures the primary subject discussed
    tags: Choose 1 subject tag and 1 content type tag from the lists below.
        Content types: {content_tags}
        Subject tags: {class_tags}
    recall_prompts: Create 3-5 concise topic phrases that capture key concepts discussed, no questions. 
        Examples: "Pins vs. locks in buffer management", "LRU and nested loop joins", "Clustering vs. secondary indexes"
    key_concepts: Extract core explanations using hierarchical bullet structure. Use **bold** sparingly, only for main headers and key concepts. No title case. Use inline LaTeX ($\to$) for arrows and any math. Structure: **main header** → key concept (bold only when very important): explanation → sub-bullets with details → non-bold sub-concepts. Example: "**Storage and buffer management**\n- **Blocks:** Units of storage allocation\n    - Groups of bytes (4KB-16KB)\n    - Blocks on disk $\to$ memory buffers\n- **Buffer operations**\n    - Pins: Prevent eviction while in use\n    - Locks: Control concurrent access"

Keep total response under 500 characters.

Returns:
    Dictionary containing:
    - success: Boolean indicating if note was created successfully
    - file_path: Path to the created note file
"""

SEARCH_NOTES_PROMPT = """
Call this when the user asks questions about their coursework, wants to review previous learning, or needs to find specific information from their notes.

This tool performs semantic search across all indexed markdown notes, finding content
that matches the meaning and context of the search query. Results are ranked by 
relevance and limited to the most pertinent notes.

Args:
    query: What you're looking for in their notes
           Examples: "linear algebra eigenvalues", "database indexing strategies"
    tags: Filter by content type or subject (optional)
          Available: {content_tags} (content) or {class_tags} (subjects)
          Examples: ["lecture"], ["cs101", "exam"], ["homework", "math201"]

Returns:
    List of relevant notes, each containing:
    - title: The note's title
    - content: The note's content (may be truncated if very long)
    - file_path: Path to the original markdown file
    - tags: List of tags associated with the note
    - confidence_score: Relevance score (0.0 to 1.0, higher = more relevant)
    
The search returns a maximum of 3 most relevant notes to avoid overwhelming context.
"""

def get_prompt(prompt_name: str) -> str:
    """Get formatted prompt with dynamic tags."""
    prompt_template = globals()[prompt_name]
    return prompt_template.format(
        content_tags=CONTENT_TAGS,
        class_tags=CLASS_TAGS
    )