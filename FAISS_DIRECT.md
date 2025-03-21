# Direct FAISS Integration for Engram

This document explains how to use the direct FAISS integration for Engram with Ollama, which provides memory capabilities that work with NumPy 2.x.

## Overview

The direct FAISS integration provides a simplified approach to making Engram work with NumPy 2.x by patching the memory module. This solution:

1. Adds FAISS vector search support
2. Works natively with NumPy 2.x
3. Requires no virtual environment
4. Uses a standalone implementation that doesn't conflict with ChromaDB

## Quick Start

```bash
# Install dependencies (if not already installed)
pip install faiss-cpu numpy requests

# Run Engram with Ollama using the direct FAISS integration
./vector_test/engram_with_ollama_faiss --model llama3:8b
```

## How It Works

The implementation works by:

1. Providing a standalone memory implementation in the vector_test directory
2. Replacing ChromaDB-based vector search with FAISS
3. Maintaining API compatibility with the existing memory system
4. Using a simple embedding technique that works with any NumPy version

The implementation includes these components:
- `engram_memory_adapter.py`: An adapter that implements Engram's memory API
- `vector_store.py`: FAISS-based vector storage
- `simple_embedding.py`: Basic embedding generation without transformer models
- `engram_with_faiss_simple.py`: The Python implementation
- `engram_with_ollama_faiss`: A convenient bash launcher

## Advantages

This implementation offers several benefits:

- **NumPy 2.x Compatibility**: Works with the latest NumPy versions
- **Simplicity**: Minimal dependencies and straightforward design
- **Performance**: FAISS is highly optimized for vector similarity search
- **No Conflicts**: Doesn't interfere with the main Engram installation

## Usage

The launcher supports several options:

```bash
./vector_test/engram_with_ollama_faiss --model llama3:8b
```

All memory commands work the same way in the chat:

```
REMEMBER This is important information to store
SEMANTIC SEARCH similar concepts
CONTEXT SEARCH FAISS
```

## Advanced Options

```
Usage: engram_with_ollama_faiss [options]

Options:
  --model MODEL       Ollama model to use (default: llama3:8b)
  --client-id ID      Client ID for Engram (default: ollama)
  --vector-dim DIM    Vector dimension for embeddings (default: 128)
  --use-gpu           Use GPU for FAISS if available
  --memory-dir DIR    Directory to store memory files (default: ./test_memories)
  --help              Show this help message
```

## Troubleshooting

If you encounter issues:

1. Ensure FAISS is properly installed: `pip install faiss-cpu`
2. Check that NumPy is installed: `pip install numpy`
3. Verify Ollama is running: `curl http://localhost:11434/api/tags`
4. Make sure the script is executable: `chmod +x vector_test/engram_with_ollama_faiss`

## Notes

- This implementation doesn't interfere with the main Engram system
- Memory files are stored in the specified memory directory
- The simple embedding technique provides semantic-like search capabilities