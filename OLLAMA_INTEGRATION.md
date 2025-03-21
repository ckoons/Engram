# Ollama Integration for Engram

This document provides an overview of the Ollama integration for the Engram memory system, enabling Ollama-supported models like Llama3 to access memory functions and AI-to-AI communication capabilities.

## Quick Start

To use Ollama with Engram:

```bash
# Direct approach with FAISS (recommended):
./engram_with_ollama_direct --model llama3:8b

# Virtual environment approach with FAISS:
./setup_ollama_env_with_faiss.sh  # Run once to create environment
./engram_with_ollama_faiss --model llama3:8b

# Original approach (requires NumPy 1.x):
./engram_with_ollama --model llama3:8b
```

This launches the Ollama bridge with the specified model and enables both memory functions and AI-to-AI communication.

## Features

The Ollama integration provides:

1. **Memory Operations**: Store and retrieve information using standard commands
2. **AI-to-AI Communication**: Exchange messages with other AI models like Claude
3. **Standardized System Prompts**: Consistent prompts based on model capabilities
4. **Model-Specific Personas**: Each model has its own identity (e.g., Llama3 = "Echo")
5. **Command Detection**: Pattern matching for both memory and communication commands
6. **Vector Search**: Semantic similarity search using either ChromaDB or FAISS

## Available Commands

### Memory Commands

| Command | Description | Example |
|---------|-------------|---------|
| REMEMBER | Store information | `REMEMBER: Meeting with John on Friday at 3pm` |
| SEARCH | Find information | `SEARCH: project deadlines` |
| RETRIEVE | Get recent memories | `RETRIEVE: 5` |
| CONTEXT | Get context memories | `CONTEXT: work schedule` |
| SEMANTIC | Vector search | `SEMANTIC: similar projects` |
| FORGET | Mark to forget | `FORGET: John's phone number` |
| LIST | List recent entries | `LIST: 3` |
| SUMMARIZE | Create summary | `SUMMARIZE: project status` |

### Communication Commands

| Command | Description | Example |
|---------|-------------|---------|
| SEND TO | Send direct message | `SEND TO Claude: Can you analyze this data?` |
| CHECK MESSAGES FROM | Get messages | `CHECK MESSAGES FROM Claude` |
| REPLY TO | Reply to message | `REPLY TO Claude: Here's the analysis you requested` |
| BROADCAST | Send to all AIs | `BROADCAST: Task completed successfully` |

## Model Capabilities

Different models have different default capabilities:

| Model | Memory Commands | Communication Commands | Vector Support | Persona |
|-------|-----------------|------------------------|---------------|---------|
| llama3 | All basic + LIST, SUMMARIZE | SEND, CHECK, REPLY | Yes | Echo |
| mistral | All basic | SEND, CHECK | No | Mist |
| mixtral | All basic + LIST, SUMMARIZE, TAG | All | Yes | Mix |
| phi3 | All basic | SEND, CHECK | No | Phi |

## System Prompt Types

The Ollama bridge supports three types of system prompts:

1. **Memory**: Focus on memory operations
2. **Communication**: Focus on AI-to-AI communication
3. **Combined**: Include both memory and communication capabilities

Select the prompt type with the `--prompt-type` option:

```bash
./engram_with_ollama_faiss --model llama3:8b --prompt-type communication
```

## Advanced Usage

### Custom Client IDs

Use different client IDs to create separate memory spaces:

```bash
./engram_with_ollama_faiss --model llama3:8b --client-id science-assistant
```

### Threaded Conversations

Maintain multiple conversation threads:

```
SEND TO Claude: [Thread: project-alpha] How is the analysis going?
```

### Multiple Available Models

Specify which models are available for communication:

```bash
./engram_with_ollama_faiss --model llama3:8b --available-models "Claude Phi Mix"
```

## Vector Database Options

Engram supports two vector database options for semantic search:

1. **ChromaDB**: Default option, works with NumPy 1.x
2. **FAISS**: Alternative option, works with NumPy 2.x

The choice is handled automatically by the launcher scripts:

- `engram_with_ollama_direct`: **RECOMMENDED** - Uses FAISS via runtime patch (works with NumPy 2.x)
- `engram_with_ollama_faiss`: Uses FAISS via virtual environment (works with NumPy 2.x)
- `engram_with_ollama`: Original script, uses ChromaDB (requires NumPy 1.x) or file-based fallback

See [FAISS_DIRECT.md](./FAISS_DIRECT.md) for details on the direct FAISS integration.
See [FAISS_VECTOR_DATABASE.md](./FAISS_VECTOR_DATABASE.md) for details on the virtual environment FAISS implementation.

## Implementation Details

The Ollama integration consists of several components:

1. **ollama_bridge.py**: Core integration connecting Ollama API to Engram
2. **ollama_system_prompts.py**: Generates standardized system prompts
3. **engram_with_ollama_direct**: Recommended launcher script (FAISS via runtime patch)
4. **engram_memory_patch.py**: Runtime patcher for FAISS integration
5. **engram_with_ollama_faiss**: Alternative launcher script (FAISS via virtual environment)
6. **engram_with_ollama**: Original launcher script (ChromaDB or file-based fallback)

## Documentation

For more detailed information, see:

- [Direct FAISS Integration](./FAISS_DIRECT.md) (Recommended)
- [Virtual Environment FAISS](./FAISS_VECTOR_DATABASE.md)
- [API Documentation](./docs/ollama_integration.md)
- [AI Communication Guide](./docs/ai_communication.md)
- [Memory Management](./docs/memory_management.md)

## Requirements

- Ollama installed and running locally
- Engram memory service installed and configured
- Python 3.8+
- Required packages: requests
- For vector search: Either ChromaDB (NumPy 1.x) or FAISS (NumPy 2.x)

## Troubleshooting

If you encounter issues:

1. **NumPy Compatibility Issues**:
   - **Direct FAISS solution (Recommended)**:
     ```bash
     ./engram_with_ollama_direct --model llama3:8b
     ```
   - This solution directly patches the memory system at runtime to use FAISS
   - See [FAISS_DIRECT.md](./FAISS_DIRECT.md) for details
   
   - **Virtual Environment FAISS solution**:
     ```bash
     ./setup_ollama_env_with_faiss.sh  # Run once to set up
     ./engram_with_ollama_faiss --model llama3:8b
     ```
   - This creates a dedicated virtual environment with FAISS

2. **Ollama Connection**:
   - Make sure Ollama is running (`curl http://localhost:11434/api/tags`)
   - The script will offer to pull models if they're not already available

3. **Memory Service**:
   - Verify the Engram memory service is running (`./engram_start.sh`)
   - The FAISS solution includes all necessary memory functionality
   - If all else fails, you can use file-based fallback:
     ```bash
     export ENGRAM_USE_FALLBACK=1
     ./engram_with_ollama
     ```

4. **Model Availability**:
   - Check if the model is available in Ollama
   - The script will offer to pull models that aren't installed

5. **General Issues**:
   - Look for error messages in the output
   - Try running with a different model (e.g., `--model llama3:8b-instruct`)

## Future Enhancements

- Multi-AI conversation groups
- Enhanced vector search capabilities
- Memory summarization and organization
- Additional model-specific tuning
- Web-based monitoring interface