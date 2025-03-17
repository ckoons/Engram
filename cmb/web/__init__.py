"""
Legacy Claude Memory Bridge Web Module

This module is maintained for backward compatibility only.
Imports are forwarded from the new 'engram.web' package.
"""

import warnings
from engram.web import *

warnings.warn(
    "The 'cmb.web' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.web' module instead.",
    DeprecationWarning,
    stacklevel=2
)