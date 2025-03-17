# Engram-Agenteer Migration Patches

This directory contains patches to update Agenteer from using the Claude Memory Bridge (CMB) to the new Engram package while maintaining backward compatibility.

## Patch Files

1. **agenteer_cmb_adapter.patch**:
   - Updates imports to try `engram` package first, then fall back to `cmb`
   - Sets both `ENGRAM_CLIENT_ID` and `CMB_CLIENT_ID` environment variables
   - Improves process detection to find both Engram and CMB services
   - Updates HTTP API URLs to include the `/http` prefix
   - Updates default HTTP URL to use port 8000

2. **agenteer_nexus_generator.patch**:
   - Updates imports in the Nexus agent generator to try `engram` first
   - Adds appropriate logging to indicate which package is being used

3. **structured_memory_compatibility.patch**:
   - Adds a compatibility method `get_memories_by_category` to Engram's `StructuredMemory` class
   - This ensures that Agenteer can work with Engram even though the API has changed slightly

## How to Apply

1. First, apply the structured_memory_compatibility patch to Engram:

```bash
cd /Users/cskoons/projects/github/Engram
patch -p0 < patches/structured_memory_compatibility.patch
```

2. Then, apply the Agenteer patches:

```bash
cd /Users/cskoons/projects/github/Agenteer
patch -p0 < /Users/cskoons/projects/github/Engram/patches/agenteer_cmb_adapter.patch
patch -p0 < /Users/cskoons/projects/github/Engram/patches/agenteer_nexus_generator.patch
```

## Testing After Patching

After applying the patches, you should test Agenteer with both Engram and CMB to ensure it works correctly:

1. Test with only Engram installed
2. Test with both Engram and CMB installed
3. Test with only CMB installed (if possible)
4. Test with neither installed (fallback mode)

Make sure to verify that memory storage, retrieval, and Nexus agent operations work as expected in all scenarios.

## Future Work

Once these patches are verified to be working correctly, we can proceed with:

1. Making Engram the primary dependency in Agenteer
2. Removing CMB-specific code paths
3. Renaming `cmb_adapter.py` to `engram_adapter.py`
4. Updating documentation to reference Engram instead of CMB