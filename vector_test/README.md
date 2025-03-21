# FAISS Vector Storage for Engram

This directory contains a simplified vector storage solution for Engram that works with NumPy 2.x.

## Background

Engram's vector search functionality normally depends on:
1. SentenceTransformers for text embedding
2. ChromaDB or Qdrant for vector storage

However, these libraries have dependencies on NumPy 1.x and don't work with NumPy 2.x, causing compatibility issues. This implementation provides a solution that works with NumPy 2.x by using:

1. A simple text embedding system that doesn't depend on transformers
2. FAISS for high-performance vector search

## Files

- `faiss_test.py` - A simple test script to verify FAISS works with NumPy 2.x
- `simple_embedding.py` - A basic text embedding implementation without dependencies on transformer models
- `vector_store.py` - A vector database implementation using FAISS
- `engram_memory_adapter.py` - An adapter that implements Engram's memory API using FAISS
- `engram_with_faiss_simple.py` - A launcher script for Engram with Ollama and FAISS

## Usage

1. First, test that FAISS works with your NumPy version:

```bash
python faiss_test.py
```

2. Make the launcher executable:

```bash
chmod +x engram_with_faiss_simple.py
```

3. Run Engram with Ollama using the FAISS adapter:

```bash
./engram_with_faiss_simple.py --model llama3:8b
```

## How It Works

This implementation:

1. **Text Embedding**: Uses a simple TF-IDF-like approach to generate text embeddings without dependencies on transformer models
2. **Vector Storage**: Uses FAISS for efficient vector search, which works with NumPy 2.x
3. **Memory API**: Provides an API-compatible replacement for Engram's MemoryService class
4. **Runtime Patching**: Replaces Engram's memory module at runtime with our FAISS-based implementation

## Limitations

The simple embedding system isn't as sophisticated as SentenceTransformers, so the quality of semantic search will be lower. However, it provides a functional solution until the underlying libraries add support for NumPy 2.x.

## Future Improvements

1. Add support for more sophisticated embedding methods
2. Optimize vector search parameters
3. Add more memory operations and features
4. Create a seamless migration path for existing ChromaDB memories

## Testing Memory Operations

You can test memory operations with commands like:

```
REMEMBER This is an important fact about FAISS vector search.

SEMANTIC SEARCH How does vector search work?

CONTEXT SEARCH FAISS library
```

## Notes

- All memory operations should work as they do in standard Engram
- The vector database is stored in the `memories` directory
- No virtual environment is needed, as all dependencies work with NumPy 2.x