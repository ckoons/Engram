# Structured Memory

This package provides a file-based memory management system with organization and importance ranking.

## Overview

The `StructuredMemory` class provides a way to organize, store, and retrieve memories with importance ranking and categorization. It's designed for use in AI systems to maintain context and important information across sessions.

## Key Features

- Organized, searchable memory files by category
- Standardized formats (JSON) for easier parsing
- Metadata with timestamps, context, and importance
- Memory importance ranking (1-5 scale)
- Context-aware memory loading
- Automatic categorization of memories based on content

## Module Structure

The module has been organized into the following components:

- **memory/** - Core memory functionality
  - **base.py** - Main `StructuredMemory` class
  - **index.py** - Metadata indexing functionality
  - **migration.py** - Legacy migration tools
  
- **storage/** - Storage mechanisms
  - **file_storage.py** - File-based storage with caching
  
- **operations/** - Core memory operations
  - **add.py** - Memory addition operations
  - **retrieve.py** - Memory retrieval operations 
  - **update.py** - Memory update operations
  - **delete.py** - Memory deletion operations
  - **search.py** - High-level search operations
  
- **search/** - Search functionality
  - **content.py** - Content-based search
  - **tags.py** - Tag-based search
  - **context.py** - Context-based search
  - **semantic.py** - Semantic search with vector embeddings
  
- **categorization/** - Memory categorization
  - **auto.py** - Automatic memory categorization

## Usage

```python
from engram.core.structured import StructuredMemory

# Initialize memory service
memory = StructuredMemory(client_id="user123")

# Add a memory
memory_id = await memory.add_memory(
    content="Important fact about neural networks",
    category="facts",
    importance=4,
    tags=["ai", "neural-networks"]
)

# Retrieve memories by search
results = await memory.search_memories(
    query="neural networks",
    min_importance=3, 
    limit=5
)

# Get a memory digest
digest = await memory.get_memory_digest()
```

## Backward Compatibility

This module maintains backward compatibility through the main `__init__.py` file, which re-exports the `StructuredMemory` class. All existing code that imports from `engram.core.structured` will continue to work without changes.