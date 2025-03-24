# Ollama MCP Integration for Engram

This documentation explains how to use the Multi-Capability Provider (MCP) integration with Ollama and Engram.

## Overview

The Ollama MCP adapter allows any MCP-compatible client to use Ollama's language models through a standardized interface. It also integrates with Engram's memory system to provide enhanced context-aware responses.

## Features

- **Standardized API**: Use the MCP protocol to interact with Ollama models
- **Memory Integration**: Optional integration with Engram memory for enhanced context
- **Multiple Capabilities**:
  - `ollama_generate`: Generate text with any Ollama model
  - `ollama_chat`: Chat with any Ollama model
  - `ollama_tags`: List available Ollama models
  - `ollama_memory_chat`: Chat with memory integration

## Getting Started

### Prerequisites

- Ollama running on your system (default: http://localhost:11434)
- Engram installed (for memory integration)
- Python 3.8+ with FastAPI and Uvicorn

### Starting the Ollama MCP Server

Use the provided launcher script:

```bash
# Basic usage
./ollama_mcp

# Specify different Ollama host and port
./ollama_mcp --ollama-host http://192.168.1.100:11434 --port 8002

# Enable memory integration with specific client ID
./ollama_mcp --client-id my_client
```

### Starting Both Engram and Ollama MCP Servers

Use the dual launcher to start both services:

```bash
# Basic usage
./engram_ollama_dual

# Customize ports
./engram_ollama_dual --engram-port 8001 --ollama-port 8002

# Use memory fallback mode (no vector DB)
./engram_ollama_dual --fallback
```

## Testing the Ollama MCP Server

Use the provided test script:

```bash
# Basic test
./utils/test_ollama_mcp.py

# Test with specific model and prompt
./utils/test_ollama_mcp.py --model llama3:8b --prompt "Explain quantum computing"

# Test with custom server host
./utils/test_ollama_mcp.py --host http://192.168.1.100:8002
```

## Capabilities Documentation

### ollama_generate

Generate text using any Ollama model.

**Parameters:**
- `model` (required): Ollama model to use (e.g., "llama3:8b")
- `prompt` (required): The text prompt to generate from
- `system` (optional): System prompt for the model
- `template` (optional): Prompt template to use
- `context` (optional): Context for model generation
- `options` (optional): Additional generation options (temperature, top_p, etc.)

**Example Request:**
```json
{
  "capability": "ollama_generate",
  "parameters": {
    "model": "llama3:8b",
    "prompt": "Explain the concept of quantum entanglement",
    "options": {
      "temperature": 0.7,
      "top_p": 0.9
    }
  }
}
```

### ollama_chat

Have a conversation with any Ollama model.

**Parameters:**
- `model` (required): Ollama model to use
- `messages` (required): Array of message objects (role and content)
- `system` (optional): System prompt for the chat
- `template` (optional): Prompt template to use
- `options` (optional): Additional generation options
- `enable_memory` (optional): Enable Engram memory integration

**Example Request:**
```json
{
  "capability": "ollama_chat",
  "parameters": {
    "model": "llama3:8b",
    "messages": [
      {"role": "user", "content": "What is machine learning?"}
    ],
    "enable_memory": true
  }
}
```

### ollama_tags

List all available Ollama models.

**Parameters:** None

**Example Request:**
```json
{
  "capability": "ollama_tags",
  "parameters": {}
}
```

### ollama_memory_chat

Chat with an Ollama model with integrated memory from Engram.

**Parameters:**
- `model` (required): Ollama model to use
- `messages` (required): Array of message objects
- `system` (optional): System prompt for the chat
- `client_id` (optional): Engram client ID
- `memory_prompt_type` (optional): Type of memory prompt (memory, communication, combined)
- `options` (optional): Additional generation options

**Example Request:**
```json
{
  "capability": "ollama_memory_chat",
  "parameters": {
    "model": "llama3:8b",
    "messages": [
      {"role": "user", "content": "What did we talk about yesterday?"}
    ],
    "client_id": "user123",
    "memory_prompt_type": "combined"
  }
}
```

## Architecture

The Ollama MCP integration consists of the following components:

1. **OllamaMCPAdapter**: Core adapter that implements MCP protocol for Ollama
2. **Ollama MCP Server**: FastAPI server that exposes the adapter via HTTP
3. **Launcher Scripts**: Convenient scripts to start the servers

Integration with Engram is achieved through:
1. Memory service access for context retrieval
2. Memory storage for conversation history
3. Memory commands in model outputs

## Troubleshooting

### Common Issues

- **Ollama not available**: Ensure Ollama is running at the specified host/port
- **Model not found**: Check available models with the ollama_tags capability
- **Memory integration not working**: Verify Engram is running and accessible

### Logs

The servers produce detailed logs that can help diagnose issues:

```bash
# Run with debug flag for more verbose logging
./ollama_mcp --debug
./engram_ollama_dual --debug
```

## Security Considerations

- The MCP server binds to localhost by default for security
- For production deployment, use proper authentication and TLS
- Consider network isolation for the Ollama and Engram servers