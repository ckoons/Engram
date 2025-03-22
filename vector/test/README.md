# FAISS Vector Storage for Engram

This directory contains test scripts and example implementations for the FAISS vector storage solution in Engram.

## Overview

Engram uses FAISS (Facebook AI Similarity Search) for vector search functionality, providing:

1. Efficient semantic search for memories and information
2. Compatible with all NumPy versions
3. High-performance vector operations

## Files

- `faiss_test.py` - Test script to verify FAISS functionality
- `simple_embedding.py` - Basic text embedding implementation
- `vector_store.py` - Vector database implementation using FAISS
- `engram_memory_adapter.py` - Adapter that implements Engram's memory API using FAISS
- `engram_with_faiss_simple.py` - Launcher script for testing Engram with Ollama and FAISS
- `engram_with_ollama_faiss` - Launcher script for Ollama with FAISS integration
- `run_faiss_test.sh` - Helper script for running FAISS tests

## Test Data

The directory contains several test data directories:

- `memories/` - Sample memories for testing
- `test_memories/` - Additional test memories
- `vector_data/` - Vector database test files

## Usage

1. Test FAISS functionality:

```bash
python faiss_test.py
```

2. Run the test launcher with Ollama:

```bash
./engram_with_faiss_simple.py --model llama3:8b
```

## How It Works

The test implementation:

1. **Text Embedding**: Demonstrates how to generate text embeddings for vector search
2. **Vector Storage**: Shows efficient vector search with FAISS
3. **Memory API**: Provides an API-compatible implementation of Engram's MemoryService
4. **Runtime Integration**: Shows how to integrate with Engram at runtime

## Memory Operations

You can test memory operations with commands like:

```
REMEMBER This is an important fact about FAISS vector search.

SEMANTIC SEARCH How does vector search work?

CONTEXT SEARCH FAISS library
```

## Notes

- All memory operations work as they do in standard Engram
- The test vector database is stored in the `memories` and `test_memories` directories
- For production use, refer to the main Engram implementation in the core directory