# CMB Directory Removal Plan

This document outlines the plan for removing the legacy `cmb` (Claude Memory Bridge) directory in favor of the consolidated `engram` package. The `cmb` package is now redundant, as all functionality has been migrated to the `engram` package.

## Background

The `cmb` directory was originally created as the primary package for the Claude Memory Bridge system. Over time, functionality was migrated to the `engram` package, and the `cmb` package was maintained only for backward compatibility.

Now that the FAISS migration is complete and the system has been consolidated, it's time to remove the redundant code to simplify maintenance.

## Files to Remove

The following directories and files will be removed:

```
cmb/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── consolidated_server.py
│   ├── http_wrapper.py
│   └── server.py
├── cli/
│   ├── __init__.py
│   ├── claude_helper.py
│   ├── claude_launcher.py
│   ├── comm_quickmem.py
│   ├── http_helper.py
│   └── quickmem.py
├── core/
│   ├── __init__.py
│   ├── async_protocol.py
│   ├── behavior_logger.py
│   ├── claude_comm.py
│   ├── crypto.py
│   ├── memory.py
│   ├── mode_detection.py
│   ├── nexus.py
│   ├── orchestrator.py
│   ├── report_generator.py
│   └── structured_memory.py
└── web/
    ├── __init__.py
    └── app.py
```

## Migration Strategy

1. **Create Import Redirection Package**:
   - Create a standalone package called `cmb_compat` with import redirection
   - Users can install this separately if they need backward compatibility

2. **Create Migration Documentation**:
   - Document the migration path in a clear guide
   - Provide import substitution examples

3. **Update Scripts**:
   - Update all scripts to use `engram` module imports
   - Add fallback imports for compatibility

4. **Package Changes**:
   - Update `setup.py` to remove `cmb` package
   - Add note about the separation

## Import Mapping

Here's the mapping from old `cmb` imports to new `engram` imports:

| Old Import | New Import |
|------------|------------|
| `from cmb.core.memory import MemoryService` | `from engram.core.memory_faiss import MemoryService` |
| `from cmb.core.structured_memory import StructuredMemory` | `from engram.core.structured_memory import StructuredMemory` |
| `from cmb.core.nexus import NexusInterface` | `from engram.core.nexus import NexusInterface` |
| `from cmb.api.consolidated_server import start_server` | `from engram.api.consolidated_server import start_server` |
| `from cmb.cli.quickmem import *` | `from engram.cli.quickmem import *` |
| `from cmb.web.app import app` | `from engram.web.app import app` |

## Timeline

1. **Phase 1** - Preparation (Current):
   - Document all import paths that need to change
   - Create compatibility layer (if needed)
   - Update all existing scripts

2. **Phase 2** - Soft Removal:
   - Mark `cmb` as deprecated in documentation
   - Create warning in `cmb/__init__.py` that directs users to use `engram`
   - Keep the package for 1-2 more versions

3. **Phase 3** - Hard Removal:
   - Remove `cmb` package completely
   - Update all documentation to reference only `engram`

## Migration Guide for Users

### For Simple Use Cases

```python
# Old import
from cmb.core.memory import MemoryService
from cmb.cli.quickmem import memory_digest, start_nexus

# New import
from engram.core.memory_faiss import MemoryService
from engram.cli.quickmem import memory_digest, start_nexus
```

### For Comprehensive Migration

Replace all imports from `cmb.*` to `engram.*` with the same subpath.

### For Running Scripts

Update any script invocations:

```bash
# Old approach
python -m cmb.api.server

# New approach
python -m engram.api.server
```

## Conclusion

Removing the redundant `cmb` package will simplify the codebase, reduce maintenance overhead, and provide a clearer API for users. The migration path is straightforward, as the `engram` package has maintained API compatibility with the `cmb` package.