"""
Engram Core Module

This package contains the core functionality of the Engram memory system, including:
- Memory service for persistent storage
- Structured memory with organization and importance ranking
- Nexus interface for AI assistants
- FAISS-based vector storage for efficient semantic search
"""

__version__ = "0.3.0"

# Import the FAISS-based memory implementation
from engram.core.memory_faiss import MemoryService