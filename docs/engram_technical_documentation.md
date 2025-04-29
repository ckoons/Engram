# Engram Technical Documentation

## Overview

Engram is the persistent memory system for the Tekton ecosystem, providing storage, retrieval, and semantic search capabilities across all components. It enables context preservation, knowledge management, and continuity across sessions for AI models and components.

## Architecture

Engram is designed with a modular, layered architecture that provides flexibility and resilience while supporting multiple storage backends and integration methods.

### Key Components

1. **Core Memory Services**
   - `MemoryService`: Base class that provides the fundamental memory operations
   - `MemoryManager`: Manages client-specific memory services and compartments
   - Storage backends: File-based and vector database implementations

2. **Latent Space System**
   - `LatentMemorySpace`: Specialized memory structure for iterative thought refinement
   - `ConvergenceDetector`: Utility for detecting when thought iterations have converged
   - Persistence mechanisms for long-term storage of reasoning traces

3. **Compartment Management**
   - `CompartmentManager`: Handles creation and management of memory compartments
   - Compartment activation/deactivation and expiration management
   - Hierarchical organization of memories

4. **Integration Layer**
   - Hermes integration for centralized database services
   - `HermesMemoryService`: Adapter implementation for Hermes database integration
   - Fallback mechanisms for degraded operation

5. **API Layer**
   - RESTful API endpoints for memory operations
   - WebSocket support for real-time memory events
   - Client authentication and multi-tenancy

### Storage Backends

Engram supports multiple storage backends with automatic fallback:

1. **File Storage**: Simple JSON-based storage for basic operations
   - Used in standalone mode or as fallback when vector storage is unavailable
   - Fully functional but without semantic search capabilities

2. **Vector Storage**: Embedding-based storage for semantic search
   - Integrated with FAISS, LanceDB, or other vector databases
   - Provides semantic similarity search and context retrieval
   - Configurable dimensionality and indexing

### Integration Points

Engram integrates with other Tekton components through:

1. **Hermes Integration**
   - Centralized database services for cross-component memory sharing
   - Unified vector storage and search capabilities
   - Message bus for memory events and notifications

2. **Direct API Access**
   - RESTful API for memory operations
   - Client libraries for common programming languages
   - WebSocket connections for real-time updates

3. **Memory Adapters**
   - Component-specific adapters for specialized memory integration
   - Custom memory retrieval and context formatting
   - Domain-specific memory processing

## Core Concepts

### Memory Namespaces

Engram organizes memories into namespaces:

- **conversations**: Dialog history between user and AI
- **thinking**: AI's internal thought processes
- **longterm**: High-priority persistent memories
- **projects**: Project-specific context
- **compartments**: Metadata about compartments
- **session**: Session-specific memory

### Memory Compartments

Compartments provide structured organization of related memories:

- Created with name, description, and optional parent
- Can be activated/deactivated to control context retrieval
- Support expiration for temporary contexts
- Enable hierarchical organization of memories

### Latent Space Reasoning

Engram's latent space system supports iterative thought refinement:

- Initialize thoughts with seed content
- Refine through multiple reasoning iterations
- Track convergence to determine when refinement is complete
- Persist final insights for long-term reference
- Enable tracing of reasoning paths

## API Reference

### Memory Operations

#### Add Memory
```
POST /memory
{
  "content": string or array of message objects,
  "namespace": string (default: "conversations"),
  "metadata": object (optional)
}
```

#### Search Memory
```
POST /search
{
  "query": string,
  "namespace": string (default: "conversations"),
  "limit": integer (default: 5)
}
```

#### Get Context
```
POST /context
{
  "query": string,
  "namespaces": array of strings (optional),
  "limit": integer (default: 3)
}
```

### Compartment Operations

#### Create Compartment
```
POST /compartments
{
  "name": string,
  "description": string (optional),
  "parent": string (optional)
}
```

#### List Compartments
```
GET /compartments?include_inactive=boolean (default: false)
```

#### Activate Compartment
```
POST /compartments/{compartment_id}/activate
```

#### Deactivate Compartment
```
POST /compartments/{compartment_id}/deactivate
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ENGRAM_CLIENT_ID | Default client ID | "default" |
| ENGRAM_DATA_DIR | Directory to store memory data | "~/.engram" |
| ENGRAM_MODE | Operating mode (standalone, hermes) | "standalone" |
| ENGRAM_USE_FALLBACK | Use fallback file-based storage | false |
| ENGRAM_HOST | Host to bind server to | "127.0.0.1" |
| ENGRAM_PORT | Port to run server on | 8000 |
| ENGRAM_DEBUG | Enable debug logging | false |

### Command Line Arguments

When running the server directly, the following arguments are available:

```bash
python -m engram.api.server [options]

Options:
  --client-id CLIENT_ID    Default client ID (default: 'default')
  --port PORT              Port to run the server on (default: 8000)
  --host HOST              Host to bind the server to (default: '127.0.0.1')
  --data-dir DATA_DIR      Directory to store memory data (default: '~/.engram')
  --fallback               Use fallback file-based implementation without vector database
  --debug                  Enable debug mode
```

## Using Engram

### Starting the Server

```bash
# Start with default settings
python -m engram.api.server

# Start with Hermes integration
ENGRAM_MODE=hermes python -m engram.api.server

# Start with fallback storage
ENGRAM_USE_FALLBACK=1 python -m engram.api.server
```

### Basic Memory Operations

```python
import requests

# Add a memory
response = requests.post("http://localhost:8000/memory", json={
    "content": "This is a test memory",
    "namespace": "conversations",
    "metadata": {"source": "user"}
})
memory_id = response.json()["id"]

# Search memories
response = requests.post("http://localhost:8000/search", json={
    "query": "test memory",
    "namespace": "conversations",
    "limit": 5
})
results = response.json()["results"]

# Get relevant context
response = requests.post("http://localhost:8000/context", json={
    "query": "What was our conversation about?",
    "namespaces": ["conversations", "thinking"],
    "limit": 3
})
context = response.json()["context"]
```

### Using Memory Compartments

```python
import requests

# Create a compartment
response = requests.post("http://localhost:8000/compartments", json={
    "name": "Project X",
    "description": "Memories related to Project X"
})
compartment_id = response.json()["id"]

# Activate the compartment
requests.post(f"http://localhost:8000/compartments/{compartment_id}/activate")

# Add memory to the compartment
requests.post("http://localhost:8000/memory", json={
    "content": "Project X design notes",
    "namespace": f"compartment-{compartment_id}",
    "metadata": {"type": "design"}
})
```

## Integration with Other Components

### Hermes Integration

Engram integrates with Hermes for centralized database services:

1. Enable Hermes mode: `ENGRAM_MODE=hermes`
2. Hermes automatically handles vector database integration
3. Memory is shared across components using Hermes database
4. Fallback to local storage if Hermes is unavailable

### Direct API Integration

Other components can integrate with Engram through its API:

1. Connect to the Engram API server
2. Use standard HTTP methods for memory operations
3. Pass client ID in X-Client-ID header for multi-tenancy
4. Handle authentication and authorization as needed

## Deployment Considerations

### Memory Storage

- Persistent volume required for data directory
- Resource requirements depend on expected memory size
- Vector database requires additional resources for embeddings

### Scalability

- Single-instance design with potential for distributed future versions
- Memory compartments provide logical isolation
- Client IDs enable multi-tenancy

### Security

- No built-in authentication (rely on API gateway or proxies)
- Consider network security for production deployments
- API keys or auth tokens recommended for production use

## Common Patterns and Best Practices

### Memory Organization

- Use namespaces for broad categories of memories
- Create compartments for project-specific or domain-specific memories
- Set appropriate expiration for temporary contexts
- Use metadata to enhance searchability

### Context Retrieval

- Use `get_relevant_context` for generating prompts
- Activate relevant compartments before context retrieval
- Include appropriate namespaces for comprehensive context
- Consider limiting result size for large context windows

### Latent Space for Reasoning

- Initialize thoughts for complex reasoning tasks
- Refine thoughts through multiple iterations
- Check for convergence to optimize processing
- Finalize and persist important insights

## Troubleshooting

### Common Issues

1. **Vector Database Not Available**
   - Engram will fall back to file-based storage
   - Check vector database installation and configuration
   - Set `ENGRAM_USE_FALLBACK=1` to explicitly use file storage

2. **API Connection Issues**
   - Verify server is running with `curl http://localhost:8000/health`
   - Check port and host configuration
   - Ensure network connectivity and firewall settings

3. **Memory Not Found**
   - Verify namespace and client ID
   - Check for expired compartments
   - Ensure memory was successfully stored

4. **Poor Search Results**
   - In fallback mode, only basic text search is available
   - Vector search quality depends on embedding model
   - Consider more specific queries for better results

## Future Directions

1. **Distributed Storage**: Support for distributed memory across instances
2. **Memory Summarization**: Automatic condensing of verbose memories
3. **Enhanced Vector Search**: Additional vector search algorithms and models
4. **Memory Visualization**: Tools for visualizing memory relationships
5. **Advanced Schema Support**: Structured memory for specialized domains