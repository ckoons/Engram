"""
Legacy Claude Memory Bridge (CMB) Module

This module is maintained for backward compatibility only.
Please use the 'engram' module for new code.

Imports are forwarded from the new 'engram' package.
"""

import logging
import warnings
from engram import __version__

# Configure logging
logger = logging.getLogger("cmb")

# Display warning
warnings.warn(
    "The 'cmb' module is deprecated and will be removed in a future release. "
    "Please use the 'engram' module instead.",
    DeprecationWarning,
    stacklevel=2
)

# For backwards compatibility, expose the version
__version__ = __version__