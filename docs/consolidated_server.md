# Engram Consolidated Server

The Consolidated Server feature of Engram combines the core memory service and HTTP wrapper into a single server running on a single port, simplifying deployment and firewall configuration.

## Overview

Previously, Engram required two separate services:
1. **Memory Service**: Core storage and retrieval (port 8000)
2. **HTTP Wrapper**: Simplified REST API interface (port 8001)

The Consolidated Server combines both services on a single port (8000) using FastAPI's routing system to organize the endpoints by prefix:

- `/memory/*` - Core memory API endpoints
- `/http/*` - HTTP wrapper endpoints for Claude
- `/nexus/*` - Nexus interface endpoints
- `/structured/*` - Structured memory endpoints

## Benefits

- **Simplified Deployment**: Only one service to manage and monitor
- **Single Port**: Only one firewall port to open and configure
- **Easier Maintenance**: Single code base and configuration
- **Improved Security**: Reduced attack surface and port exposure
- **No Functionality Loss**: All features remain available through organized endpoints

## Usage

### Starting the Consolidated Server

```bash
# Start the consolidated server
./cmb_consolidated

# With custom settings
./cmb_consolidated --client-id my-project --port 8080 --host 0.0.0.0 --data-dir ~/cmb-data
```

### Using with Claude

When using with Claude, the quickmem library automatically connects to the consolidated server:

```python
# Import memory functions
from cmb.cli.quickmem import m, t, r, w, l, c, k, f, i, x, s, a, p, v

# Check memory service status
status = s()

# Load previous memories
previous = l(3)

# Use memory functions as usual
m("project")  # Search memories
t("New insight")  # Store a thought
```

### API Structure

The consolidated server organizes endpoints by service type:

1. **Core Memory API** (`/memory/*`)
   - POST `/memory/query` - Search memories with complex parameters
   - POST `/memory/store` - Store a memory with metadata
   - POST `/memory/context` - Get context from multiple namespaces

2. **HTTP Wrapper** (`/http/*`) 
   - GET `/http/thinking` - Store a thought
   - GET `/http/longterm` - Store important information
   - GET `/http/query` - Simple memory search
   - GET `/http/context` - Get context for conversation

3. **Structured Memory** (`/structured/*`)
   - GET `/structured/add` - Add a structured memory
   - GET `/structured/auto` - Add with auto-categorization
   - GET `/structured/search` - Search structured memories
   - GET `/structured/digest` - Get memory digest

4. **Nexus Interface** (`/nexus/*`)
   - GET `/nexus/start` - Start a Nexus session
   - GET `/nexus/process` - Process a message with memory context
   - GET `/nexus/store` - Store a memory through Nexus
   - GET `/nexus/search` - Search across memory systems

### Example Code

See `examples/consolidated_example.py` for a complete example of using the consolidated server API.

## Technical Implementation

The consolidated server uses FastAPI's APIRouter system to organize endpoints:

```python
# Create routers for each service
core_router = APIRouter(prefix="/memory", tags=["Core Memory API"])
http_router = APIRouter(prefix="/http", tags=["HTTP Wrapper API"])
nexus_router = APIRouter(prefix="/nexus", tags=["Nexus API"])
structured_router = APIRouter(prefix="/structured", tags=["Structured Memory API"])

# Mount routers to the main app
app.include_router(core_router)
app.include_router(http_router)
app.include_router(nexus_router)
app.include_router(structured_router)
```

The implementation maintains full compatibility with existing client code by updating the default URL in the quickmem library.

## Migration

Migrating from the two-service setup to the consolidated server:

1. Update to the latest version of Claude Memory Bridge
2. Use the `cmb_consolidated` script instead of `cmb_start_all`
3. No client code changes are needed (URL updates are handled automatically)

## Legacy Support

The traditional two-service setup is still supported for backward compatibility:

```bash
# Legacy mode - separate services
./cmb_start_all
```