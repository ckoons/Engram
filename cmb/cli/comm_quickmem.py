#!/usr/bin/env python3
"""
Legacy Communication QuickMem Module (Compatibility Wrapper)

This module is maintained for backward compatibility only.
All functionality is now provided by engram.cli.comm_quickmem.
"""

import warnings
from engram.cli.comm_quickmem import *

warnings.warn(
    "The 'cmb.cli.comm_quickmem' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.cli.comm_quickmem' module instead.",
    DeprecationWarning,
    stacklevel=2
)