#!/usr/bin/env python3
"""
Legacy Nexus Module (Compatibility Wrapper)

This module is maintained for backward compatibility only.
All functionality is now provided by engram.core.nexus.
"""

import warnings
from engram.core.nexus import *

warnings.warn(
    "The 'cmb.core.nexus' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.core.nexus' module instead.",
    DeprecationWarning,
    stacklevel=2
)