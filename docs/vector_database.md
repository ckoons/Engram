# Vector Database Integration in Engram

This document provides information about Engram's vector database integration, which enables semantic search capabilities across memory stores.

## Overview

Engram uses vector databases to store and retrieve memories based on semantic similarity. This provides significant advantages over simple keyword matching:

1. **Semantic Search**: Find memories based on meaning rather than exact word matches
2. **Better Context Relevance**: Retrieve memories that are conceptually related to queries
3. **Enhanced Memory Retrieval**: Improve the quality of AI assistant responses by providing the most relevant context

## Supported Vector Databases

Engram currently supports the following vector database implementations:

1. **FAISS (Facebook AI Similarity Search)** - Primary Implementation
   - High-performance similarity search and clustering
   - NumPy 2.x compatible (works with any NumPy version)
   - Optional GPU acceleration
   - Minimal dependencies
   - Fast and efficient vector operations

## Installation Requirements

To use the vector database functionality, you need to install the following Python packages:

```bash
# Install required packages
pip install faiss-cpu  # Basic CPU version
# OR
pip install faiss-gpu  # GPU-accelerated version (requires CUDA)
```

You can also use the provided setup utility to verify your installation:

```bash
python vector_db_setup.py --test
```

## Embeddings

Engram uses a simple deterministic embedding approach that doesn't require external models like sentence-transformers:

- Lightweight embedding generation that works with any Python environment
- Consistent 128-dimensional embeddings
- Token-based approach with TF-IDF inspired weighting
- Deterministic results for the same input text
- No large model downloads required

While this approach may not match the semantic quality of deep learning models like sentence-transformers, it provides good results for memory retrieval with minimal dependencies.

## Configuration

The vector database functionality can be configured through environment variables:

- `ENGRAM_USE_FALLBACK`: Set to `1`, `true`, or `yes` to force using file-based storage instead of vector database.
- `ENGRAM_DATA_DIR`: Directory where vector database files will be stored (defaults to `~/.engram`).
- `ENGRAM_CLIENT_ID`: Client identifier for separating different memory contexts.

You can also use command-line options when starting the consolidated server:

```bash
# Start with file-based fallback
./engram_consolidated --fallback

# Custom data directory
./engram_consolidated --data-dir /path/to/data
```

## Automatic Fallback Mode

Engram is designed to gracefully degrade if vector database components are not available:

1. If FAISS is not installed, the system will automatically fall back to file-based storage
2. If embedding generation fails, the system will fall back to file-based storage
3. Any errors during vector operations will trigger fallback to ensure memory operations continue to work

All core memory functionality works in fallback mode, but without the semantic search capabilities.

## Testing Vector Database Functionality

Engram includes a utility script to verify vector database functionality:

```bash
# Test vector database setup
python vector_db_setup.py --test

# Output example
✅ NumPy version 2.0.0 is compatible
✅ Package faiss-cpu is installed
✅ Successfully created FAISS test index
✅ Successfully created embedding of size 128
✅ Successfully added document to FAISS
✅ Successfully queried FAISS
✅ Vector database verification successful
```

## Performance Considerations

### Resource Usage

- FAISS stores indexes and data on disk only when saved
- Embedding generation is fast and efficient
- Search operations are optimized for speed
- GPU acceleration can significantly improve performance for large collections

### Scaling

- For large memory collections (>100k memories), consider:
  - Using GPU acceleration with `faiss-gpu`
  - Monitoring memory usage and disk space
  - Implementing memory pruning strategies

## Integration with Engram

The vector database is integrated into several key components:

1. **Memory Service**: Core storage and retrieval with namespace support
2. **Structured Memory**: Higher-level organization with importance ranking
3. **Nexus Interface**: Unified API for context-aware AI assistants

## API Impact

Using vector database does not change Engram's API. All existing endpoints work the same way, but with enhanced semantic search capabilities.

## Migration from ChromaDB

If you previously used ChromaDB with Engram, your existing memories will need to be manually migrated to the new FAISS implementation. The simplest approach is:

1. Use the `search` method to retrieve all memories from each namespace in ChromaDB
2. Use the `add` method to add them to the new FAISS implementation
3. Verify that all memories have been transferred correctly

## Troubleshooting

Common issues and solutions:

1. **Missing Dependencies**:
   ```
   Error: No module named 'faiss'
   ```
   Solution: Install required dependencies with `pip install faiss-cpu`

2. **Fallback Mode Active**:
   ```
   INFO - engram.memory - Using fallback file-based memory implementation
   ```
   Solution: Ensure FAISS is installed and `ENGRAM_USE_FALLBACK` is not set

3. **Performance Issues**:
   - If searches are slow, consider using GPU acceleration with `faiss-gpu`
   - For large collections, consider optimizing index parameters
   - Monitor memory usage and index size

## Future Enhancements

Planned improvements for the vector database integration:

1. Enhanced embedding quality with optional integration of more sophisticated models
2. Hybrid search combining vector and keyword search
3. Improved memory pruning and consolidation strategies
4. Additional index types for different performance characteristics

## Related Documentation

- [Memory Management](memory_management.md): Core memory concepts in Engram
- [Structured Memory](structured_memory.md): Higher-level memory organization
- [Configuration](configuration.md): General configuration options
- [Consolidated Server](consolidated_server.md): Server that provides memory services