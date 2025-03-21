#!/usr/bin/env python3
"""
CMB Compatibility Layer

This module provides import compatibility for code that still imports from the 'cmb' package,
which has been deprecated in favor of the 'engram' package.

Usage:
    import cmb_compat
    
    # Then continue to use cmb imports, which will be redirected to engram
    from cmb.core.memory import MemoryService
    from cmb.core.structured_memory import StructuredMemory
"""

import sys
import warnings
import importlib.util
from types import ModuleType

# Display warning
warnings.warn(
    "The 'cmb' package is deprecated and has been removed. "
    "Please update your imports to use the 'engram' package instead.\n"
    "Example: from cmb.core.memory import MemoryService → from engram.core.memory_faiss import MemoryService",
    DeprecationWarning,
    stacklevel=2
)

# Import mapping
IMPORT_MAPPING = {
    "cmb.core.memory": "engram.core.memory_faiss",
    "cmb.core.structured_memory": "engram.core.structured_memory",
    "cmb.core.nexus": "engram.core.nexus",
    "cmb.api.consolidated_server": "engram.api.consolidated_server",
    "cmb.api.http_wrapper": "engram.api.http_wrapper",
    "cmb.api.server": "engram.api.server",
    "cmb.cli.quickmem": "engram.cli.quickmem",
    "cmb.cli.claude_helper": "engram.cli.claude_helper",
    "cmb.cli.claude_launcher": "engram.cli.claude_launcher",
    "cmb.cli.comm_quickmem": "engram.cli.comm_quickmem",
    "cmb.cli.http_helper": "engram.cli.http_helper",
    "cmb.web.app": "engram.web.app",
}


class CMBFinder:
    """Import finder that redirects 'cmb' imports to 'engram'."""
    
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("cmb."):
            # Find the engram equivalent
            engram_name = IMPORT_MAPPING.get(fullname)
            if engram_name:
                # Try to import the engram module
                try:
                    engram_spec = importlib.util.find_spec(engram_name)
                    if engram_spec:
                        return engram_spec
                except ImportError:
                    pass
        return None


class CMBModule(ModuleType):
    """Proxy module that redirects attributes to the engram module."""
    
    def __init__(self, name, engram_module):
        super().__init__(name)
        self._engram_module = engram_module
    
    def __getattr__(self, name):
        return getattr(self._engram_module, name)


# Register the import finder
sys.meta_path.append(CMBFinder())

# Install a module redirector for top level 'cmb'
cmb_module = CMBModule("cmb", importlib.import_module("engram"))
sys.modules["cmb"] = cmb_module

print("CMB compatibility layer installed. Legacy imports will be redirected to 'engram'.")