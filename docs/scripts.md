# Engram Script Reference

This guide explains all the executable scripts and utilities available in Engram and when to use them.

## User Scripts

These scripts are intended for regular use:

| Script | Description | Use When |
|--------|-------------|----------|
| **`engram_with_claude`** | Starts memory service and launches Claude | Starting a new Claude session with memory |
| **`engram_with_ollama`** | Starts memory service and launches Ollama | Starting a new Ollama session with memory |
| **`engram_with_ollama_direct`** | Launches Ollama with FAISS via runtime patch | Using Ollama with direct FAISS integration |
| **`engram_with_ollama_faiss`** | Launches Ollama with FAISS via virtual env | Using Ollama with FAISS in dedicated environment |
| **`engram_consolidated`** | Starts the consolidated memory server | Running just the memory service |
| **`engram_config`** | Interactive configuration tool | Changing settings or viewing configuration |
| **`engram_start_web`** | Starts memory service and web UI | Managing memories through a web interface |
| **`engram_check.py`** | Checks service status | Diagnosing or managing services |

## Memory Helpers

These scripts are helpful for starting and ending memory sessions:

| Script | Description | Usage |
|--------|-------------|-------|
| **`utils/engram_memory_start.py`** | Python helper to initialize memory | `from utils.engram_memory_start import start_memory` |
| **`utils/engram_memory_end.py`** | Python helper to store session summary | `from utils.engram_memory_end import end_session` |
| **`utils/engram_memory_patch.py`** | Runtime patch for FAISS integration | Used by `engram_with_ollama_direct` |

## Utility Scripts

The `/utils` directory contains utilities for various functions:

| Category | Description | Location |
|----------|-------------|----------|
| **AI Communication** | Scripts for AI-to-AI communication | `utils/ai_communication/` |
| **Vector Database** | Setup and configuration for vector databases | `utils/vector_db_setup.py` |
| **Ollama Integration** | Setup scripts for Ollama environments | `utils/setup_ollama_env*.sh` |
| **Multi-Claude Support** | Utilities for multiple Claude instances | `utils/multi_claude.sh`, etc. |
| **Testing Utilities** | Scripts for testing and data generation | `utils/add_test_data.py` |

## Vector Database Integration

The `/vector` directory contains components for vector database functionality:

| Component | Description | Location |
|-----------|-------------|----------|
| **FAISS Adapter** | Virtual environment with FAISS | `vector/ollama_faiss_venv/` |
| **Test Environment** | Test scripts and data for vector databases | `vector/test/` |

## Low-Level Scripts

These scripts are for advanced usage or compatibility:

| Script | Description | Notes |
|--------|-------------|-------|
| **`engram_server`** | Core memory server only | Legacy script for individual services |
| **`engram_http`** | HTTP wrapper only | Legacy script for individual services |

## Using the Scripts

### Starting Claude with Memory

The simplest way to start Engram with Claude is:

```bash
./engram_with_claude
```

This script:
1. Starts the consolidated memory server if needed
2. Launches Claude with memory functions pre-loaded
3. Enables access to previous memories

### Starting Ollama with Memory

To use Ollama models with Engram:

```bash
# Recommended approach (FAISS via runtime patch)
./engram_with_ollama_direct --model llama3:8b

# Alternative approach (FAISS via virtual environment)
./engram_with_ollama_faiss --model llama3:8b
```

### Manual Memory Management

For more control, you can start services separately:

```bash
# Start the memory service
./engram_consolidated 

# In Claude or Python, load memory functions
from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v
```

### Web UI

To manage memories through a web interface:

```bash
./engram_start_web
```

This opens a web UI where you can browse, search, and manage memories.

### Configuration

To customize Engram settings:

```bash
# Interactive configuration
./engram_config

# Show current settings
./engram_config --show

# Edit configuration file
./engram_config --edit
```

## Customizing Settings

All scripts accept command-line parameters to override default settings:

```bash
# Change port and client ID
./engram_consolidated --port 9000 --client-id custom

# Start with a custom config file
./engram_consolidated --config ~/my_engram_config.json

# Disable automatic agency
./engram_consolidated --no-auto-agency
```

## Environment Variables

You can also set environment variables to control behavior:

```bash
# Set port and client ID
export ENGRAM_PORT=9000
export ENGRAM_CLIENT_ID=custom

# Enable fallback mode if vector database isn't working
export ENGRAM_USE_FALLBACK=1

# Then run
./engram_consolidated
```