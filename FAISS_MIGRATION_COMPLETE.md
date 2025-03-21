# FAISS Migration Complete

Engram now uses FAISS for vector storage and similarity search instead of ChromaDB. This migration provides several benefits:

1. **NumPy 2.x Compatibility**: Works with any version of NumPy, including NumPy 2.x
2. **Simplified Dependencies**: No longer requires sentence-transformers or ChromaDB
3. **Enhanced Performance**: FAISS is highly optimized for vector search operations
4. **GPU Support**: Optional GPU acceleration for large-scale vector operations
5. **Deterministic Embeddings**: Consistent results with simple embedding technique

## Key Changes

- Replaced ChromaDB with FAISS for vector storage
- Implemented a simple deterministic embedding generator that doesn't require external models
- Updated `requirements.txt` and `setup.py` to use FAISS instead of ChromaDB
- Created a completely new implementation of the memory system in `memory_faiss.py`
- Made the FAISS implementation the default for all memory operations

## Using the New Implementation

The new implementation is fully backward compatible with existing code. All the memory functionality remains the same, but under the hood, it now uses FAISS instead of ChromaDB.

```python
# Example usage remains the same
from engram.core.memory import MemoryService

# Initialize memory service
memory_service = MemoryService(client_id="my-client")

# Use memory operations as before
await memory_service.add("This is a test memory", namespace="conversations")
results = await memory_service.search("test", namespace="conversations")
```

## Installation

The installation process has been simplified:

```bash
pip install faiss-cpu numpy  # Optional: faiss-gpu for GPU support
pip install -e .  # Install Engram in development mode
```

## Performance and Quality

The FAISS implementation uses a simple but effective embedding technique that provides good semantic matching capabilities without external dependencies. While the semantic quality may not match specialized language models like sentence-transformers, it works well for most memory retrieval use cases and provides consistent results.

## Migration from ChromaDB

If you have existing ChromaDB memories, they will need to be manually migrated to the new FAISS implementation. The simplest approach is to export your memories from ChromaDB and import them into the new FAISS implementation:

1. Use the `search` method to retrieve all memories from each namespace in ChromaDB
2. Use the `add` method to add them to the new FAISS implementation
3. Verify that all memories have been transferred correctly

## Troubleshooting

If you encounter any issues with the new implementation:

1. Ensure FAISS is installed correctly: `pip install faiss-cpu`
2. Check that you have write permissions to the data directory
3. Try running with the `--fallback` flag to use file-based storage without vectors
4. Review logs for detailed error messages

For support or to report issues, please open an issue on the GitHub repository.