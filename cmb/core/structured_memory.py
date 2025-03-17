#!/usr/bin/env python3
"""
Legacy Structured Memory Module (Compatibility Wrapper)

This module is maintained for backward compatibility only.
All functionality is now provided by engram.core.structured_memory.
"""

import warnings
from engram.core.structured_memory import *

warnings.warn(
    "The 'cmb.core.structured_memory' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.core.structured_memory' module instead.",
    DeprecationWarning,
    stacklevel=2
)