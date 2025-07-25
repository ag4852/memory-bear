"""
Tool prompts for Memory Bear MCP server tools.
"""

from ..config import CONTENT_TAGS, CLASS_TAGS

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

FIND_BEST_MATCH_PROMPT = """
Find the top semantic match for a topic to determine if an existing note should be edited or a new one created.

Call this when the user wants to create study content and you need to check if similar content already exists that could be enhanced instead of creating a duplicate.

This tool searches for the single most semantically similar note and calculates a match score considering:
- Semantic similarity (primary factor)
- Tag overlap between existing and new content  
- Note length (shorter notes are better edit candidates)

Args:
    query: The topic or subject matter you're checking for matches
           Examples: "linear algebra matrix operations", "database transaction isolation levels"
    tags: Tags you would use for the new content (optional)
          Available: {content_tags} (content) or {class_tags} (subjects)

Returns:
    Dictionary containing:
    - should_edit: Boolean indicating if you should edit the existing note (score ≥ 0.6)
    - existing_note: Details of the top match including full content, file_path, and scores
    - final_score: Calculated match score (0.0 to 1.0)
    - decision_reason: Explanation of the edit/create decision

If should_edit is True, use the existing_note content to generate contextual additions.
If should_edit is False, the existing_note is still provided for context to avoid content duplication.
"""

EDIT_STUDY_NOTE_PROMPT = """
Edit an existing study note by merging new content with existing content intelligently.

Call this when find_best_match indicates should_edit=True and you need to enhance an existing note rather than create a new one.

You have access to the full existing note content and should:
1. Merge new concepts with existing key_concepts section (preserve existing, add new)
2. Combine recall_prompts (avoid duplicates, add complementary prompts)  
3. Merge tags (keep existing relevant tags, add new ones)
4. Update title if the new content significantly expands the scope

Args:
    file_path: Path to the existing note (from find_best_match result)
    title: Updated title that reflects merged content scope
    tags: Combined tag list including existing relevant tags plus new ones
          Available: {content_tags} (content) or {class_tags} (subjects)
    recall_prompts: Merged list of recall prompts (existing + new, no duplicates)
    key_concepts: Enhanced key_concepts section combining existing and new content
                 Use same hierarchical structure as create_study_note

Provide complete sections that will replace the existing content entirely.
The file watcher will automatically handle timestamps and database updates.

Returns:
    Dictionary containing:
    - success: Boolean indicating if note was edited successfully  
    - file_path: Path to the updated note file
    - action: "edited" to distinguish from create operations
"""

def get_prompt(prompt_name: str) -> str:
    """Get formatted prompt with dynamic tags."""
    prompt_template = globals()[prompt_name]
    return prompt_template.format(
        content_tags=CONTENT_TAGS,
        class_tags=CLASS_TAGS
    )