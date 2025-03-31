# Hermes Memory Adapter

This directory contains the refactored implementation of the Hermes Memory Adapter for Engram. The system was previously implemented as a single monolithic file (`memory_adapter.py`) but has now been refactored into a more modular structure for better maintainability and extensibility.

## Directory Structure

- **core/**: Core implementation and imports
  - `imports.py`: Common imports and Hermes availability detection
  - `service.py`: Main service class implementation
  
- **operations/**: Memory operations
  - `memory.py`: Functions for adding and managing memories
  - `search.py`: Functions for searching and retrieving memories
  
- **compartments/**: Compartment management
  - `manager.py`: Management of memory compartments
  
- **utils/**: Utility functions
  - `helpers.py`: General helper functions
  - `fallback.py`: Fallback implementations for when Hermes is unavailable

## Backward Compatibility

The original `memory_adapter.py` file now serves as a compatibility layer, importing and re-exporting classes and functions from the new structure. This ensures that existing code using the Hermes Memory Adapter will continue to work without modification.

## Usage

The API remains the same as before:

```python
from engram.integrations.hermes.memory_adapter import HermesMemoryService

# Create a memory service instance
memory_service = HermesMemoryService(client_id="my-client")

# Add a memory
await memory_service.add(
    content="This is a memory",
    namespace="conversations",
    metadata={"source": "user"}
)

# Search for memories
results = await memory_service.search(
    query="memory",
    namespace="conversations",
    limit=5
)

# Get relevant context
context = await memory_service.get_relevant_context(
    query="What do I remember?",
    limit=3
)
```

## Features

- **Vector Search**: Semantic search using vector embeddings when Hermes is available
- **Fallback Storage**: File-based storage when Hermes is not available
- **Memory Compartments**: Organization of memories into compartments
- **Forgotten Memory Filtering**: Support for filtering out forgotten information
- **Metadata Support**: Rich metadata for memory entries
- **Asynchronous API**: Full async/await support throughout