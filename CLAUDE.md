# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
uv sync

# Install in development mode
uv sync --dev
```

### Running the Application
```bash
# Run production MCP server
memory-bear --server

# Run test server (uses TEST_NOTES_DIR)
memory-bear --test

# Run directly via module
python -m memory_bear.main --server
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/watcher/test_sync_workflow.py

# Run with verbose output
python -m pytest -v tests/watcher/
```

## Architecture Overview

**Memory Bear** is an MCP server that provides intelligent note management through real-time file monitoring and vector database integration. The system watches a markdown notes directory, automatically indexes content into Weaviate for semantic search, and exposes MCP tools for searching and creating notes.

### Core Components

1. **MCP Server** (`server.py`): FastMCP-based server managing Weaviate connections and coordinating components
2. **File Watcher** (`watcher/`): Real-time monitoring using watchdog with offline sync capabilities
3. **Database Layer** (`database/`): Weaviate client management and markdown CRUD operations
4. **MCP Tools** (`tools/`): Search notes and create study note implementations
5. **Utilities** (`utils/`): Shared functionality for files, templates, markdown parsing, and logging

### Data Flow
- File changes → Watchdog events → MarkdownOperations → Weaviate updates
- MCP requests → Semantic search → Formatted results
- Note creation → Template population → File written → Auto-indexed

## Configuration

### Required Environment Variables
```bash
HUGGINGFACE_API_KEY="your_key"      # For embeddings
NOTES_DIR="/path/to/notes"          # Production notes directory
TEST_NOTES_DIR="/path/to/test"      # Test notes directory
SUBJECTS="list,of,your,own,subjects"
CONTENT_TAGS="lecture,homework,exam,concepts,research"
LOG_LEVEL="INFO"
```

### Dependencies
- **weaviate-client**: Vector database operations
- **mcp[cli]**: MCP server framework  
- **watchdog**: File system monitoring
- **python-frontmatter**: Markdown frontmatter parsing

## Key Development Patterns

### File Operations
- All file operations go through `utils/files.py` utilities
- Markdown processing uses frontmatter parsing via `utils/markdown.py`
- File watcher handles create/modify/delete/move events with sync support

### Database Operations
- Use `database/client.py` for Weaviate connection management
- All markdown CRUD goes through `database/utils.py` MarkdownOperations
- Collections managed via `database/collections.py`

### Testing Approach
- Uses integration tests focusing on sync workflow scenarios
- Test base classes in `tests/watcher/` provide reusable infrastructure
- Tests validate offline sync, file operations, and database consistency

### Error Handling
- Centralized logging configuration in `utils/logging.py`
- Server continues operation if file watcher initialization fails
- Graceful shutdown handling for Weaviate connections

## Template System

Notes are created using markdown templates with frontmatter:
- Templates stored in `src/memory_bear/templates/`
- Populated via `utils/templates.py` with metadata injection
- Automatic tagging and categorization through frontmatter

## MCP Tool Development

When adding new MCP tools:
1. Implement in `tools/` directory following existing patterns
2. Add tool prompts to `tools/prompts.py`
3. Register in `server.py` MCP server setup
4. Use async implementations for non-blocking operations