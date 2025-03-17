"""
Legacy Claude Memory Bridge API Module

This module is maintained for backward compatibility only.
Imports are forwarded from the new 'engram.api' package.
"""

import warnings
from engram.api import *

warnings.warn(
    "The 'cmb.api' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.api' module instead.",
    DeprecationWarning,
    stacklevel=2
)