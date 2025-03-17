#!/usr/bin/env python3
"""
Legacy Memory Module (Compatibility Wrapper)

This module is maintained for backward compatibility only.
All functionality is now provided by engram.core.memory.
"""

import warnings
from engram.core.memory import *

warnings.warn(
    "The 'cmb.core.memory' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.core.memory' module instead.",
    DeprecationWarning,
    stacklevel=2
)