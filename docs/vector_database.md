# Vector Database Integration in Engram

This document provides information about Engram's vector database integration, which enables semantic search capabilities across memory stores.

## Overview

Engram uses vector databases to store and retrieve memories based on semantic similarity. This provides significant advantages over simple keyword matching:

1. **Semantic Search**: Find memories based on meaning rather than exact word matches
2. **Better Context Relevance**: Retrieve memories that are conceptually related to queries
3. **Enhanced Memory Retrieval**: Improve the quality of AI assistant responses by providing the most relevant context

## Supported Vector Databases

Engram currently supports the following vector database implementations:

1. **ChromaDB** (Primary Implementation)
   - Fast, lightweight vector database
   - Persistent storage with automatic collection management
   - Low resource requirements
   - Supports custom embedding models

## Installation Requirements

To use the vector database functionality, you need to install the following Python packages:

```bash
# Install required packages
pip install chromadb>=0.6.0 sentence-transformers>=2.2.2
```

You can also use the provided setup utility to verify your installation:

```bash
python vector_db_setup.py --test
```

## Embeddings

Engram uses the `sentence-transformers` library to generate embeddings from text. By default, it uses the `all-MiniLM-L6-v2` model, which provides:

- Good semantic representation with a vector size of 384 dimensions
- Fast inference speed
- Reasonable memory usage
- Good balance of performance and resource requirements

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

1. If ChromaDB is not installed, the system will automatically fall back to file-based storage
2. If embedding generation fails, the system will fall back to file-based storage
3. Any errors during vector operations will trigger fallback to ensure memory operations continue to work

All core memory functionality works in fallback mode, but without the semantic search capabilities.

## Testing Vector Database Functionality

Engram includes a utility script to verify vector database functionality:

```bash
# Test vector database setup
python vector_db_setup.py --test

# Output example
✅ NumPy version 1.26.4 is compatible
✅ Package chromadb is installed
✅ Package sentence-transformers is installed
✅ Successfully created ChromaDB test collection
✅ Successfully created embedding of size 384
✅ Successfully added document to ChromaDB
✅ Successfully queried ChromaDB
✅ Vector database verification successful
```

## Performance Considerations

### Resource Usage

- ChromaDB stores indexes and data on disk by default
- Embedding generation is computationally intensive but happens once per memory
- Search operations are fast and efficient once embeddings are generated

### Scaling

- For large memory collections (>100k memories), consider:
  - Using a dedicated machine for the memory service
  - Monitoring memory usage and disk space
  - Implementing memory pruning strategies

## Integration with Engram

The vector database is integrated into several key components:

1. **Memory Service**: Core storage and retrieval with namespace support
2. **Structured Memory**: Higher-level organization with importance ranking
3. **Nexus Interface**: Unified API for context-aware AI assistants

## API Impact

Using vector database does not change Engram's API. All existing endpoints work the same way, but with enhanced semantic search capabilities.

## Troubleshooting

Common issues and solutions:

1. **Missing Dependencies**:
   ```
   Error: No module named 'chromadb'
   ```
   Solution: Install required dependencies with `pip install chromadb sentence-transformers`

2. **Fallback Mode Active**:
   ```
   INFO - engram.memory - Using fallback file-based memory implementation
   ```
   Solution: Ensure ChromaDB is installed and `ENGRAM_USE_FALLBACK` is not set

3. **Performance Issues**:
   - If searches are slow, check if you're running on CPU instead of GPU
   - For large collections, consider optimizing database parameters
   - Monitor memory usage and index size

## Future Enhancements

Planned improvements for the vector database integration:

1. Support for additional vector database backends (Milvus, Weaviate, etc.)
2. Customizable embedding models to balance performance and accuracy
3. Hybrid search combining vector and keyword search
4. Improved memory pruning and consolidation strategies
5. Enhanced telemetry control options

## Telemetry Note

ChromaDB has anonymized telemetry enabled by default. If you wish to disable this, you can set the environment variable:

```bash
export ANONYMIZED_TELEMETRY=False
```

This will prevent ChromaDB from sending any telemetry data.

## Related Documentation

- [Memory Management](memory_management.md): Core memory concepts in Engram
- [Structured Memory](structured_memory.md): Higher-level memory organization
- [Configuration](configuration.md): General configuration options
- [Consolidated Server](consolidated_server.md): Server that provides memory services