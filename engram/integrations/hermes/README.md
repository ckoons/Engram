# Hermes Integration for Engram

This module provides comprehensive integration between Engram and Hermes's centralized services, enabling enhanced capabilities for memory, messaging, and logging.

## Overview

The Hermes integration for Engram connects to Hermes's centralized services, providing:

- **Enhanced Vector Search**: Leverage advanced vector search capabilities from Hermes
- **Centralized Storage**: Store memories in a centralized database shared across components
- **Hardware Optimization**: Automatically use the optimal vector database based on available hardware
- **Asynchronous Messaging**: Enable communication between Engram instances and other components
- **Structured Logging**: Centralized logging with advanced filtering and querying
- **Fallback Mechanism**: Gracefully degrade to local implementations if Hermes is unavailable

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

## Components

The Hermes integration includes several components:

1. **Memory Adapter**: Interface to Hermes's database services for memory storage
2. **Message Bus Adapter**: Interface to Hermes's message bus for component communication
3. **Logging Adapter**: Interface to Hermes's centralized logging system

## Usage

### Memory Service

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

### Message Bus

To use the Hermes message bus for communication:

```python
from engram.integrations.hermes.message_bus_adapter import MessageBusAdapter

# Initialize the message bus
message_bus = MessageBusAdapter(client_id="my_client")
await message_bus.start()

# Define a message handler
async def handle_message(message):
    print(f"Received: {message['content']}")

# Subscribe to a topic
await message_bus.subscribe("example.topic", handle_message)

# Publish a message
await message_bus.publish(
    topic="example.topic",
    message="Hello, world!",
    metadata={"priority": "high"}
)

# Close connections when done
await message_bus.close()
```

### Logging System

To use the Hermes logging system:

```python
from engram.integrations.hermes.logging_adapter import LoggingAdapter

# Initialize the logging adapter
logger = LoggingAdapter(client_id="my_client")

# Log messages at different levels
logger.debug("Debug message")
logger.info("Info message", component="memory")
logger.warning("Warning message", context={"source": "user_input"})
logger.error("Error message", source_file=__file__, source_line=42)
logger.critical("Critical message", component="database", context={"error_code": 500})

# Get recent logs
logs = logger.get_logs(level="WARNING", limit=10)
for log in logs:
    print(f"{log['timestamp']} - {log['level']} - {log['message']}")
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

## Examples

- [memory_example.py](example.py) - Example of memory service usage
- [message_bus_adapter.py](message_bus_adapter.py) - Example of message bus usage (see main function)
- [logging_adapter.py](logging_adapter.py) - Example of logging system usage (see main function)
- [full_integration_example.py](full_integration_example.py) - Comprehensive example using all integration features

## Requirements

- Hermes installed and accessible (graceful fallback if not available)
- Async support (Python 3.7+)
- Only standard Python libraries for fallback mode

## Integration Notes

### Memory System
- Memory namespaces in Engram are mapped to namespaces in Hermes with the prefix `engram.{client_id}`
- Compartments are stored locally but their contents are stored in Hermes
- The interface is fully compatible with Engram's standard `MemoryService`, allowing drop-in replacement

### Message Bus
- Topics are namespaced with `engram.{client_id}` prefix
- Messages can contain string or structured data (converted to/from JSON)
- Provides clean asynchronous communication between Engram instances

### Logging System
- Logs are stored centrally and tagged with component ID
- Provides automatic file-based logging with configurable levels
- Supports context-rich structured logging for better filtering and analysis

## Security Notes

- Communication with Hermes services is currently unencrypted and should be used only in trusted networks
- Future enhancements will include message encryption and authentication
- Local fallback modes provide graceful degradation when Hermes is unavailable