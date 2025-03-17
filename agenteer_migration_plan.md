# Agenteer to Engram Migration Plan

## Overview

This document outlines the plan for migrating Agenteer from using the Claude Memory Bridge (CMB) to the new Engram package while maintaining backward compatibility.

## Current Integration

Agenteer uses CMB in two main places:

1. **`cmb_adapter.py`** - Core memory integration that handles:
   - Direct imports from `cmb.cli.quickmem` and `cmb.core.*` modules
   - Fallbacks when CMB is not available
   - HTTP API access to CMB services

2. **`nexus/generator.py`** - Creates Nexus agents with memory tools that depend on CMB

## Migration Strategy

### Step 1: Update Imports

Update import statements in both files:

```python
# Original
from cmb.cli.quickmem import (
    status, process_message, start_nexus, end_nexus, auto_remember,
    memory_digest, s, q, n, y, z, d
)

# Updated
try:
    # Try engram package first
    from engram.cli.quickmem import (
        status, process_message, start_nexus, end_nexus, auto_remember,
        memory_digest, s, q, n, y, z, d
    )
except ImportError:
    # Fall back to legacy cmb package
    from cmb.cli.quickmem import (
        status, process_message, start_nexus, end_nexus, auto_remember,
        memory_digest, s, q, n, y, z, d
    )
```

### Step 2: Update Environment Variables

Add support for both CMB and Engram environment variables in the CmbAdapter:

```python
def __init__(self, agent_id: int, agent_name: str = None):
    self.agent_id = agent_id
    self.agent_name = agent_name or f"Agent-{agent_id}"
    self.client_id = f"agenteer_{agent_id}"
    
    # Set both environment variables for compatibility
    os.environ["ENGRAM_CLIENT_ID"] = self.client_id
    os.environ["CMB_CLIENT_ID"] = self.client_id
```

### Step 3: Update Core Component Imports

Update direct core component imports in the CmbAdapter:

```python
try:
    # Try engram core first
    from engram.core.structured_memory import StructuredMemory
    from engram.core.nexus import NexusInterface
    from engram.core.memory import MemoryService as CmbMemoryService
    HAS_CMB_CORE = True
except ImportError:
    # Fall back to cmb core
    try:
        from cmb.core.structured_memory import StructuredMemory
        from cmb.core.nexus import NexusInterface
        from cmb.core.memory import MemoryService as CmbMemoryService
        HAS_CMB_CORE = True
    except ImportError:
        HAS_CMB_CORE = False
```

### Step 4: Update HTTP URLs

Update HTTP URL handling for API access:

```python
# Default HTTP URL for the Engram/CMB wrapper
DEFAULT_HTTP_URL = "http://127.0.0.1:8000/http"

def _get_http_url():
    """Get the HTTP URL for Engram/CMB wrapper."""
    return os.environ.get("ENGRAM_HTTP_URL", 
                         os.environ.get("CMB_HTTP_URL", 
                                       DEFAULT_HTTP_URL))
```

### Step 5: Update Process Detection

Improve process detection to find both Engram and CMB services:

```python
def _check_cmb_status(start_if_not_running: bool = False) -> bool:
    # Check for both engram and cmb processes
    try:
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "engram.api.consolidated_server|cmb.api.consolidated_server"],
            capture_output=True
        )
        if result.returncode == 0:
            return True
    except Exception:
        pass
        
    # ... rest of the function
```

## Testing and Validation

After implementation, we should:

1. Test Agenteer with:
   - Only Engram installed
   - Only CMB installed
   - Both installed
   - Neither installed (fallback mode)

2. Verify functionality:
   - Memory storage and retrieval
   - Context generation
   - Nexus agent operation

## Future Work

Once the migration is stable and verified, we can:

1. Gradually deprecate CMB-specific code paths
2. Remove the CMB package dependency
3. Rename `cmb_adapter.py` to `engram_adapter.py` with appropriate redirects
4. Update documentation to reference Engram instead of CMB
5. Adjust Agenteer's requirements.txt to list Engram as a dependency