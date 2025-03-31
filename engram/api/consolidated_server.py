"""
Engram Consolidated API Server

This module has been refactored into a more modular structure.
It now serves as a compatibility layer that imports from the new structure.
"""

# Re-export from server.py
from engram.api.server import (
    app, 
    main, 
    parse_arguments,
    lifespan
)

# This module is kept for backward compatibility
if __name__ == "__main__":
    main()