# Vector Database Integration for Engram

This directory contains components related to vector database integration for Engram. Vector databases enable semantic search functionality, allowing for more natural queries and better retrieval of conceptually similar information.

## Contents

- `faiss_adapter.py` - Adapter for FAISS vector database integration
- `vector_store.py` - Core vector storage interface
- Scripts and utilities for working with vector databases
- Test data and examples

## Vector Database Implementation

Engram uses FAISS (Facebook AI Similarity Search) as its vector database solution:

- High-performance vector similarity search
- Compatible with all NumPy versions including 2.x
- No longer has compatibility issues since ChromaDB was removed
- Excellent for semantic search capabilities

## Usage

To use vector functionality, see:

- `/docs/vector/FAISS_DIRECT.md` - Recommended runtime patching approach
- `/docs/vector/FAISS_VECTOR_DATABASE.md` - Virtual environment approach
- `/utils/vector_db_setup.py` - Setup and configuration utility

## Directory Structure

- `ollama_faiss_venv/` - Virtual environment for FAISS with Ollama integration
  - Used by `engram_with_ollama_faiss` script
  - Contains production-ready dependencies for vector operations

- `test/` - Test scripts and data for vector functionality
  - Example implementations and tests for FAISS
  - Sample vector databases and test memories
  - Test utilities and adapters

- `test_venv/` - Testing virtual environment
  - Isolated environment for testing vector functionality
  - Contains all dependencies needed for comprehensive testing