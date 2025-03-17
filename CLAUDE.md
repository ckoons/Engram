# Claude Memory Bridge Development Notes

## Project Overview

Claude Memory Bridge (CMB) is a project to give Claude persistent memory across different sessions. The project aims to:

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
- Both vector-based (using mem0ai) and fallback memory implementations
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
cd ~/projects/github/ClaudeMemoryBridge
./cmb_start.sh

# With custom client ID
./cmb_start.sh --client-id project-x

# Check service status and start if needed
./cmb_check.py --start

# Run tests
cd ~/projects/github/ClaudeMemoryBridge
python -m pytest tests

# Install development version
cd ~/projects/github/ClaudeMemoryBridge
pip install -e .
```

### Structured Memory & Nexus

```python
# Import Structured Memory core components
from cmb.core.structured_memory import StructuredMemory
from cmb.core.nexus import NexusInterface
from cmb.core.memory import MemoryService

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
from cmb.cli.quickmem import memory_digest, start_nexus, process_message, auto_remember, end_nexus
from cmb.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z

# Get memory digest (ultra-short version: d)
await memory_digest(max_memories=10)

# Start a Nexus session (ultra-short version: n)
await start_nexus("Project Discussion")

# Process a message (ultra-short version: q)
await process_message("Let's discuss the structured memory implementation", is_user=True)

# Auto-remember something (ultra-short version: z)
await auto_remember("The structured memory system uses importance levels from 1 to 5")
```

## Latest Updates (March 17, 2025)

### Memory System Improvements

1. **Vector Storage Compatibility**:
   - Updated to support mem0ai library (replacing mem0)
   - Improved error handling and graceful fallback to file-based storage
   - Enhanced health check endpoint with detailed implementation status
   - Better diagnostic information during startup

2. **Service Reliability**:
   - Fixed port conflict detection and handling
   - Improved service startup and status checking
   - Added comprehensive error reporting during service initialization
   - Enhanced health endpoint with implementation details

3. **Engram Script Enhancements**:
   - Fixed issue with engram_with_claude script detection of running services
   - Added port availability checking before starting services
   - Improved error logging for better troubleshooting
   - Enhanced process management with proper PID tracking

### Implementation Status

As of March 17, 2025, Engram has been successfully migrated to work with both mem0ai (for vector search) and a fallback file-based implementation. The system is designed to work correctly without mem0ai while maintaining its core functionalities:

- Storage and retrieval of memories works in all implementations
- Context-aware memory loading functions correctly
- Structured memory and Nexus interfaces operate as expected
- Memory compartmentalization and expiration controls work in all modes

When mem0ai is available, the system will automatically use vector search for enhanced retrieval. When mem0ai is unavailable, the system automatically falls back to file-based storage, with clear logging of the fallback status.

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