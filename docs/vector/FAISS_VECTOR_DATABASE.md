# FAISS Vector Database Integration

This document explains the virtual environment approach for FAISS integration with Engram, providing an alternative method for vector database support.

## Overview

The virtual environment FAISS integration creates a dedicated Python environment with FAISS and NumPy compatibility. This approach:

- Uses a separate virtual environment to avoid conflicts
- Provides a clean, isolated environment for FAISS
- Works with all NumPy versions including 2.x
- Offers high performance for vector operations

## How It Works

The virtual environment integration uses:

1. A dedicated virtual environment (`vector/ollama_faiss_venv`)
2. Custom scripts for launching Ollama with this environment
3. A FAISS adapter that ensures compatibility with Engram
4. Special setup scripts to create and configure the environment

## Setup and Usage

To use the virtual environment FAISS integration:

```bash
# First time: Set up the virtual environment
./utils/setup_ollama_env_with_faiss.sh

# Launch Ollama with FAISS virtual environment
./engram_with_ollama_faiss --model llama3:8b
```

The setup script:
1. Creates a virtual environment with Python 3.8+
2. Installs NumPy and FAISS
3. Creates a custom adapter for FAISS
4. Configures the launcher script

## Advantages

- **Isolation**: Keeps dependencies separate from main environment
- **Compatibility**: Works with all NumPy versions
- **Customization**: Tailored environment just for vector operations
- **Reproducibility**: Consistent environment across systems

## Limitations

- Requires additional setup step
- Uses more disk space for the virtual environment
- Slightly more complex than the direct integration

## Vector Test Environment

The `vector/test/` directory contains:
- Test scripts for FAISS functionality
- Sample vector databases
- Test memories for verification
- Custom adapter implementations

This provides a testing environment for the FAISS integration.

## Troubleshooting

If you encounter issues:

1. Delete the virtual environment and re-run setup:
   ```bash
   rm -rf vector/ollama_faiss_venv/
   ./utils/setup_ollama_env_with_faiss.sh
   ```

2. Ensure Python 3.8+ is available on your system

3. Check for any error messages during setup

4. Try the direct FAISS integration as an alternative