# Claude Memory Bridge

A lightweight bridge connecting Claude AI to persistent memory, enabling continuous conversation and growth across sessions.

## Overview

Claude Memory Bridge (CMB) provides Claude with the ability to maintain memory across different interactions and conversations. This allows Claude to:

- Remember past conversations
- Store and access its own thinking processes
- Maintain long-term prioritized memories
- Bridge context across different projects
- Organize memories in compartments
- Control memory expiration
- Automatically categorize and rank memory importance

## Features

- **Balanced Memory System**:
  - **Structured Memory**: File-based storage with categorized organization
  - **Memory Importance Ranking**: 1-5 scale with prioritized retrieval
  - **Enhanced Retrieval**: Context-aware memory loading
  - **Nexus Interface**: Standardized API for memory-enabled AI assistants

- **Multiple Memory Categories**:
  - `personal`: Store user personal information (highest importance)
  - `projects`: Connect context across different workspaces
  - `facts`: Maintain general factual information
  - `preferences`: Remember user preferences and settings
  - `session`: Persist memories between conversations
  - `private`: Encrypted memories only Claude can access

- **Advanced Memory Management**:
  - Auto-categorization of memories based on content analysis
  - Memory digests with formatted summaries of important information
  - Context enrichment for conversations with relevant memories
  - Unified search across memory systems
  - Memory compartmentalization for organization
  - Session persistence for cross-conversation memory
  - Time-based memory expiration control
  - Hierarchical memory organization
  - Memory correction for handling misinformation
  - Private encrypted memories with key management
  - Web-based visualization and management UI

- **Simple Interface**:
  - Ultra-short commands with QuickMem (m, t, r, w, c, k, s, a, p, v, d, n, q, y, z)
  - Agency and privacy respecting design
  - Automatic service health checking and startup
  - Lightweight Python helper for Claude to access memories
  - Minimal dependencies, easy to run anywhere
  - Cross-session persistence with vector search

- **Shared Understanding**:
  - Enables meaningful continuity in human-AI collaboration
  - Supports Claude's growth and learning over time
  - Creates a shared context between human and AI

## Quick Start

### Option 1: Automatic Memory Loading (Recommended)

```bash
# Launch Claude with all memory services pre-configured
./claude_with_memory

# OR use the simplified starter in Claude Code session
from claude_memory_start import start_memory
start_memory("Project Work Session")  # Loads memories and starts session
```

### Option 2: Manual Memory Loading

```bash
# Start both the memory bridge and HTTP services
./cmb_start_all

# OR use the cmb_check script to check status and start services
./cmb_check.py --start

# In your Claude session, access memories with QuickMem:
from cmb.cli.quickmem import m, t, r, w, l, c, k, f, i, x, s, a, p, v, b, e, o

# Auto-load previous memories and start session in one command
o()

# Or step by step:
# Check memory service status (and start if needed with s(True))
s()

# Load previous session memories
l()

# Start a new session
b("Project Work Session")
```

### Memory Commands

#### Basic Memory Operations

```bash
# Check memories about a topic
m("project")

# Store a thought
t("Casey seems to prefer structured memory organization")

# Remember important information
r("Casey's current project is about memory management")

# Create a compartment for project memories
c("ProjectX: This is a memory about the ProjectX initiative")

# Write session memory for persistence
w("Today we worked on implementing compartmentalized memory")

# Set memory expiration (30 days)
k("memory_id_123")

# Correct misinformation
x("Casey lives in San Francisco", "Casey lives in Seattle")

# Use Claude's agency for memory decisions
a("Should I categorize this project information?")

# Store private encrypted memory
p("My private analysis of the current project direction")

# View private memories
v()

# End session with summary
e("Completed memory integration with auto-loading")
```

#### Structured Memory & Nexus Commands

```bash
# Get a formatted digest of important memories
await d(max_memories=10, include_private=False)

# Start a Nexus session with memory enrichment
await n("Project Discussion Session")

# Process a message with memory context
await q("Let's discuss the structured memory implementation", is_user=True)

# Store memory with auto-categorization
await z("The structured memory system uses importance levels from 1 to 5")

# End a Nexus session with summary
await y("Completed work on structured memory implementation")
```

## Installation

```bash
# Clone the repository
git clone https://github.com/cskoons/ClaudeMemoryBridge
cd ClaudeMemoryBridge

# Install dependencies
pip install -r requirements.txt

# Or install the package
pip install -e .

# Start everything (interactive mode)
./cmb_start_web

# Start everything in background
./cmb_start_web_bg
./cmb_stop_web  # Stop background services when done

# Or start services separately
./cmb_start_all  # Memory services only
./cmb_web        # Web UI only (requires memory services)

# Launch Claude with memory services and full tool access
./claude_with_memory  # All-in-one script for Claude Code with memory
```

## Documentation

- [Usage Guide](docs/usage.md): Basic usage instructions and examples
- [QuickMem Commands](docs/quickmem.md): Ultra-short memory command reference
- [Structured Memory](docs/structured_memory.md): Balanced memory system with importance ranking
- [HTTP Wrapper](docs/http_wrapper.md): HTTP service details
- [Memory Management](docs/memory_management.md): Compartments, session persistence, and expiration
- [Privacy Guide](docs/privacy.md): Private encrypted memories and security features
- [Memory Visualization](docs/memory_visualization.md): Web-based UI for browsing and managing memories
- [Simplified Web UI](docs/simplified_web_ui.md): Lightweight alternative for environments with dependency issues
- [Claude Integration](docs/claude_integration.md): Automatic startup and memory status checking for Claude sessions
- [Future Enhancements](docs/future_enhancements.md): Planned features and improvements

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](LICENSE) for details.