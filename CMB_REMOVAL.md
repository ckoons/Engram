# CMB Directory Has Been Removed

The `cmb` (Claude Memory Bridge) directory has been removed from the repository. All functionality has been migrated to the `engram` package.

## Migration Guide

If you were using imports from the `cmb` package, please update your code to use the `engram` package instead.

### Common Import Changes

| Old Import | New Import |
|------------|------------|
| `from cmb.core.memory import MemoryService` | `from engram.core.memory_faiss import MemoryService` |
| `from cmb.core.structured_memory import StructuredMemory` | `from engram.core.structured_memory import StructuredMemory` |
| `from cmb.core.nexus import NexusInterface` | `from engram.core.nexus import NexusInterface` |
| `from cmb.api.consolidated_server import start_server` | `from engram.api.consolidated_server import start_server` |
| `from cmb.cli.quickmem import *` | `from engram.cli.quickmem import *` |
| `from cmb.web.app import app` | `from engram.web.app import app` |

### Temporary Compatibility

If you need temporary compatibility while migrating your code, you can use the `cmb_compat.py` module:

```python
# At the beginning of your script
import sys
import os
sys.path.append('/path/to/engram')
import cmb_compat

# Then continue to use cmb imports, which will be redirected to engram
from cmb.core.memory import MemoryService
from cmb.core.structured_memory import StructuredMemory
```

This compatibility layer is provided as a temporary measure and will be removed in a future version.

## Why Was the CMB Directory Removed?

The `cmb` directory was redundant after the migration to the `engram` package. Having two parallel package hierarchies with the same functionality made it harder to maintain and improve the codebase.

Benefits of this change:
- Simplified codebase
- Single source of truth for each feature
- Clear import path for users
- Reduced maintenance overhead
- Better optimization of the code

## FAISS Migration

In addition to the package reorganization, we've also migrated from ChromaDB to FAISS for vector storage, which provides better compatibility with NumPy 2.x.

For details on the FAISS migration, see [FAISS_MIGRATION_COMPLETE.md](FAISS_MIGRATION_COMPLETE.md).