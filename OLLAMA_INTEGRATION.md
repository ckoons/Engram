# Ollama Integration with Engram

Quick reference guide for using Ollama with Engram's memory system.

## Setup

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start Ollama service: `ollama serve`
3. Pull a model: `ollama pull llama3:8b` (or any other model)
4. Run Engram with Ollama: `engram_with_ollama [MODEL_NAME]`

## Usage

```bash
# Launch with default model (llama3:8b)
engram_with_ollama

# Launch with a specific model
engram_with_ollama mistral
engram_with_ollama llama3:70b
engram_with_ollama deepseek-r1:70b

# Launch with a custom client ID
engram_with_ollama --client-id ollama_custom mistral

# Only start memory service without launching Ollama
engram_with_ollama --memory-only
```

## Memory Commands

During a chat session, you can use:

- `/remember TEXT`: Save a memory
- `/memories`: List recent memories
- `/search QUERY`: Search memories
- `/reset`: Reset chat history
- `/quit` or `exit`: Exit the session

## Known Issues & Fixes

If you encounter a "'coroutine' object is not iterable" error or "RuntimeWarning: coroutine was never awaited" warning, you need to update the bridge script:

```bash
# Force recreate the bridge script
rm ~/projects/github/Engram/ollama_bridge.py
engram_with_ollama

# Alternative: manually update the bridge script to use the MemoryHandler class 
# that properly handles async memory functions
```

## Detailed Documentation

For detailed documentation, see [docs/ollama_integration.md](docs/ollama_integration.md)