# Engram Project Reorganization Plan

This document outlines a comprehensive plan to reorganize the Engram project structure for better maintainability.

## 1. Directory Structure

Create the following structure:
```
/Users/cskoons/projects/github/Engram/
├── engram/            # Core Engram code
├── ollama/            # Ollama integration code
├── utils/             # Utility scripts and helpers
├── vector/            # Vector database implementations
└── [symlinks]         # Root symlinks to commonly used scripts
```

## 2. File Migrations

### 2.1 Move Ollama-specific files to ollama/ directory

| Current Location | New Location | Type | Notes |
|------------------|--------------|------|-------|
| `/Engram/ollama_bridge.py` | `/Engram/ollama/ollama_bridge.py` | Implementation | Core Ollama integration |
| `/Engram/ollama_system_prompts.py` | `/Engram/ollama/ollama_system_prompts.py` | Implementation | Ollama prompts library |
| `/Engram/ollama_mcp` | `/Engram/ollama/ollama_mcp` | Launcher | Ollama MCP server | 
| `/Engram/engram_with_ollama` | `/Engram/ollama/engram_with_ollama` | Launcher | Basic Ollama launcher |
| `/Engram/engram_with_ollama_direct` | `/Engram/ollama/engram_with_ollama_direct` | Launcher | Direct Ollama integration |
| `/Engram/engram_with_ollama_faiss` | `/Engram/ollama/engram_with_ollama_faiss` | Launcher | Ollama with FAISS |
| `/Engram/engram_with_ollama_lancedb` | `/Engram/ollama/engram_with_ollama_lancedb` | Launcher | Ollama with LanceDB |
| `/Engram/engram_ollama_dual` | `/Engram/ollama/engram_ollama_dual` | Launcher | Dual server (Engram+Ollama) |
| `/Engram/engram_smart_launch_ollama` | `/Engram/ollama/engram_smart_launch_ollama` | Launcher | Smart Ollama launcher |

### 2.2 Move utility scripts to utils/ directory

| Current Location | New Location | Type | Notes |
|------------------|--------------|------|-------|
| `/Engram/debug_server.py` | `/Engram/utils/debug_server.py` | Debug | Already moved |
| `/Engram/debug_ollama_mcp.py` | `/Engram/utils/debug_ollama_mcp.py` | Debug | Already moved |
| `/Engram/engram_check.py` | `/Engram/utils/engram_check.py` | Utility | Service status checker |
| `/Engram/engram_check_dual.py` | `/Engram/utils/engram_check_dual.py` | Utility | Dual server checker |
| `/Engram/engram_kill` | `/Engram/utils/engram_kill` | Utility | Process terminator |
| `/Engram/engram_config` | `/Engram/utils/engram_config` | Utility | Configuration helper |

### 2.3 Keep essential launchers in root with symlinks

The following files should remain in the root directory (or be symlinked from their new locations):

| File | Type | Notes |
|------|------|-------|
| `engram_consolidated` | Launcher | Main entry point |
| `engram_dual` | Launcher | Dual mode HTTP/MCP |
| `engram_mcp` | Launcher | MCP-only mode |
| `engram_http` | Launcher | HTTP-only mode |
| `engram_smart_launch` | Launcher | Auto-detect best vector DB |
| `engram_with_claude` | Launcher | Claude integration |

## 3. Code Changes Required

### 3.1 Update imports in ollama_bridge.py

Current:
```python
from ollama_system_prompts import (
    get_memory_system_prompt,
    get_communication_system_prompt, 
    get_combined_system_prompt,
    get_model_capabilities
)
```

New:
```python
from ollama.ollama_system_prompts import (
    get_memory_system_prompt,
    get_communication_system_prompt, 
    get_combined_system_prompt,
    get_model_capabilities
)
```

### 3.2 Update imports in new ollama_mcp_adapter.py

Current:
```python
try:
    from ollama_system_prompts import (
        get_memory_system_prompt,
        get_communication_system_prompt, 
        get_combined_system_prompt,
        get_model_capabilities
    )
    SYSTEM_PROMPTS_AVAILABLE = True
except ImportError:
    logger.warning("Ollama system prompts not available, will use default prompts")
    SYSTEM_PROMPTS_AVAILABLE = False
```

New:
```python
try:
    from engram.ollama.ollama_system_prompts import (
        get_memory_system_prompt,
        get_communication_system_prompt, 
        get_combined_system_prompt,
        get_model_capabilities
    )
    SYSTEM_PROMPTS_AVAILABLE = True
except ImportError:
    logger.warning("Ollama system prompts not available, will use default prompts")
    SYSTEM_PROMPTS_AVAILABLE = False
```

### 3.3 Update paths in utils/detect_best_vector_db.py

This script should be updated to reference the new locations of launcher scripts.

### 3.4 Update paths in utils/launch_best_vector_db.sh

This script should be updated to reference the new locations of launcher scripts.

## 4. Creating Symlinks

### 4.1 Create root directory symlinks for Ollama launchers

```bash
# After moving originals to ollama/ directory
ln -s /Users/cskoons/projects/github/Engram/ollama/ollama_mcp /Users/cskoons/projects/github/Engram/ollama_mcp
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama /Users/cskoons/projects/github/Engram/engram_with_ollama
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama_direct /Users/cskoons/projects/github/Engram/engram_with_ollama_direct
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama_faiss /Users/cskoons/projects/github/Engram/engram_with_ollama_faiss
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama_lancedb /Users/cskoons/projects/github/Engram/engram_with_ollama_lancedb
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_ollama_dual /Users/cskoons/projects/github/Engram/engram_ollama_dual
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_smart_launch_ollama /Users/cskoons/projects/github/Engram/engram_smart_launch_ollama
```

### 4.2 Create root directory symlinks for utilities

```bash
# After moving originals to utils/ directory
ln -s /Users/cskoons/projects/github/Engram/utils/engram_check.py /Users/cskoons/projects/github/Engram/engram_check.py
ln -s /Users/cskoons/projects/github/Engram/utils/engram_check_dual.py /Users/cskoons/projects/github/Engram/engram_check_dual.py
ln -s /Users/cskoons/projects/github/Engram/utils/engram_kill /Users/cskoons/projects/github/Engram/engram_kill
ln -s /Users/cskoons/projects/github/Engram/utils/engram_config /Users/cskoons/projects/github/Engram/engram_config
```

### 4.3 Update ~/utils symlinks

```bash
# After moving originals to their new locations
rm /Users/cskoons/utils/engram_check_dual.py
rm /Users/cskoons/utils/engram_dual
rm /Users/cskoons/utils/engram_kill
rm /Users/cskoons/utils/engram_mcp
rm /Users/cskoons/utils/engram_smart_launch
rm /Users/cskoons/utils/engram_smart_launch_mcp
rm /Users/cskoons/utils/engram_smart_launch_ollama
rm /Users/cskoons/utils/engram_with_claude
rm /Users/cskoons/utils/engram_with_faiss_mcp
rm /Users/cskoons/utils/engram_with_lancedb
rm /Users/cskoons/utils/engram_with_lancedb_mcp
rm /Users/cskoons/utils/engram_with_ollama
rm /Users/cskoons/utils/engram_with_ollama_direct
rm /Users/cskoons/utils/engram_with_ollama_faiss
rm /Users/cskoons/utils/engram_with_ollama_lancedb

# Create new symlinks
ln -s /Users/cskoons/projects/github/Engram/utils/engram_check_dual.py /Users/cskoons/utils/engram_check_dual.py
ln -s /Users/cskoons/projects/github/Engram/engram_dual /Users/cskoons/utils/engram_dual
ln -s /Users/cskoons/projects/github/Engram/utils/engram_kill /Users/cskoons/utils/engram_kill
ln -s /Users/cskoons/projects/github/Engram/engram_mcp /Users/cskoons/utils/engram_mcp
ln -s /Users/cskoons/projects/github/Engram/engram_smart_launch /Users/cskoons/utils/engram_smart_launch
ln -s /Users/cskoons/projects/github/Engram/engram_smart_launch_mcp /Users/cskoons/utils/engram_smart_launch_mcp
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_smart_launch_ollama /Users/cskoons/utils/engram_smart_launch_ollama
ln -s /Users/cskoons/projects/github/Engram/engram_with_claude /Users/cskoons/utils/engram_with_claude
ln -s /Users/cskoons/projects/github/Engram/engram_with_faiss_mcp /Users/cskoons/utils/engram_with_faiss_mcp
ln -s /Users/cskoons/projects/github/Engram/engram_with_lancedb /Users/cskoons/utils/engram_with_lancedb
ln -s /Users/cskoons/projects/github/Engram/engram_with_lancedb_mcp /Users/cskoons/utils/engram_with_lancedb_mcp
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama /Users/cskoons/utils/engram_with_ollama
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama_direct /Users/cskoons/utils/engram_with_ollama_direct
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama_faiss /Users/cskoons/utils/engram_with_ollama_faiss
ln -s /Users/cskoons/projects/github/Engram/ollama/engram_with_ollama_lancedb /Users/cskoons/utils/engram_with_ollama_lancedb
```

## 5. Implementation Steps

The reorganization should be executed in the following order:

1. Create and verify ollama/ directory
2. Move all ollama-specific implementation files
3. Update imports and path references in the moved files
4. Move utility scripts to utils/ directory
5. Create symlinks in root directory
6. Update ~/utils symlinks
7. Test all launchers to verify functionality

## 6. Verification Tests

After reorganization, verify functionality with:

1. Start basic Engram server: `./engram_consolidated`
2. Start Ollama integration: `./engram_with_ollama`
3. Start MCP server: `./engram_mcp`
4. Start Ollama MCP server: `./ollama_mcp`
5. Run vector database tests: `./utils/vector_db_setup.py --test`

## 7. Rollback Plan

If issues arise, a rollback can be done by:

1. Restoring original files from their new locations to the root directory
2. Removing the symlinks
3. Re-linking ~/utils to the restored root files

For safety, make a backup of critical files before reorganization.