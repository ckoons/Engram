# LanceDB Integration for Engram

This integration provides high-performance vector storage and retrieval for Engram using LanceDB and PyArrow.

## Features

- Cross-platform vector database with strong performance on both Apple Silicon and CUDA GPUs
- Memory-optimized storage format with Arrow-based table structure
- Fast vector similarity search with excellent scaling for large memory collections
- Fallback mechanisms for graceful degradation when database operations fail
- Metadata caching for performance enhancement

## Requirements

- Python 3.8+
- LanceDB 0.2.0+
- PyArrow 12.0.0+
- NumPy 1.21.0+

## Installation

The integration is automatically installed when using the LanceDB launcher scripts. You can manually install it with:

```bash
python vector/lancedb/install.py
```

## Usage

### Using Launcher Scripts

The easiest way to use LanceDB with Engram is to use one of the launcher scripts:

1. **With Claude:**
   ```bash
   ./engram_with_lancedb
   ```

2. **With Ollama:**
   ```bash
   ./engram_with_ollama_lancedb
   ```

3. **Smart Launcher** (automatically selects the best vector database for your hardware):
   ```bash
   ./engram_smart_launch
   ```

### Using Smart Detection

Smart detection automatically selects the best vector database based on your hardware:

- Apple Silicon with Metal → LanceDB (optimal choice)
- CUDA GPU with FAISS-GPU → FAISS
- Other hardware → Best available between LanceDB and FAISS

## Hardware-Specific Optimizations

### Apple Silicon (M1/M2/M3)

LanceDB automatically leverages Metal performance when available on Apple Silicon. The launcher detects this and sets the appropriate environment variables:

```bash
export LANCEDB_USE_METAL=1
```

### NVIDIA GPUs

For NVIDIA GPUs, CUDA acceleration is automatically enabled when available:

```bash
export LANCEDB_USE_CUDA=1
```

## Architecture

The LanceDB integration consists of these key components:

1. **LanceDBAdapter**: The adapter layer between Engram's memory system and LanceDB, implementing the same interface as the FAISS adapter for easy swapping.

2. **VectorStore**: The LanceDB vector store implementation, handling vector operations and metadata storage.

3. **Installation Script**: Installs and sets up LanceDB for use with Engram.

4. **Launcher Scripts**: Simplify using LanceDB with different Engram configurations.

5. **Smart Detection**: Automatically selects the best vector database for the current hardware.

## Directory Structure

```
vector/
├── lancedb/
│   ├── adapter.py         # LanceDB adapter implementation
│   ├── install.py         # Installation script
│   ├── README.md          # This documentation
│   ├── simple_test.py     # Basic LanceDB test script
│   ├── test_lancedb.py    # LanceDB integration tests
│   ├── test_vector_db.py  # Comprehensive vector database tests
│   └── vector_store.py    # LanceDB vector store implementation
└── ...
```

## Implementation Details

### Vector Embedding

The system uses a simple yet effective embedding generator for producing vector representations:

- Deterministic vector generation for consistent performance
- Token-based approach with stable random vectors for each token
- TF-IDF-like algorithm for creating document embeddings
- Supports cosine similarity for semantic search

### Compartment System

Memory is organized into compartments, which are implemented as separate tables in LanceDB:

- Each compartment is a separate LanceDB table
- Metadata caching for performance optimization
- Support for isolation between different types of memories
- Fallback to JSON-based metadata storage when database operations fail

### Performance Considerations

- Metadata caching reduces read operations by keeping frequently accessed information in memory
- Automatic retrieval of similar memories with tunable parameters
- Arrow-based storage format provides memory-efficient storage and retrieval
- Platform-specific optimizations enhance performance on different hardware
- Robust error handling and fallback mechanisms ensure system reliability

## Troubleshooting

If you encounter issues with the LanceDB integration:

1. Ensure LanceDB and its dependencies are properly installed:
   ```bash
   python -c "import lancedb, pyarrow; print(f'LanceDB: {lancedb.__version__}, PyArrow: {pyarrow.__version__}')"
   ```

2. Run the simple test script to verify basic functionality:
   ```bash
   python vector/lancedb/simple_test.py
   ```

3. Check the log output for specific error messages.

4. Ensure the memories directory exists and is writable:
   ```bash
   mkdir -p memories/lancedb
   ```

## Contributing

Contributions to improve the LanceDB integration are welcome. Areas for enhancement include:

- Optimizing vector search performance for specific use cases
- Improving cross-platform compatibility
- Adding support for more complex metadata filtering
- Enhancing the embedding algorithm for better semantic matches