"""
Legacy Claude Memory Bridge Core Module

This module is maintained for backward compatibility only.
Imports are forwarded from the new 'engram.core' package.
"""

import warnings
from engram.core import *

warnings.warn(
    "The 'cmb.core' module is deprecated and will be removed in a future release. "
    "Please use the 'engram.core' module instead.",
    DeprecationWarning,
    stacklevel=2
)