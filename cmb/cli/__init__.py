"""
Legacy Claude Memory Bridge CLI Module

This module is maintained for backward compatibility only.
Imports are forwarded from the new 'engram.cli' package.
"""

import warnings
from engram.cli import *

warnings.warn(
    "The 'cmb.cli' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.cli' module instead.",
    DeprecationWarning,
    stacklevel=2
)