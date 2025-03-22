# Engram Multi-Client Support

The Engram Memory System now supports multiple Claude instances connecting to a single server with different client IDs, offering a more efficient and manageable architecture.

## Overview

Engram's multi-client architecture allows:

1. A single server instance to handle requests from multiple Claude instances
2. Each client to maintain its own separate memory spaces
3. Dynamic initialization of memory services per client
4. Efficient resource sharing and management

## How It Works

The multi-client architecture is built on a new `MemoryManager` component that manages memory services for different clients:

1. A single server instance runs on one port (default: 8000)
2. Client IDs are passed in API requests via the `X-Client-ID` header
3. The server dynamically creates and manages memory services for each unique client ID
4. Idle clients are periodically cleaned up to conserve resources

## Usage

### Starting the Server

Start the Engram server in background mode:

```bash
# Start with default settings
./engram_consolidated --background

# Start with specific port and data directory
./engram_consolidated --port 8001 --data-dir /path/to/data --background
```

### Connecting Multiple Claude Instances

Each Claude instance should:

1. Set a unique `ENGRAM_CLIENT_ID` environment variable
2. OR use the `X-Client-ID` header in API requests

```python
# Example: Setting client ID in API requests
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/memory/store",
        headers={"X-Client-ID": "claude-alpha"},
        json={
            "key": "memory_1",
            "value": "This is a test memory for Claude Alpha",
            "namespace": "personal"
        }
    )
```

### Managing Clients

The `/clients` API endpoints allow you to manage and monitor connected clients:

- List all clients: `GET /clients/list`
- Get client status: `GET /clients/status/{client_id}`
- Clean up idle clients: `POST /clients/cleanup?idle_threshold=3600`

### Example Script

A complete example demonstrating multi-client usage is available in:
`/examples/multi_client_example.py`

## Architecture

The multi-client architecture is built on these key components:

1. **MemoryManager**: Manages memory services for different clients
   - Creates and caches service instances per client
   - Tracks client activity and last access time
   - Provides clean-up mechanisms for idle clients

2. **FastAPI Dependency Injection**: Routes requests to the right client services
   - Uses the `X-Client-ID` header to identify clients
   - Falls back to a default client ID when none is specified
   - Injects the appropriate service into API endpoint handlers

3. **Client API**: Provides management endpoints for clients
   - Lists active clients and their status
   - Monitors client activity
   - Manages cleanup of idle clients

## Benefits

- **Resource Efficiency**: One server instance serves multiple clients
- **Simplified Deployment**: No need for multiple server processes
- **Centralized Management**: Single point of control for all memory services
- **Easier Scaling**: Add new Claude instances without additional server overhead

## Limitations

- All clients share the same vector database implementation choice (FAISS or fallback)
- Performance may degrade with a very large number of active clients
- No built-in authentication mechanism for client requests

## Future Enhancements

- Client authentication mechanisms
- Client-specific configuration options
- Resource limits per client
- Enhanced monitoring and metrics for client activity
- Client grouping for shared memory spaces