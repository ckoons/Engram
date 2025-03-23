# Engram Memory System Development Notes

## Project Overview

Engram (formerly Claude Memory Bridge) is a project to give Claude persistent memory across different sessions. The project aims to:

1. Allow Claude to remember past conversations
2. Enable Claude to store and retrieve its own thoughts
3. Maintain longterm, high-priority memories
4. Share context across different projects
5. Automatically categorize and prioritize information by importance
6. Provide context-aware memory retrieval for conversations

## Key Features

- **Balanced Memory System**:
  - Structured Memory: File-based storage with categorized organization
  - Memory Importance Ranking: 1-5 scale with prioritized retrieval
  - Enhanced Retrieval: Context-aware memory loading
  - Nexus Interface: Standardized API for memory-enabled AI assistants
- Multiple memory categories (personal, projects, facts, preferences, session, private)
- Both vector-based (using ChromaDB and sentence-transformers) and fallback memory implementations
- Auto-categorization based on content analysis
- Memory digests for session start context
- Simple Claude helper interface for store/retrieve operations
- Easy-to-use CLI for starting the memory service

## Code Style and Conventions

### Python

- Use f-strings for string formatting
- Add type hints to function signatures
- Follow PEP 8 guidelines
- 4 spaces for indentation
- Use docstrings for all functions and classes

### Comments

- Include brief comments for complex sections
- Add TODOs for future improvements
- Document any workarounds or tricky implementations

### Error Handling

- Use try/except blocks for operations that could fail
- Log errors with appropriate level (info, warning, error)
- Return meaningful error messages

### Commit Messages

```
feat: Descriptive title for the changes

- Bullet point describing key implementation details
- Another bullet point with important design decisions
- Additional context about the implementation

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Casey Koons <cskoons@gmail.com> & Claude <noreply@anthropic.com>
```

IMPORTANT: Always include co-authorship credit in the commit message. This properly attributes contributions to both Casey and Claude.

## Common Commands

### Service Management

```bash
# Start memory bridge
cd ~/projects/github/Engram
./engram_consolidated

# With custom client ID
./engram_consolidated --client-id project-x

# Start in fallback mode (no vector database)
./engram_consolidated --fallback

# Check service status and start if needed
./engram_check.py --start

# Test vector database integration
./utils/vector_db_setup.py --test

# Fix NumPy compatibility issues with vector database
./utils/vector_db_setup.py --fix-numpy

# Install vector database dependencies
./utils/vector_db_setup.py --install

# Run tests
cd ~/projects/github/Engram
python -m pytest tests

# Install development version
cd ~/projects/github/Engram
pip install -e .
```

### Structured Memory & Nexus

```python
# Import Structured Memory core components
from engram.core.structured_memory import StructuredMemory
from engram.core.nexus import NexusInterface
from engram.core.memory import MemoryService

# Initialize components
memory_service = MemoryService(client_id="claude")
structured_memory = StructuredMemory(client_id="claude")
nexus = NexusInterface(memory_service=memory_service, structured_memory=structured_memory)

# Start a Nexus session
await nexus.start_session("Project Discussion")

# Process a user message with memory enrichment
enriched_message = await nexus.process_message("Let's discuss structured memory", is_user=True)

# Store a memory with auto-categorization
await structured_memory.add_auto_categorized_memory(
    content="The structured memory system has importance levels from 1-5"
)

# Get a memory digest
digest = await structured_memory.get_memory_digest(max_memories=10, include_private=False)
```

### QuickMem Shortcuts

```python
# Import QuickMem for structured memory and Nexus
from engram.cli.quickmem import memory_digest, start_nexus, process_message, auto_remember, end_nexus
from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z

# Get memory digest (ultra-short version: d)
await memory_digest(max_memories=10)

# Start a Nexus session (ultra-short version: n)
await start_nexus("Project Discussion")

# Process a message (ultra-short version: q)
await process_message("Let's discuss the structured memory implementation", is_user=True)

# Auto-remember something (ultra-short version: z)
await auto_remember("The structured memory system uses importance levels from 1 to 5")
```

## Latest Updates (March 23, 2025 - v0.8.2)

### Vector Database Improvements

1. **FAISS Vector Database Integration**:
   - Successfully integrated FAISS 1.10.0 with NumPy 2.x compatibility
   - Created comprehensive test suite for FAISS verification
   - Implemented GPU detection and support via `install_faiss_gpu.py`
   - Improved error handling with graceful fallback to file-based storage
   - Resolved path resolution issues in launcher scripts
   - Added detailed documentation and troubleshooting guide in `vector/README.md`

2. **LanceDB Integration (Completed)**:
   - Implemented full LanceDB adapter in `vector/lancedb/adapter.py`
   - Created vector store implementation in `vector/lancedb/vector_store.py`
   - Added installation system with platform detection in `install.py`
   - Included hardware optimization for Apple Silicon (Metal) and CUDA
   - Created launcher scripts: `engram_with_lancedb` and `engram_with_ollama_lancedb`
   - Implemented same API as FAISS adapter for interchangeability
   - Added comprehensive test script in `test_lancedb.py`
   - Updated documentation with usage examples and comparison

3. **Ollama Integration Enhancements**:
   - Fixed input handling in Ollama-FAISS integration
   - Added improved logging for memory operations
   - Enhanced error recovery during chat sessions
   - Fixed path resolution for cross-directory script execution
   - Added memory tagging with source model information
   - Improved session management for vector search results

### Implementation Status

As of March 23, 2025, Engram has fully operational FAISS vector database integration with several key improvements:

- **Cross-Platform Support**: 
  - CPU version working on all platforms
  - GPU detection for appropriate CUDA version when available
  - Testing on MacOS with Apple Silicon

- **Core Functionality**:
  - Vector-based semantic search with proper relevance scoring
  - Simple deterministic embedding that works without external models
  - Automatic fallback to file-based storage when needed
  - Complete adapter layer for Engram memory system

- **Performance**:
  - FAISS provides efficient similarity search capabilities
  - Lightweight embedding generation for resource-constrained environments
  - Fast startup and initialization times

- **Stability**:
  - Comprehensive error handling and recovery
  - Graceful degradation when vector features unavailable
  - Full test suite for verification of functionality

Engram now offers both FAISS and LanceDB as vector database options:

- **FAISS**: Mature vector database with excellent CUDA performance
- **LanceDB**: Modern Arrow-based vector database with native Apple Silicon support

Users can choose the appropriate backend based on their hardware platform:

```bash
# Smart launcher - automatically selects the best database
./engram_smart_launch

# Smart launcher with Ollama - automatically selects the best database
./engram_smart_launch_ollama

# Manually select a specific backend:
./engram_with_ollama_faiss     # FAISS with Ollama (good for CUDA systems)
./engram_with_lancedb          # LanceDB with Claude (good for Apple Silicon)
./engram_with_ollama_lancedb   # LanceDB with Ollama (cross-platform)
```

The smart launcher automatically detects your hardware capabilities and installed libraries to select the optimal vector database backend:

- On Apple Silicon with Metal → LanceDB
- On NVIDIA GPU systems with CUDA → FAISS
- Optimizes for available hardware acceleration

Both implementations provide the same API and functionality, allowing seamless switching between backends.

## Future Enhancements

1. Advanced NLP for memory auto-categorization (beyond pattern matching)
2. Memory embeddings for more accurate context retrieval
3. Memory pruning and consolidation for older content
4. Multi-user support with shared memory spaces
5. Integration with other AI systems beyond Claude
6. Enhanced web UI for structured memory browsing and visualization
7. Hierarchical memory organization within categories
8. Memory federation for sharing across instances 
9. Conversation topic detection and auto-compartmentalization

## Deployment Notes

The memory bridge should be run as a separate service, ideally started when the system boots. It can be run:

1. Directly: `./cmb_start.sh`
2. Via system service: Create a systemd or launchd service
3. As a background process: `nohup ./cmb_start.sh &`

For production use, consider running behind a proper web server like nginx with authentication.