# Engram Memory System

This directory contains the modular implementation of the Engram Memory System, which provides memory storage, retrieval, and management with namespace support for AI systems.

## Architecture

The memory system has been refactored from a monolithic `memory.py` file into a modular structure with the following components:

### Core Components

- **`__init__.py`**: Exports the main MemoryService class and essential components
- **`base.py`**: Contains the MemoryService class that orchestrates memory operations
- **`config.py`**: Manages configuration including vector database dependencies and fallback mode
- **`compartments.py`**: Provides compartmentalized memory organization and management
- **`search.py`**: Implements search functionality across namespaces with relevance ranking
- **`utils.py`**: Utility functions for formatting, timestamps, and common operations

### Storage Backends

- **`storage/file_storage.py`**: File-based fallback storage when vector DB is not available
- **`storage/vector_storage.py`**: Vector-based storage with semantic search capabilities

## Backward Compatibility

The original `memory.py` file now serves as a compatibility layer that re-exports all components from the new modular structure. This ensures that existing code will continue to work without requiring changes.

## Features

- **Multiple Memory Namespaces**: Organize memories by type (conversations, thinking, longterm, etc.)
- **Compartmentalization**: Create, activate, and deactivate memory compartments for different contexts
- **Expiration Management**: Set and enforce expiration dates for memories and compartments
- **Vector Search**: High-performance semantic search when vector database (FAISS) is available
- **Fallback Mode**: Graceful degradation to file-based storage when vector capabilities aren't available
- **Metadata Support**: Store and retrieve additional data associated with memories
- **Relevance Ranking**: Return memories sorted by relevance to the query
- **Content Filtering**: Filter out forgotten information from search results

## Usage Example

```python
from engram.core.memory import MemoryService

# Initialize memory service
memory = MemoryService(client_id="user123")

# Add a memory
await memory.add(
    content="Important fact about AI systems",
    namespace="longterm",
    metadata={"priority": "high"}
)

# Create a compartment
project_id = await memory.create_compartment(
    name="Project X",
    description="Research on quantum computing"
)

# Activate the compartment
await memory.activate_compartment(project_id)

# Search for relevant memories
results = await memory.search(
    query="quantum computing",
    namespace=f"compartment-{project_id}",
    limit=5
)

# Get formatted context for prompting
context = await memory.get_relevant_context(
    query="AI systems",
    namespaces=["longterm", f"compartment-{project_id}"]
)
```

## Maintainer Notes

When modifying the memory system:

1. Ensure backward compatibility is maintained
2. Update unit tests for any changed functionality
3. Document new features in this README
4. Handle exceptions gracefully with appropriate logging
5. Validate namespace inputs to prevent errors

## Implementation Details

- The system is designed to work without vector DB dependencies by falling back to file-based storage
- Component interactions are managed through well-defined interfaces between modules
- Each namespace is stored as a separate collection in the vector database
- Compartments are implemented as dynamic namespaces with additional metadata
- Search functionality implements content filtering for privacy and safety