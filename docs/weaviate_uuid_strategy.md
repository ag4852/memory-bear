# File Watcher + Weaviate UUID Management Approach

## Core Strategy
Use file watcher events to determine operations, and use Weaviate's `file_path` property as the lookup key to find existing objects. No separate mapping file needed.

## Event-to-Operation Mapping

| File Watcher Event | Operation | Weaviate Action |
|-------------------|-----------|-----------------|
| `on_created` | New file added | `INSERT` new object with new UUID |
| `on_modified` | File content changed | `UPDATE` existing object (same UUID) |
| `on_moved` | File renamed/moved | `UPDATE` file_path only (same UUID) |
| `on_deleted` | File removed | `DELETE` object by UUID |

## Detailed Implementation

### 1. New File Created
```python
def on_created(self, event):
    # Parse markdown → Insert new object → Weaviate generates UUID
    memory.data.insert({"title": title, "content": content, "file_path": path, ...})
```

### 2. File Content Modified  
```python
def on_modified(self, event):
    # Find object: WHERE file_path = event.src_path
    # Update object: SAME UUID, new content
    memory.data.update(existing_uuid, {"title": new_title, "content": new_content, ...})
```

### 3. File Renamed/Moved
```python
def on_moved(self, event):
    # Find object: WHERE file_path = event.src_path (old path)
    # Update object: SAME UUID, SAME content, new file_path
    memory.data.update(existing_uuid, {"file_path": event.dest_path})
```

### 4. File Deleted
```python
def on_deleted(self, event):
    # Find object: WHERE file_path = event.src_path
    # Delete object completely
    memory.data.delete_by_id(existing_uuid)
```

## UUID Preservation Examples

**Scenario 1: User renames `ml-notes.md` → `machine-learning.md`**
- File watcher: `on_moved(src="ml-notes.md", dest="machine-learning.md")`
- Weaviate: Find UUID for "ml-notes.md" → Update file_path to "machine-learning.md"
- **Result**: Same UUID, same content, new path ✅

**Scenario 2: User edits content in existing file**
- File watcher: `on_modified(src="machine-learning.md")`  
- Weaviate: Find UUID for "machine-learning.md" → Update content
- **Result**: Same UUID, same path, new content ✅

## Key Benefits
- ✅ **Single source of truth**: Weaviate stores everything
- ✅ **UUID preservation**: Same file = same UUID across all operations
- ✅ **No external state**: No mapping files to maintain
- ✅ **Handles all scenarios**: Create, edit, rename, move, delete
- ✅ **Event-driven**: File operations directly trigger correct Weaviate operations

## Potential Drawbacks
- ⚠️ **Lookup cost**: Each operation requires Weaviate query by file_path
- ⚠️ **Edge cases**: Missed file watcher events could cause inconsistency
- ⚠️ **Query dependency**: Relies on file_path queries working reliably

## Conclusion
This approach treats Weaviate as both the vector database AND the file-to-UUID mapping system, eliminating the need for external tracking.