# Claude Integration

Claude Memory Bridge provides seamless integration with Claude Code sessions, enabling automatic memory service checking and simple memory management commands.

## Quick Start for Claude Sessions

At the beginning of your Claude Code session:

```python
# Method 1: Run the startup script
%run /path/to/ClaudeMemoryBridge/claude_startup.py

# Method 2: Import memory functions directly
from cmb.cli.quickmem import m, t, r, f, i, w, l, c, k, cx, s

# Check memory service status (and start if needed)
s()  # or s(True) to auto-start if not running
```

## Status Checking

The `status()` function (or its shorthand `s()`) allows Claude to check the memory service:

```python
# Basic status check
s()

# Status check with auto-start option
s(True)  # Will start services if they're not running
```

The status check will provide information about:
- Whether memory services are running
- The client ID being used
- Whether mem0 vector integration is available
- Memory statistics (number of items per namespace)
- Active compartments

## Startup Script

The `claude_startup.py` script automates memory integration at the beginning of your Claude Code sessions:

```python
# At the start of your Claude session
%run /path/to/ClaudeMemoryBridge/claude_startup.py
```

This script:
1. Locates the CMB module in the current environment
2. Checks if memory services are running
3. Offers to start services if they're not running
4. Imports all memory functions into the global namespace
5. Provides a status report on memory availability

## Service Management Tools

### 1. `cmb_check.py`

A comprehensive tool for checking CMB service status and managing services:

```bash
# Check service status
./cmb_check.py

# Start services if not running
./cmb_check.py --start

# Force restart services
./cmb_check.py --restart

# Stop running services
./cmb_check.py --stop

# Test a memory query
./cmb_check.py --query "test query"

# Check for newer versions
./cmb_check.py --version-check
```

### 2. `status()` Memory Function

The `status()` function in the quickmem module provides a lightweight way for Claude to:
- Check if memory services are running
- Get basic memory statistics
- Optionally start services if they're not running

## Claude Session Flow

Recommended flow at the beginning of each Claude Code session:

1. Start with the startup script: `%run /path/to/ClaudeMemoryBridge/claude_startup.py`
2. The script will check memory services and import functions
3. If memory services aren't running, the script will offer to start them
4. Use memory functions directly: `m()`, `t()`, `r()`, etc.
5. Periodically check status with `s()` to ensure memory services are running

## Troubleshooting

If Claude can't access memories:

1. Check if services are running with `s()`
2. If not running, start with `s(True)` or `./cmb_check.py --start`
3. Verify proper imports with `from cmb.cli.quickmem import *`
4. Check if the ClaudeMemoryBridge package is installed or in the PATH
5. Restart services with `./cmb_check.py --restart` if needed

## Automatic Startup Integration

For fully automated integration:

1. Add the claude_startup.py script to your project
2. Add this code to your .claudeignore or similar initialization:
   ```python
   try:
       exec(open("/path/to/claude_startup.py").read())
       print("Memory services initialized")
   except Exception as e:
       print(f"Error initializing memory services: {e}")
   ```

This allows Claude to automatically check and access memory services at the start of each session, creating a seamless experience.