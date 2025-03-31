# Memory FAISS Module Refactored Structure

This directory contains the refactored Memory FAISS components for Engram. The original monolithic `memory_faiss.py` has been split into multiple modules for better maintainability and readability.

## Directory Structure

- `base/`: Core memory service functionality
  - `service.py`: Main MemoryService class with initialization and common operations
  - `configuration.py`: Configuration and initialization utilities

- `storage/`: Storage mechanisms 
  - `vector.py`: FAISS-based vector storage integration
  - `file.py`: Fallback file-based storage

- `compartments/`: Memory compartments management
  - `manager.py`: Managing compartments (creating, activating, deactivating)
  - `expiration.py`: Compartment expiration functionality

- `search/`: Search functionality
  - `keyword.py`: Keyword-based search
  - `vector.py`: Vector-based semantic search

- `utils/`: Utility functions and helpers
  - `logging.py`: Logging configuration
  - `helpers.py`: Common helper functions

- `fallback/`: Fallback mechanisms when vector search is unavailable
  - `file_storage.py`: File-based storage implementation

## Usage

The original `memory_faiss.py` file is maintained as a compatibility layer that imports from this refactored structure, ensuring backwards compatibility while providing a more modular codebase.