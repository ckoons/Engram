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

## Features

- **Multiple Memory Namespaces**:
  - `conversations`: Store and recall dialog history
  - `thinking`: Preserve Claude's reasoning processes
  - `longterm`: Maintain high-priority facts and insights
  - `projects`: Connect context across different workspaces
  - `compartments`: Organize memories by topic or project
  - `session`: Persist memories between conversations
  - `private`: Encrypted memories only Claude can access

- **Advanced Memory Management**:
  - Memory compartmentalization for organization
  - Session persistence for cross-conversation memory
  - Time-based memory expiration control
  - Hierarchical memory organization
  - Memory correction for handling misinformation
  - Private encrypted memories with key management
  - Web-based visualization and management UI

- **Simple Interface**:
  - Ultra-short commands with QuickMem (m, t, r, w, c, k, s, a, p, v)
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

```bash
# Start both the memory bridge and HTTP services
./cmb_start_all

# OR use the cmb_check script to check status and start services
./cmb_check.py --start

# In your Claude session, access memories with QuickMem:
from cmb.cli.quickmem import m, t, r, w, c, k, x, s, a, p, v

# Check memory service status (and start if needed with s(True))
s()

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
```

## Documentation

- [Usage Guide](docs/usage.md): Basic usage instructions and examples
- [QuickMem Commands](docs/quickmem.md): Ultra-short memory command reference
- [HTTP Wrapper](docs/http_wrapper.md): HTTP service details
- [Memory Management](docs/memory_management.md): Compartments, session persistence, and expiration
- [Memory Visualization](docs/memory_visualization.md): Web-based UI for browsing and managing memories
- [Simplified Web UI](docs/simplified_web_ui.md): Lightweight alternative for environments with dependency issues
- [Claude Integration](docs/claude_integration.md): Automatic startup and memory status checking for Claude sessions
- [Future Enhancements](docs/future_enhancements.md): Planned features and improvements

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](LICENSE) for details.