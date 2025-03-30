# Hermes Integration for Engram

This module provides integration between Engram's memory system and Hermes's centralized database services, enabling enhanced vector storage and search capabilities.

## Overview

The Hermes integration for Engram replaces the standard memory storage with Hermes's centralized database services, providing:

- **Enhanced Vector Search**: Leverage advanced vector search capabilities from Hermes
- **Centralized Storage**: Store memories in a centralized database shared across components
- **Hardware Optimization**: Automatically use the optimal vector database based on available hardware (FAISS for NVIDIA GPUs, Qdrant for Apple Silicon)
- **Fallback Mechanism**: Gracefully degrade to file-based storage if Hermes is unavailable

## Installation

First, ensure that Hermes is installed and available in your Python environment:

```bash
# Clone the Hermes repository if you haven't already
cd /path/to/tekton
git clone https://github.com/yourusername/hermes.git

# Install Hermes
cd hermes
pip install -e .
```

The Hermes integration is included with Engram and does not require additional installation.

## Usage

### Basic Usage

To use the Hermes-backed memory service:

```python
from engram.integrations.hermes.memory_adapter import HermesMemoryService

# Initialize the memory service
memory = HermesMemoryService(client_id="my_client")

# Add a memory
await memory.add(
    content="Important information to remember",
    namespace="longterm",
    metadata={"priority": "high"}
)

# Search for memories
results = await memory.search(query="important information", limit=5)
for result in results["results"]:
    print(f"{result['content']} (relevance: {result['relevance']})")

# Get relevant context for a query
context = await memory.get_relevant_context(query="information")
print(context)

# Close connections when done
await memory.close()
```

### Replacing the Default Memory Service

To replace the default memory service with the Hermes-backed one:

```python
# Instead of:
# from engram.core.memory import MemoryService

# Use:
from engram.integrations.hermes.memory_adapter import MemoryService

# Then use as normal
memory = MemoryService(client_id="my_client")
```

### Using Compartments

Compartments provide a way to organize memories by topic or purpose:

```python
# Create a compartment
compartment_id = await memory.create_compartment(
    name="Project X",
    description="Memories related to Project X"
)

# Add memories to the compartment
await memory.add(
    content="Project X design document",
    namespace=f"compartment-{compartment_id}",
    metadata={"type": "document"}
)

# Activate the compartment to include in context retrieval
await memory.activate_compartment(compartment_id)

# When done with the compartment
await memory.deactivate_compartment(compartment_id)
```

### Fallback Mode

The Hermes integration will automatically fall back to file-based storage if Hermes is unavailable:

```python
memory = HermesMemoryService(client_id="my_client")
print(f"Hermes available: {memory.hermes_available}")

# All operations will still work, just with file-based storage
```

## API Reference

The Hermes-backed memory service implements the same interface as Engram's standard `MemoryService`:

### Core Methods

- `add(content, namespace, metadata)`: Add a memory to storage
- `search(query, namespace, limit)`: Search for memories
- `get_relevant_context(query, namespaces, limit)`: Get formatted context from multiple namespaces
- `clear_namespace(namespace)`: Clear all memories in a namespace
- `get_namespaces()`: Get available namespaces

### Compartment Methods

- `create_compartment(name, description, parent)`: Create a new memory compartment
- `activate_compartment(compartment_id_or_name)`: Activate a compartment
- `deactivate_compartment(compartment_id_or_name)`: Deactivate a compartment
- `set_compartment_expiration(compartment_id, days)`: Set expiration for a compartment
- `list_compartments(include_expired)`: List all compartments

### New Methods

- `close()`: Close connections and clean up resources

## Example

See [example.py](example.py) for a complete demonstration of using the Hermes integration with Engram.

## Requirements

- Hermes installed and accessible (graceful fallback if not available)
- Async support (Python 3.7+)
- Only standard Python libraries for fallback mode

## Notes

- Memory namespaces in Engram are mapped to namespaces in Hermes with the prefix `engram.{client_id}`
- Compartments are stored locally but their contents are stored in Hermes
- The interface is fully compatible with Engram's standard `MemoryService`, allowing drop-in replacement