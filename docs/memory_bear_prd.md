# Memory-Bear MCP Server - Product Requirements Document

## 1. Overview & Vision

**Memory-Bear** is a local-first knowledge management MCP server that enables AI assistants to search and create notes in a user's personal markdown collection. It prioritizes simplicity and treats a directory of unstructured markdown files as the single source of truth.

### 1.1. Core User Flow

1. **Passive Indexing:** User creates/edits `.md` files → file watcher detects changes → content gets indexed in local vector database
2. **Active Retrieval:** User asks AI questions → AI calls `search_notes` tool → relevant notes returned as context
3. **Note Creation:** User asks AI to create structured study notes → AI calls `create_study_note` tool → new formatted note saved to directory

## 2. Technical Architecture

### 2.1. Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **MCP Server** | FastAPI | Handles tool requests from AI clients |
| **MCP Definition** | FastMCP | Defines available tools |
| **Vector Database** | Weaviate (built-in embeddings) | Stores and searches note embeddings |
| **File Watcher** | Watchdog | Monitors notes directory for changes |
| **Markdown Parser** | python-frontmatter | Extracts metadata and content |

### 2.2. File System Structure

```
/Users/me/MyNotes/          # User's notes directory (configurable)
├── project-ideas.md
├── cooking-recipes.md
├── meeting-notes-2025.md
└── ...

/Users/me/.memory-bear/     # Application data directory
├── db/
│   └── chromadb.sqlite3    # Vector database
└── templates/
    └── study_note_template.md
```

### 2.3. Data Flow

```
File Change → File Watcher → Markdown Parser → Weaviate Indexing
                                                      ↑
User Question → AI Client → MCP Server → Vector Search ↓ → Response
```

## 3. MCP Tools

### 3.1. search_notes

```python
def search_notes(query: str, tags: Optional[list[str]] = None) -> list[dict]:
    """
    Searches user's knowledge base for notes relevant to the query.
    
    Args:
        query: Natural language search query
        tags: Optional list of tags to filter results (AND logic)
    
    Returns:
        List of note objects with title, content, path, confidence_score
    """
```

**Tool Triggering:** Reactive only - LLM decides when to use based on tool description and user phrasing patterns.

### 3.2. create_study_note

```python
def create_study_note(
    title: str,
    recall_prompts: list[str],
    key_concepts: str,
    tags: list[str]
):
    """
    Creates a structured study note optimized for active recall.
    Uses formatting template to ensure consistency.
    """
```

**Template System:** Uses separate `study_note_template.md` file for formatting, keeping tool descriptions clean and templates easily editable.

## 4. Implementation Details

### 4.1. Note Format

```markdown
---
title: Note Title
tags: [tag1, tag2]
---

### Recall Prompts
- Brief topic phrases for active recall

---

### Key Concepts
* Detailed explanations with markdown formatting
```

### 4.2. Search Strategy

- **Semantic Search:** ChromaDB cosine similarity between query and note vectors
- **Results Limit:** Maximum 3 notes returned to prevent context overflow
- **Tag Filtering:** AND logic (note must contain all specified tags)

### 4.3. Indexing Pipeline

1. File watcher detects `.md` file changes
2. Markdown parser extracts frontmatter (title, tags) and content
3. ChromaDB generates embedding for content
4. Vector stored with metadata (title, tags, file_path)

## 5. MVP Scope

### 5.1. Included Features
- Basic file watching and indexing
- Semantic search with tag filtering
- Study note creation with templates
- Simple markdown frontmatter support

### 5.2. Future Iterations
- File editing delay/detection
- File rename/deletion handling
- Proactive search behavior
- Advanced ID management for updates
- Multiple note templates