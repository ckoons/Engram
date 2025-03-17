#!/usr/bin/env python3
"""
Legacy QuickMem Module (Compatibility Wrapper)

This module is maintained for backward compatibility only.
All functionality is now provided by engram.cli.quickmem.
"""

import warnings
from engram.cli.quickmem import *

warnings.warn(
    "The 'cmb.cli.quickmem' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.cli.quickmem' module instead.",
    DeprecationWarning,
    stacklevel=2
)