# Claude Memory Bridge HTTP Wrapper

The HTTP Wrapper provides a way for Claude to access memories without requiring tool approval for each action.

## Overview

The HTTP wrapper is a simple FastAPI server that exposes the same functionality as the core memory service, but via HTTP endpoints that can be accessed using standard Python libraries without triggering Claude's tool approval system.

## How It Works

1. You start the HTTP wrapper on port 8001 (different from the standard memory bridge on port 8000)
2. In Claude Code sessions, you import the `http_helper` module instead of `claude_helper`
3. The helper functions make HTTP requests to the wrapper instead of directly calling the memory service
4. Since the requests use Python's built-in `urllib` library, they don't require tool approval

## Getting Started

### Starting the HTTP Wrapper

```bash
# Start the HTTP wrapper (runs on port 8001 by default)
./cmb_http

# Start with custom settings
./cmb_http --port 8002 --client-id custom
```

### Using the HTTP Helper in Claude Code

```python
# Import the HTTP helper (no tool approval needed)
from cmb.cli.http_helper import query_memory, store_memory, store_thinking, store_longterm, get_context

# Store a memory
store_memory("fact", "Claude Memory Bridge allows seamless memory access")

# Query memories
query_memory("memory bridge")

# Store a thought
store_thinking("The user seems interested in creating a natural conversation flow")

# Store important information
store_longterm("The user's name is Casey Koons")

# Get formatted context for current conversation
context = get_context("current project")
```

## HTTP Endpoints

The HTTP wrapper exposes the following endpoints:

### Basic Memory Operations
- `GET /health` - Check the status of the memory bridge
- `GET /store?key=<key>&value=<value>&namespace=<namespace>` - Store a memory
- `GET /thinking?thought=<thought>` - Store a thought
- `GET /longterm?info=<info>` - Store important information
- `GET /query?query=<query>&namespace=<namespace>&limit=<limit>` - Query memories
- `GET /context?query=<query>&include_thinking=<true|false>&limit=<limit>` - Get context
- `GET /clear/<namespace>` - Clear all memories in a namespace

### Session Persistence
- `GET /write?content=<content>&metadata=<json_metadata>` - Write session memory for persistence

### Memory Compartmentalization
- `GET /compartment/create?name=<name>` - Create a new memory compartment
- `GET /compartment/list` - List existing compartments and their active status
- `GET /compartment/activate?compartment=<compartment_id_or_name>` - Activate a compartment
- `GET /compartment/deactivate?compartment=<compartment_id_or_name>` - Deactivate a compartment
- `GET /compartment/store?compartment=<compartment_id_or_name>&content=<content>` - Store in compartment

### Memory Expiration
- `GET /keep?memory_id=<memory_id>&days=<days>` - Set expiration date for a memory

## Standalone Usage

You can also use the HTTP wrapper without Claude, using standard HTTP tools:

```bash
# Store a memory
curl "http://localhost:8001/store?key=fact&value=This%20is%20a%20test"

# Query memories
curl "http://localhost:8001/query?query=test&namespace=conversations"

# Get context
curl "http://localhost:8001/context?query=test"

# Create a memory compartment
curl "http://localhost:8001/compartment/create?name=ProjectX"

# Store in a compartment
curl "http://localhost:8001/compartment/store?compartment=ProjectX&content=Important%20project%20info"

# List compartments
curl "http://localhost:8001/compartment/list"

# Write session memory
curl "http://localhost:8001/write?content=Session%20notes%20to%20remember"

# Set memory expiration
curl "http://localhost:8001/keep?memory_id=memory123&days=90"
```

## Troubleshooting

- Make sure the HTTP wrapper is running on the correct port (8001 by default)
- Check that the URL in `http_helper.py` matches the wrapper's address
- If you change the port, set the `CMB_HTTP_URL` environment variable to the new address
- Use `/health` endpoint to verify the service is running correctly
- Check memory bridge logs for any errors related to compartment or expiration operations

## Security Considerations

The HTTP wrapper has no authentication by default. Use it only on your local machine or in a secure environment. Do not expose it to the internet without adding proper authentication.