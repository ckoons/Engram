# Engram API Reference

## Overview

Engram provides a RESTful API for memory operations, allowing components to store, retrieve, and search memories. The API is designed to be straightforward and consistent, with JSON-based request and response formats.

## Base URL

```
http://{host}:{port}
```

Default: `http://127.0.0.1:8000`

## Authentication

The API currently supports basic authentication through client identification:

* `X-Client-ID` header: A unique identifier for the client using the API

If not provided, the default client ID (typically "default") is used.

## Common Response Codes

* `200` - Success
* `400` - Bad Request - Missing or invalid parameters
* `404` - Not Found - Resource does not exist
* `500` - Server Error - Something went wrong on the server

## Endpoints

### Root Endpoint

#### `GET /`

Returns basic information about the Engram service.

**Response:**

```json
{
  "service": "Engram Memory API",
  "version": "0.8.0",
  "mode": "standalone", 
  "fallback": false
}
```

### Health Check

#### `GET /health`

Checks the health of the Engram service.

**Response:**

```json
{
  "status": "ok",
  "timestamp": "2025-04-28T12:34:56.789123",
  "client_id": "default",
  "storage_type": "vector",
  "vector_available": true,
  "hermes_integration": false
}
```

### Memory Operations

#### `POST /memory`

Adds a new memory.

**Request:**

```json
{
  "content": "This is a memory to store",
  "namespace": "conversations",
  "metadata": {
    "source": "user",
    "importance": "high",
    "tags": ["meeting", "project-x"]
  }
}
```

**Parameters:**

* `content` (required): String or array of message objects
* `namespace` (optional): Namespace to store the memory in (default: "conversations")
* `metadata` (optional): Additional information about the memory

**Response:**

```json
{
  "id": "mem_1682654321",
  "status": "success"
}
```

#### `GET /memory/{memory_id}`

Retrieves a memory by ID.

**Parameters:**

* `memory_id` (path parameter): The ID of the memory to retrieve
* `namespace` (query parameter): The namespace to look in (default: "conversations")

**Response:**

```json
{
  "id": "mem_1682654321",
  "content": "This is a memory to store",
  "namespace": "conversations",
  "metadata": {
    "source": "user",
    "importance": "high",
    "tags": ["meeting", "project-x"],
    "created_at": "2025-04-28T12:34:56.789123"
  }
}
```

### Search Operations

#### `POST /search`

Searches for memories based on a query.

**Request:**

```json
{
  "query": "meeting notes",
  "namespace": "conversations",
  "limit": 5
}
```

**Parameters:**

* `query` (required): Search query
* `namespace` (optional): Namespace to search in (default: "conversations")
* `limit` (optional): Maximum number of results to return (default: 5)

**Response:**

```json
{
  "query": "meeting notes",
  "namespace": "conversations",
  "results": [
    {
      "id": "mem_1682654321",
      "content": "Meeting notes from Project X discussion",
      "relevance": 0.92,
      "metadata": {
        "source": "user",
        "created_at": "2025-04-28T12:34:56.789123",
        "tags": ["meeting", "project-x"]
      }
    },
    {
      "id": "mem_1682654322",
      "content": "Follow-up items from yesterday's meeting",
      "relevance": 0.85,
      "metadata": {
        "source": "user",
        "created_at": "2025-04-27T15:30:00.123456",
        "tags": ["meeting", "follow-up"]
      }
    }
  ],
  "count": 2
}
```

#### `POST /context`

Retrieves relevant context from multiple namespaces based on a query.

**Request:**

```json
{
  "query": "What are the key points from our recent discussions?",
  "namespaces": ["conversations", "thinking", "longterm"],
  "limit": 3
}
```

**Parameters:**

* `query` (required): Search query
* `namespaces` (optional): Array of namespaces to search in (default: all available)
* `limit` (optional): Maximum memories per namespace (default: 3)

**Response:**

```json
{
  "context": "Here are relevant memories from our conversations:\n\n1. Meeting notes from Project X discussion (April 28, 2025)\n2. Follow-up items from yesterday's meeting (April 27, 2025)\n\nFrom thinking:\n\n1. Analysis of Project X requirements (April 26, 2025)\n\nFrom longterm:\n\n1. Project X Goals and Objectives (April 20, 2025)",
  "source_memories": [
    {
      "id": "mem_1682654321",
      "namespace": "conversations"
    },
    {
      "id": "mem_1682654322",
      "namespace": "conversations"
    },
    {
      "id": "mem_1682654323",
      "namespace": "thinking"
    },
    {
      "id": "mem_1682654324",
      "namespace": "longterm"
    }
  ]
}
```

### Namespace Operations

#### `GET /namespaces`

Lists all available namespaces.

**Response:**

```json
[
  "conversations",
  "thinking",
  "longterm",
  "projects",
  "compartments",
  "session",
  "compartment-comp_12345",
  "compartment-comp_67890"
]
```

### Compartment Operations

#### `POST /compartments`

Creates a new memory compartment.

**Request:**

```json
{
  "name": "Project X",
  "description": "Memories related to Project X development",
  "parent": "comp_12345"
}
```

**Parameters:**

* `name` (required): Name of the compartment
* `description` (optional): Description of the compartment
* `parent` (optional): ID of the parent compartment for hierarchical organization

**Response:**

```json
{
  "id": "comp_67890",
  "status": "success"
}
```

#### `GET /compartments`

Lists all compartments.

**Parameters:**

* `include_inactive` (query parameter): Whether to include inactive compartments (default: false)

**Response:**

```json
[
  {
    "id": "comp_12345",
    "name": "Projects",
    "description": "All project-related memories",
    "parent": null,
    "active": true,
    "created_at": "2025-04-20T10:00:00.123456",
    "expires_at": null
  },
  {
    "id": "comp_67890",
    "name": "Project X",
    "description": "Memories related to Project X development",
    "parent": "comp_12345",
    "active": true,
    "created_at": "2025-04-28T12:34:56.789123",
    "expires_at": "2025-05-28T12:34:56.789123"
  }
]
```

#### `POST /compartments/{compartment_id}/activate`

Activates a compartment for automatic context retrieval.

**Parameters:**

* `compartment_id` (path parameter): The ID of the compartment to activate

**Response:**

```json
{
  "status": "success"
}
```

#### `POST /compartments/{compartment_id}/deactivate`

Deactivates a compartment, excluding it from automatic context retrieval.

**Parameters:**

* `compartment_id` (path parameter): The ID of the compartment to deactivate

**Response:**

```json
{
  "status": "success"
}
```

#### `POST /compartments/{compartment_id}/expiration`

Sets the expiration time for a compartment.

**Request:**

```json
{
  "days": 30
}
```

**Parameters:**

* `compartment_id` (path parameter): The ID of the compartment to update
* `days` (request body): Number of days until expiration, or null to remove expiration

**Response:**

```json
{
  "status": "success",
  "expires_at": "2025-05-28T12:34:56.789123"
}
```

## WebSocket API

Engram also provides a WebSocket API for real-time memory events. The WebSocket endpoint is available at:

```
ws://{host}:{port}/ws
```

### Connection

To connect, include the client ID as a query parameter:

```
ws://127.0.0.1:8000/ws?client_id=example
```

### Message Format

Messages are sent and received in JSON format:

```json
{
  "type": "command",
  "payload": {
    // Command-specific payload
  }
}
```

### Available Commands

#### Memory Add

```json
{
  "type": "memory.add",
  "payload": {
    "content": "This is a memory to store",
    "namespace": "conversations",
    "metadata": {
      "source": "user"
    }
  }
}
```

#### Memory Search

```json
{
  "type": "memory.search",
  "payload": {
    "query": "memory to store",
    "namespace": "conversations",
    "limit": 5
  }
}
```

#### Get Context

```json
{
  "type": "context.get",
  "payload": {
    "query": "What do I need to remember?",
    "namespaces": ["conversations", "longterm"]
  }
}
```

### Event Messages

The server sends event messages to notify clients of memory operations:

```json
{
  "type": "event",
  "event": "memory.added",
  "payload": {
    "id": "mem_1682654321",
    "namespace": "conversations"
  }
}
```

Event types include:
* `memory.added`
* `memory.updated`
* `memory.deleted`
* `compartment.created`
* `compartment.activated`
* `compartment.deactivated`

## Error Handling

Error responses follow a consistent format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common errors include:

* `"Missing required parameter: [parameter]"` - A required parameter was not provided
* `"Invalid namespace: [namespace]"` - The specified namespace is not valid
* `"Memory [id] not found in namespace [namespace]"` - The requested memory does not exist
* `"Compartment [id] not found"` - The requested compartment does not exist
* `"Error connecting to vector database"` - Vector database is unavailable

## Client Libraries

### Python

```python
from engram.client import EngramClient

# Initialize client
client = EngramClient(url="http://localhost:8000", client_id="example")

# Add memory
memory_id = await client.add_memory(
    content="This is a test memory",
    namespace="conversations"
)

# Search memories
results = await client.search_memories(
    query="test memory",
    namespace="conversations",
    limit=5
)

# Get context
context = await client.get_context(
    query="What should I remember?",
    namespaces=["conversations", "longterm"]
)
```

### JavaScript

```javascript
import { EngramClient } from 'engram-client';

// Initialize client
const client = new EngramClient({
  url: 'http://localhost:8000',
  clientId: 'example'
});

// Add memory
client.addMemory({
  content: 'This is a test memory',
  namespace: 'conversations'
})
.then(response => {
  console.log(`Memory added with ID: ${response.id}`);
})
.catch(error => {
  console.error('Error adding memory:', error);
});

// Search memories
client.searchMemories({
  query: 'test memory',
  namespace: 'conversations',
  limit: 5
})
.then(results => {
  console.log('Search results:', results);
})
.catch(error => {
  console.error('Error searching memories:', error);
});

// Get context
client.getContext({
  query: 'What should I remember?',
  namespaces: ['conversations', 'longterm']
})
.then(context => {
  console.log('Context:', context);
})
.catch(error => {
  console.error('Error getting context:', error);
});
```