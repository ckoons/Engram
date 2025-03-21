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

## Enhancing Ollama Models with Memory Capabilities

Since most Ollama models lack direct tool-calling abilities, here are several approaches to enhance their integration with Engram:

### 1. Structured Prompt System

Implement a structured prompt system that inserts memory information directly into the context:

```python
def enhance_prompt_with_memory(user_input, model_name, memory_handler):
    """Enhance user prompt with relevant memories."""
    
    # Check if input requires memory augmentation
    if "remember" in user_input.lower() or "what do you know about" in user_input.lower():
        # Search for relevant memories
        search_term = user_input.split("about")[-1].strip() if "about" in user_input else user_input
        memories = memory_handler.search_memories(search_term)
        
        # Format memories for context
        memory_context = "Here are some relevant memories I have:\n"
        for memory in memories[:3]:  # Limit to 3 most relevant memories
            memory_context += f"- {memory.get('content', '')}\n"
        
        # Create enhanced prompt
        enhanced_prompt = f"{memory_context}\n\nUser: {user_input}"
        return enhanced_prompt
    
    return user_input
```

### 2. Function Calling Emulation

Create a function calling emulation layer that detects potential function calls in model outputs:

```python
def detect_memory_operations(model_output):
    """Detect and execute memory operations in model output."""
    operation_results = []
    cleaned_output = model_output
    
    # Define patterns for memory operations with flexible formatting
    memory_patterns = [
        (r"(?:REMEMBER:|(?:\*\*)?REMEMBER(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "store", MemoryHandler.store_memory),
        (r"(?:SEARCH:|(?:\*\*)?SEARCH(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "search", MemoryHandler.search_memories),
        (r"(?:RETRIEVE:|(?:\*\*)?RETRIEVE(?:\*\*)?:?)\s*(\d+)(?=\n|$)", "retrieve", lambda n: MemoryHandler.get_recent_memories(int(n))),
        (r"(?:CONTEXT:|(?:\*\*)?CONTEXT(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "context", MemoryHandler.get_context_memories),
        (r"(?:SEMANTIC:|(?:\*\*)?SEMANTIC(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "semantic", MemoryHandler.get_semantic_memories),
    ]
    
    # Check for patterns and execute corresponding functions
    for pattern, op_type, func in memory_patterns:
        matches = re.findall(pattern, model_output)
        for match in matches:
            try:
                result = func(match)
                operation_results.append({
                    "type": op_type,
                    "input": match,
                    "result": result
                })
                # Remove the operation from the output
                cleaned_output = re.sub(pattern, "", cleaned_output, count=1)
            except Exception as e:
                print(f"Error executing memory operation: {e}")
    
    # Clean up extra newlines caused by removal
    cleaned_output = re.sub(r'\n{3,}', '\n\n', cleaned_output)
    return cleaned_output.strip(), operation_results
```

The pattern detector is flexible and can recognize multiple formats:
- Standard format: `REMEMBER: information`
- Markdown bold: `**REMEMBER**: information`
- With or without colons: `REMEMBER information`

This flexibility helps accommodate various formatting styles that models might use.

### 3. System Prompt Design

Provide clear instructions in the system prompt to guide the model to use a specific format for memory operations:

```
System: You have access to a memory system that can store and retrieve information. 
To use this system, include special commands in your responses:

- To store information: REMEMBER: {information to remember}
- To search for information: SEARCH: {search term}
- To retrieve recent memories: RETRIEVE: {number of memories}

Your memory commands will be processed automatically, and the output will be fed back
to you in the next user message. Be sure to format your memory commands exactly as shown.
```

### 4. Automated Semantic Memory Operations

Implement automatic semantic memory operations based on conversation context:

```python
def auto_memory_management(user_input, model_output, client_id, memory_handler):
    """Automatically handle memory operations based on conversation."""
    
    # Store significant exchanges
    if len(user_input) > 20 and len(model_output) > 50:
        memory_text = f"User asked about {user_input[:50]}... and {client_id} responded with information about {model_output[:50]}..."
        memory_handler.store_memory(memory_text)
    
    # Detect potential information worth remembering
    if "important to remember" in model_output.lower() or "don't forget" in model_output.lower():
        sentences = re.split(r'[.!?]', model_output)
        for sentence in sentences:
            if "important" in sentence.lower() or "remember" in sentence.lower() or "key point" in sentence.lower():
                memory_handler.store_memory(sentence.strip())
    
    # Automatic context enrichment for next exchange
    related_memories = memory_handler.search_memories(user_input)
    return related_memories
```

### 5. Hybrid Architecture

Create a hybrid architecture where Claude acts as a memory manager for Ollama models:

```python
def hybrid_memory_architecture(user_input, ollama_model, claude_endpoint, memory_handler):
    """Use Claude as a memory manager for Ollama models."""
    
    # First, get relevant memories using Claude's capabilities
    claude_prompt = f"The user is asking Ollama: '{user_input}'. Retrieve relevant memories that would help answer this question effectively. Format as bullet points."
    claude_response = call_claude_api(claude_endpoint, claude_prompt)
    
    # Extract memory suggestions
    memory_suggestions = parse_claude_response(claude_response)
    
    # Augment Ollama prompt with Claude-selected memories
    augmented_prompt = f"Here is relevant background information:\n{memory_suggestions}\n\nUser: {user_input}"
    
    # Get Ollama response with augmented context
    ollama_response = call_ollama_api(ollama_model, augmented_prompt)
    
    # Use Claude to determine what to remember from this exchange
    memory_prompt = f"User asked: '{user_input}'\nOllama responded: '{ollama_response}'\nWhat information from this exchange should be remembered for future reference? Format as a concise statement."
    memory_suggestion = call_claude_api(claude_endpoint, memory_prompt)
    
    # Store the memory
    memory_handler.store_memory(memory_suggestion)
    
    return ollama_response
```

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