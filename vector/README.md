# Engram Vector Database Integration with FAISS

This directory contains the FAISS vector database integration for Engram, providing high-performance vector search capabilities.

## Overview

FAISS (Facebook AI Similarity Search) provides efficient similarity search and clustering of dense vectors. The Engram integration:

- Enables semantic search across memory items
- Works with both CPU and GPU for high performance
- Ensures compatibility with NumPy 2.x
- Provides a clean, isolated implementation

## Setup Instructions

### 1. Installation

To install FAISS with GPU support (recommended for performance):

```bash
# Activate your Engram virtual environment
source /path/to/engram/venv/bin/activate

# Run the installation script
python ./vector/install_faiss_gpu.py
```

For CPU-only installation:

```bash
# Activate your Engram virtual environment
source /path/to/engram/venv/bin/activate

# Install FAISS CPU version
pip install faiss-cpu
```

### 2. Testing the Installation

After installation, verify that FAISS is working properly:

```bash
# Run diagnostic script
python ./vector/test/debug_faiss.py

# Run comprehensive test
python ./vector/test/test_engram_faiss.py
```

### 3. Using FAISS with Ollama

To use Engram with Ollama and FAISS vector search:

```bash
# Make sure Ollama is running
ollama list

# Run Engram with Ollama and FAISS
./engram_with_ollama_faiss --model llama3:8b
```

## Directory Structure

- `test/` - Test scripts and example code
  - `debug_faiss.py` - Diagnostics for FAISS installation
  - `engram_memory_adapter.py` - Adapter for Engram memory system
  - `engram_with_faiss_simple.py` - Simplified Ollama + FAISS integration
  - `faiss_test.py` - Basic FAISS functionality test
  - `simple_embedding.py` - Lightweight embedding generation
  - `test_engram_faiss.py` - Integration test with Engram
  - `vector_store.py` - Core vector storage implementation

- `install_faiss_gpu.py` - Script to install FAISS with GPU support

## GPU vs CPU Considerations

- **GPU Support**: Significantly faster for large vector collections (>100K vectors)
- **CPU Version**: Works on all machines, adequate for smaller collections
- **Memory Usage**: GPU version requires GPU memory for index storage
- **Compatibility**: CPU version has broader compatibility with different environments

## Troubleshooting

If you encounter issues:

1. Check that FAISS is installed correctly:
   ```python
   import faiss
   print(faiss.__version__)
   ```

2. Verify GPU detection (for GPU version):
   ```python
   import faiss
   print(faiss.get_num_gpus())  # Should be > 0 if GPU is available
   ```

3. For "No module named 'faiss'" error:
   - Ensure you're in the correct virtual environment
   - Reinstall with `pip install faiss-cpu` or run `install_faiss_gpu.py`

4. For path-related errors:
   - Use absolute paths when running scripts
   - Ensure scripts are run from the Engram root directory

## Customization

The vector dimension, index type, and other parameters can be customized:

- **Vector Dimension**: Default is 128, can be changed in `VectorStore` initialization
- **Index Type**: Currently using `IndexFlatL2` for exact search, can be modified for approximate search
- **Memory Storage**: Default directory is `./memories`, can be changed with `--memory-dir`

For more detailed information, see the code comments in each file.