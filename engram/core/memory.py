#!/usr/bin/env python3
"""
Memory Service - Core memory functionality for Engram

This module has been refactored into a more modular structure.
It now serves as a compatibility layer that imports from the new structure.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.memory")

# Re-export from new structure
from engram.core.memory import (
    MemoryService, 
    STANDARD_NAMESPACES,
    create_compartment,
    activate_compartment,
    deactivate_compartment,
    set_compartment_expiration,
    list_compartments,
    search_memory,
    get_relevant_context
)

# Vector database configuration for backward compatibility
from engram.core.memory.config import (
    HAS_VECTOR_DB,
    VECTOR_DB_NAME,
    VECTOR_DB_VERSION,
    USE_FALLBACK
)

# Legacy variable compatibility
HAS_MEM0 = False  # Legacy compatibility

# Export public symbols
__all__ = [
    "MemoryService",
    "HAS_VECTOR_DB",
    "VECTOR_DB_NAME",
    "VECTOR_DB_VERSION",
    "HAS_MEM0",
    "USE_FALLBACK"
]