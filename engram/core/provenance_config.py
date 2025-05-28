#!/usr/bin/env python3
"""
Configuration for provenance tracking.

Configurable settings for different use cases.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ProvenanceConfig:
    """Configuration for provenance tracking behavior."""
    
    # Performance settings
    batch_interval: float = 1.0  # Seconds between batch flushes
    batch_size: int = 10  # Max operations per batch
    cache_ttl: int = 300  # Cache time-to-live in seconds
    max_cache_size: int = 1000  # Maximum cached entries
    
    # Tracking settings
    track_by_default: bool = False  # Global default
    tracked_namespaces: set = field(default_factory=lambda: {"shared", "longterm", "projects"})
    importance_threshold: int = 3  # Minimum importance to track
    
    # Chain management
    max_chain_length: int = 100  # Squash after this many entries
    squash_keep_milestones: bool = True  # Keep important entries when squashing
    auto_squash: bool = True  # Automatically squash long chains
    
    # Conflict resolution
    auto_conflict_branch: bool = True  # Create conflict branches on merge failure
    conflict_branch_pattern: str = "{base}.conflict-{timestamp}"
    include_conflict_markers: bool = True  # Add <<<< ==== >>>> markers
    
    # Storage settings
    provenance_namespace: str = "_provenance"
    branch_namespace: str = "_branches"
    
    @classmethod
    def interactive(cls) -> "ProvenanceConfig":
        """Config optimized for interactive sessions."""
        return cls(
            batch_interval=0.1,  # 100ms for responsive feel
            batch_size=5,  # Smaller batches, faster feedback
            cache_ttl=600,  # Longer cache for session
            track_by_default=True  # Track everything in interactive mode
        )
    
    @classmethod
    def background(cls) -> "ProvenanceConfig":
        """Config optimized for background processing."""
        return cls(
            batch_interval=5.0,  # 5s for efficiency
            batch_size=50,  # Larger batches
            cache_ttl=60,  # Shorter cache, less memory
            track_by_default=False  # Only track important
        )
    
    @classmethod
    def minimal(cls) -> "ProvenanceConfig":
        """Minimal tracking for performance-critical apps."""
        return cls(
            batch_interval=10.0,  # Very lazy
            track_by_default=False,
            tracked_namespaces={"longterm"},  # Only most important
            importance_threshold=5,  # Only critical memories
            auto_squash=True,
            max_chain_length=50  # Aggressive squashing
        )