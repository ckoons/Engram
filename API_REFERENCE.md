# Engram API Reference

## Core API

### `engram.Memory`

The main class for all memory operations.

```python
class Memory:
    def __init__(self, namespace: str = "default") -> None
    async def store(self, content: str, **metadata) -> str
    async def recall(self, query: str, limit: int = 5) -> List[MemoryItem]
    async def context(self, query: str, limit: int = 10) -> str
```

### `engram.MemoryItem`

Data class returned by recall operations.

```python
@dataclass
class MemoryItem:
    id: str                    # Unique identifier
    content: str              # The stored text
    timestamp: datetime       # When stored
    metadata: Dict[str, Any]  # Additional data
    relevance: float = 1.0    # Search relevance score
```

## Method Details

### `Memory.__init__(namespace="default")`

Initialize a new Memory instance.

**Parameters:**
- `namespace` (str): Logical grouping for memories. Defaults to "default".

**Example:**
```python
# Default namespace
mem = Memory()

# Custom namespace
project_mem = Memory("project_alpha")
```

### `await Memory.store(content, **metadata)`

Store content in memory with optional metadata.

**Parameters:**
- `content` (str): The text to store. Required.
- `**metadata`: Optional keyword arguments stored with the memory.

**Common metadata keys:**
- `tags` (List[str]): Searchable tags
- `category` (str): Memory category
- `importance` (float): Priority 0.0-1.0
- `source` (str): Where this came from

**Returns:**
- `str`: Unique memory ID

**Example:**
```python
# Simple storage
memory_id = await mem.store("User prefers vim")

# With metadata
memory_id = await mem.store(
    "Production database is PostgreSQL",
    tags=["infrastructure", "database"],
    category="technical",
    importance=0.9
)
```

### `await Memory.recall(query, limit=5)`

Search for memories similar to the query.

**Parameters:**
- `query` (str): Search terms. Uses semantic similarity.
- `limit` (int): Maximum results. Default: 5.

**Returns:**
- `List[MemoryItem]`: Memories sorted by relevance.

**Example:**
```python
# Find memories about databases
memories = await mem.recall("database configuration")

# Get more results
all_configs = await mem.recall("config", limit=20)

# Process results
for memory in memories:
    print(f"[{memory.relevance:.2f}] {memory.content}")
    if memory.metadata.get("importance", 0) > 0.8:
        print("  ^^ High importance!")
```

### `await Memory.context(query, limit=10)`

Get formatted context string for use in prompts.

**Parameters:**
- `query` (str): Topic requiring context
- `limit` (int): Max memories to include. Default: 10.

**Returns:**
- `str`: Formatted context string with timestamps and content.

**Example:**
```python
# Get context for a task
context = await mem.context("API authentication")

# Use in a prompt
prompt = f"""
Previous context:
{context}

User question: How do I authenticate API requests?
"""
```

## Environment Variables

### `ENGRAM_DEBUG`
Set to "true" to enable debug logging.

```bash
ENGRAM_DEBUG=true python your_script.py
```

### `ENGRAM_DATA_DIR`
Override default data directory (~/.engram).

```bash
ENGRAM_DATA_DIR=/custom/path python your_script.py
```

## Storage Backends

Engram automatically selects the best available backend:

1. **Vector Storage** (if FAISS available)
   - Semantic similarity search
   - Efficient for large datasets
   - Requires: `faiss-cpu` or `faiss-gpu`

2. **File Storage** (fallback)
   - Simple JSON storage
   - No dependencies
   - Good for small datasets

## Error Handling

All methods handle errors gracefully:

```python
# Store always succeeds or raises exception
try:
    memory_id = await mem.store("Important data")
except Exception as e:
    print(f"Storage failed: {e}")

# Recall returns empty list on error
memories = await mem.recall("search term")
if not memories:
    print("No memories found or search failed")

# Context returns helpful message on error
context = await mem.context("topic")
# Returns "No relevant context found." if search fails
```

## Performance Tips

1. **Batch Operations**: Store related memories together
   ```python
   for item in items:
       await mem.store(item)  # Each is a separate transaction
   ```

2. **Namespace Selection**: Use namespaces to organize memories
   ```python
   conversation = Memory("conversation")
   technical = Memory("technical")
   personal = Memory("personal")
   ```

3. **Metadata for Filtering**: Use metadata for better organization
   ```python
   await mem.store(
       "Configuration updated",
       timestamp=datetime.now(),
       user="alice",
       action="config_change"
   )
   ```

## Thread Safety

Memory instances are safe for concurrent use with asyncio:

```python
async def worker(mem, data):
    await mem.store(data)

# Safe to use concurrently
await asyncio.gather(
    worker(mem, "data1"),
    worker(mem, "data2"),
    worker(mem, "data3")
)
```

## Limitations

- Maximum content size: No hard limit, but very large texts may impact performance
- Namespaces: Alphanumeric + underscore recommended
- Metadata: Must be JSON-serializable

## Version History

- v0.7.0: Simplified API - just Memory class with 3 methods
- v0.6.0: Previous version with multiple APIs (deprecated)