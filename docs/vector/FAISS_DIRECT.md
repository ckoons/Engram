# Direct FAISS Integration

This document explains the direct FAISS integration approach for Engram vector database functionality, which is the recommended method for vector search capabilities.

## Overview

The direct FAISS integration uses runtime patching to modify Engram's memory system to use FAISS for vector operations. This approach:

- Works with all NumPy versions including NumPy 2.x
- Doesn't require a separate virtual environment
- Directly patches the memory system at runtime
- Provides seamless vector search capabilities

## How It Works

The direct FAISS integration works through `engram_memory_patch.py`, which:

1. Dynamically imports the Engram memory system
2. Patches the vector search methods to use FAISS
3. Creates a compatible interface between FAISS and the existing memory system
4. Automatically falls back to file-based storage if needed

## Setup and Usage

To use the direct FAISS integration:

```bash
# Launch Ollama with direct FAISS integration
./engram_with_ollama_direct --model llama3:8b
```

This uses the `engram_with_ollama_direct` script, which:
1. Loads the memory patch system
2. Configures the Ollama bridge with appropriate settings
3. Initializes the memory system with FAISS support
4. Connects to Ollama and enables memory operations

No manual setup or separate virtual environment is needed, making this the simplest approach.

## Advantages

- **Simplicity**: No virtual environment setup required
- **Compatibility**: Works with all NumPy versions including 2.x
- **Performance**: FAISS offers excellent performance for vector operations
- **Consistency**: Same memory API as the standard Engram system
- **Transparency**: Runtime patching is invisible to the user

## Limitations

- Requires FAISS to be installed (`pip install faiss-cpu`)
- Not suitable for GPU acceleration (using only CPU version)
- Limited to the feature set of the FAISS implementation

## Troubleshooting

If you encounter issues:

1. Make sure FAISS is installed: `pip install faiss-cpu`
2. Check for NumPy compatibility: `pip show numpy`
3. If errors persist, try the virtual environment approach instead