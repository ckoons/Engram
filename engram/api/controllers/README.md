# API Controllers

This directory was created as part of refactoring the large `consolidated_server.py` file into a more modular structure to improve maintainability and readability, following the Tekton engineering guidelines on file size (under 500 lines per file).

## Module Structure

The controllers are organized by functional area:

- `root.py`: Root and health check endpoints
- `core_memory.py`: Core memory management endpoints
- `http_wrapper.py`: HTTP GET endpoints for memory operations
- `compartments.py`: Memory compartment management endpoints
- `private.py`: Private memory management endpoints
- `structured.py`: Structured memory endpoints
- `nexus.py`: Nexus interface endpoints
- `clients.py`: Client management endpoints

## Compatibility

The main `consolidated_server.py` file acts as a compatibility layer, re-exporting the key components from the modular structure. This ensures backward compatibility with existing code that imports from the original location.

## Usage

The server functionality remains the same, but the code is now more modular and easier to maintain. 

To start the server:

```python
from engram.api.server import app

# Run with uvicorn
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

Or use the compatibility layer:

```python
from engram.api.consolidated_server import app
```