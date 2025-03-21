# Ollama Integration with Engram

This document describes the integration between Ollama and Engram, allowing Ollama models to use Engram's memory system.

## Overview

The Ollama integration allows you to use Ollama models with Engram's memory system. This gives locally run AI models persistent memory across sessions, similar to how Claude works with Engram.

## Setup

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Install Engram according to the [installation instructions](../README.md)
3. Run the `engram_with_ollama` script to launch Ollama with Engram memory

## Usage

To launch Ollama with Engram memory, use the `engram_with_ollama` script:

```bash
engram_with_ollama [MODEL_NAME]
```

Where `MODEL_NAME` is the name of the Ollama model you want to use (e.g., `llama3:8b`, `mistral`, etc.). If not specified, it defaults to `llama3:8b`.

### Options

- `--client-id NAME`: Set a specific client ID (default: `ollama`)
- `--memory-only`: Only start the memory service, don't launch Ollama
- `--help`: Show help message

### Memory Commands

During a chat session, you can use the following commands:

- `/remember TEXT`: Save a memory
- `/memories`: List recent memories
- `/search QUERY`: Search memories
- `/reset`: Reset chat history
- `/quit` or `exit`: Exit the session

## Technical Implementation

### Components

1. **engram_with_ollama**: Shell script that sets up and launches Ollama with Engram
2. **ollama_bridge.py**: Python bridge between Ollama and Engram memory
3. **test_ollama_integration.py**: Test script for verifying integration

### Asynchronous Memory Handling

The Engram memory functions are asynchronous (they return coroutines that need to be awaited), but the Ollama bridge needs to call them in a synchronous context. 

The bridge implements a `MemoryHandler` class that properly handles the asynchronous nature of the memory functions:

```python
class MemoryHandler:
    """Helper class to handle async/sync memory operations."""
    
    @staticmethod
    def store_memory(content: str):
        """Store a memory, handling async/sync cases."""
        try:
            return run(m(content))
        except Exception as e:
            print(f"Error storing memory: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_recent_memories(count: int = 5):
        """Get recent memories, handling async/sync cases."""
        try:
            return run(l(count))
        except Exception as e:
            print(f"Error getting recent memories: {e}")
            return []
    
    @staticmethod
    def search_memories(query: str):
        """Search memories, handling async/sync cases."""
        try:
            return run(k(query))
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
```

The `run` function from `engram.cli.quickmem` properly executes coroutines:

```python
def run(coro):
    """Run a coroutine in the current event loop or create a new one."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)
```

### Memory API

The integration uses the following memory functions from `engram.cli.quickmem`:

- `m(content)`: Store a memory
- `l(count)`: List recent memories
- `k(query)`: Search memories by keyword
- `t(content, tags)`: Store a tagged memory
- `s()`: Get memory service status

## Troubleshooting

### Common Issues

1. **Ollama not installed or running**
   - Install Ollama from [ollama.ai](https://ollama.ai)
   - Start Ollama with `ollama serve`

2. **Model not available**
   - Pull the model with `ollama pull MODEL_NAME`

3. **Memory service not running**
   - Start the Engram memory service with `engram_consolidated`

4. **"'coroutine' object is not iterable" error**
   - This error occurs when the memory functions are called directly without properly awaiting them or running them through the `run` function.
   - Make sure you're using the latest version of the bridge script that uses the `MemoryHandler` class.

5. **"RuntimeWarning: coroutine 'm' was never awaited"**
   - This warning indicates that an async function is being called without being awaited.
   - The bridge script uses the `run` function to properly execute coroutines.

### Updates and Fixes

If you encounter issues with the Ollama bridge, you may need to update the bridge script. The `engram_with_ollama` script will not overwrite an existing bridge script, so you'll need to delete it first:

```bash
rm ~/projects/github/Engram/ollama_bridge.py
engram_with_ollama
```

## Future Enhancements

1. **Streaming support**: Add streaming support for Ollama responses
2. **Advanced memory retrieval**: Implement more advanced memory retrieval methods
3. **Context enrichment**: Automatically inject relevant memories into the conversation context
4. **Web UI integration**: Add Ollama support to the Engram web UI
5. **Multi-model support**: Support simultaneous usage of multiple Ollama models