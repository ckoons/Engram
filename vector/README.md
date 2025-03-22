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
- Used in both direct and virtual environment approaches
- Excellent for semantic search capabilities

## Usage

To use vector functionality, see:

- `/docs/vector/FAISS_DIRECT.md` - Recommended runtime patching approach
- `/docs/vector/FAISS_VECTOR_DATABASE.md` - Virtual environment approach
- `/utils/vector_db_setup.py` - Setup and configuration utility

## Test Environments

- `test/` directory contains test scripts and data 
- `test_venv/` contains a test virtual environment