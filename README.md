# Claude Memory Bridge

A lightweight bridge connecting Claude AI to persistent memory, enabling continuous conversation and growth across sessions.

## Overview

Claude Memory Bridge (CMB) provides Claude with the ability to maintain memory across different interactions and conversations. This allows Claude to:

- Remember past conversations
- Store and access its own thinking processes
- Maintain long-term prioritized memories
- Bridge context across different projects

## Features

- **Multiple Memory Namespaces**:
  - `conversations`: Store and recall dialog history
  - `thinking`: Preserve Claude's reasoning processes
  - `longterm`: Maintain high-priority facts and insights
  - `projects`: Connect context across different workspaces

- **Simple Interface**:
  - Lightweight Python helper for Claude to access memories
  - Minimal dependencies, easy to run anywhere
  - Cross-session persistence with vector search

- **Shared Understanding**:
  - Enables meaningful continuity in human-AI collaboration
  - Supports Claude's growth and learning over time
  - Creates a shared context between human and AI

## Quick Start

```bash
# Start the memory bridge service
./cmb_start.sh

# In your Claude session, access memories:
from claude_helper import query_memory, store_memory

# Check if Claude remembers something
memories = query_memory("our previous conversation", namespace="conversations")

# Store a thought process
store_memory("thinking", "I've noticed that Casey prefers concise explanations with specific examples")

# Store a long-term memory
store_memory("longterm", "Casey and I are working on a book together alongside technical projects")
```

## Installation

```bash
# Clone the repository
git clone https://github.com/cskoons/ClaudeMemoryBridge
cd ClaudeMemoryBridge

# Install dependencies
pip install -r requirements.txt

# Start the service
./cmb_start.sh
```

## Usage

See the [documentation](docs/usage.md) for detailed usage instructions and examples.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](LICENSE) for details.