"""
Tool prompts for Memory Bear MCP server tools.
"""

from ..config import CONTENT_TAGS, SUBJECTS

CREATE_STUDY_NOTE_PROMPT = """
Create a structured study note from the current conversation for active recall and knowledge retention.

Call this when the user asks to create a study note from the conversation.

Args:
    title: Create a specific, descriptive title that captures the primary subject discussed
    subject: Choose ONE subject from: {subjects}
    tags: Choose content type tags from: {content_tags}
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
    subject: Filter by subject (optional)
             Available: {subjects}
             Examples: "physics", "math", "chemistry"
    tags: Filter by content type (optional)
          Available: {content_tags}
          Examples: ["lecture"], ["exam"], ["homework"]

Returns:
    List of relevant notes, each containing:
    - title: The note's title
    - subject: The note's subject
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
    subject: Subject you would use for the new content (optional)
             Available: {subjects}
    tags: Tags you would use for the new content (optional)
          Available: {content_tags}

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
    subject: Updated subject for the merged content
             Available: {subjects}
    tags: Combined tag list including existing relevant tags plus new ones
          Available: {content_tags}
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

CREATE_CARDS_FROM_NOTE_PROMPT = """
Create flashcards from recall prompts in a specific study note.

Call this when the user wants to create flashcards or study cards from recall prompts in their notes.

This tool will:
1. Search for an exact note title match first
2. Offer similar note suggestions if no exact match is found  
3. Check if cards already exist for the note (prevents duplicates)
4. Create flashcards from all bullet points under the "### Recall Prompts" section
5. Each bullet point becomes a separate flashcard for spaced repetition study

Args:
    note_title: Exact title of the note to create cards from
                Use the exact title as it appears in their notes
                Examples: "Physics - Quantum Mechanics", "Database Systems - Indexing"

Returns:
    Dictionary containing:
    - success: Boolean indicating if cards were created successfully
    - message: Descriptive message with details
    - cards_created: Number of cards created (when successful)
    - note_title: Title of the note processed
    - suggestions: List of similar note titles (when no exact match found)
    - next_action_hint: Guidance on how to study the new cards (when successful)

The user can then study the created cards using the get_cards tool with deck_title parameter.
"""

UPDATE_CARD_PROMPT = """
Update a flashcard after completing a review session with FSRS spaced repetition scheduling.

Call this to finalize each card review after the full learning conversation. This is the final step in the review workflow:

1. Present the card prompt to the user
2. Have a natural conversation about their understanding  
3. Based on their responses, evaluate their performance using FSRS difficulty scale
4. Show your rating assessment to the user (they can override if they disagree)
5. Call this tool to record the session and schedule the next review

The learning conversation should be thorough - ask follow-up questions, clarify concepts, and gauge their confidence level. Your difficulty assessment should reflect:
- Did they recall the concept immediately or struggle?
- Were they confident in their explanation or hesitant?
- Do they understand the underlying principles or just memorized facts?
- Can they apply the knowledge or only recite it?

Args:
    card_uuid: UUID of the reviewed card (from get_cards result)
    fsrs_rating: Your assessment of their performance:
                 1 = Again (failed to recall, significant confusion, needs immediate review)
                 2 = Hard (recalled with major difficulty, uncertain, partial understanding)
                 3 = Good (recalled correctly with some effort, mostly confident)  
                 4 = Easy (recalled effortlessly, fully confident, ready for advanced concepts)
    learning_summary: A reflection of the learning session that captures the user's mental model and what they learned.
                      Record both what's now in the user's memory about this topic AND what happened during the session.
                      Include: their current understanding level, how they think about the concept, what they learned/reinforced, areas of confidence vs struggle, their learning style preferences.
                      Examples: "User now has solid mental model of database indexing - thinks of it as 'book index for fast lookups' - reinforced B-tree structure understanding but struggled with clustered vs non-clustered distinction, learns best with concrete examples"
                               "Strengthened grasp of async concepts, built connection between promises and real-world waiting, but still needs practice with error handling patterns, responds well to step-by-step breakdowns"

Returns:
    Dictionary with update status, next review timing, and progress information
"""

def get_prompt(prompt_name: str) -> str:
    """Get formatted prompt with dynamic tags."""
    prompt_template = globals()[prompt_name]
    return prompt_template.format(
        content_tags=CONTENT_TAGS,
        subjects=SUBJECTS
    )