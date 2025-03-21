# CMB Removal Plan

This document outlines the strategy for removing the redundant `cmb` (Claude Memory Bridge) package and fully migrating to the `engram` package structure.

## Phase 1: Compatibility Layer (COMPLETED)

- ✅ Create `cmb_compat.py` module for import compatibility
- ✅ Update engram package to provide all functionality from cmb
- ✅ Map all cmb imports to their engram counterparts

## Phase 2: Update References (CURRENT PHASE)

1. Update all Python script imports:
   - Remove direct imports from `cmb.*` modules
   - Replace with equivalent `engram.*` imports
   - Apply to all application code, tests, and examples

2. Update shell scripts:
   - Replace any references to `cmb` in shell scripts
   - Update environment variable references (CMB_* to ENGRAM_*)
   - Ensure all launcher scripts reference engram modules

3. Update documentation:
   - Replace cmb references in all markdown files
   - Update code examples to use engram imports
   - Create migration guide for users

## Phase 3: Remove CMB Package

1. Verify all functionality:
   - Run all tests with engram-only imports
   - Manually test all scripts and tools
   - Ensure no functional regressions

2. Remove cmb package:
   - Delete cmb directory entirely
   - Keep cmb_compat.py for transitional support

3. Finalize documentation:
   - Remove any lingering cmb references
   - Update README with current status
   - Close any migration-related issues

## Phase 4: Clean-up (FUTURE)

1. Release new version:
   - Create a new release with cmb removal
   - Update version numbers

2. Deprecate compatibility layer:
   - Add future deprecation notice to cmb_compat.py
   - Plan for eventual removal in future release (6+ months)

## File Update Checklist

### Python Scripts
- [ ] `/Users/cskoons/projects/github/Engram/tests/test_http_wrapper.py`
- [ ] `/Users/cskoons/projects/github/Engram/tests/test_structured_memory.py`
- [ ] `/Users/cskoons/projects/github/Engram/tests/test_quickmem.py`
- [ ] `/Users/cskoons/projects/github/Engram/tests/test_memory.py`
- [ ] `/Users/cskoons/projects/github/Engram/simple_web_ui.py`
- [ ] `/Users/cskoons/projects/github/Engram/examples/consolidated_example.py`

### Shell Scripts
- [ ] `/Users/cskoons/projects/github/Engram/claude_comm_test.sh`
- [ ] `/Users/cskoons/projects/github/Engram/launch_claude.sh`
- [ ] `/Users/cskoons/projects/github/Engram/install.sh`

### Environment Variables
Update the following:
- CMB_CLIENT_ID → ENGRAM_CLIENT_ID
- CMB_DATA_DIR → ENGRAM_DATA_DIR
- CMB_BASE_URL → ENGRAM_BASE_URL
- CMB_HTTP_URL → ENGRAM_HTTP_URL
- CMB_WEB_HOST → ENGRAM_WEB_HOST
- CMB_WEB_PORT → ENGRAM_WEB_PORT
- CMB_WEB_DEBUG → ENGRAM_WEB_DEBUG