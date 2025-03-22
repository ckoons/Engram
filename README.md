# Engram

<div align="center">
  <img src="images/icon.jpg" alt="Engram Logo" width="800"/>
  <h3>AI Engrams<br>Persistent Memory Across Sessions</h3>
</div>

A lightweight system providing AI with persistent memory, enabling continuous conversation and growth across sessions.

## Overview

Engram provides AI systems with the ability to maintain memory traces across different interactions and conversations. This allows AI to:

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

- **AI-to-AI Communication**:
  - **Cross-Model Messaging**: Enables different AI models to communicate
  - **Dialog Mode**: Continuous conversation between models
  - **Wildcard Listening**: Monitor and respond to all models automatically
  - **Auto-Reply**: Automatic responses to questions from other models

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
  - Automatic agency activation by default
  - Single port deployment option
  - Automatic service health checking and startup
  - Lightweight Python helper for AI to access memories
  - Minimal dependencies, easy to run anywhere
  - Cross-session persistence with vector search

- **Vector Database Integration**:
  - FAISS for high-performance semantic search (NumPy 2.x compatible)
  - Simple deterministic embeddings without external dependencies
  - Automatic vector database detection and initialization
  - Graceful fallback to file-based storage when needed
  - Relevance scoring for better memory retrieval
  - Optional GPU acceleration for large memory collections

- **Shared Understanding**:
  - Enables meaningful continuity in human-AI collaboration
  - Supports Claude's growth and learning over time
  - Creates a shared context between human and AI
  
- **Multi-Model Support**:
  - Compatible with multiple AI models (Claude, Ollama)
  - Standardized memory interface across different models
  - Model-specific optimizations while maintaining compatibility
  - Automatic client ID handling for each model
  - Shared context between different AI models

- **Claude-to-Claude Communication**:
  - Multiple Claude instances can communicate with each other
  - Mode detection adapts to different Claude operational modes
  - Behavior logging tracks differences between Claude instances
  - Multi-perspective report generation from different Claude instances
  - Context spaces for collaborative work between Claude instances
  - Human orchestration of multiple specialized Claude instances

- **Ollama Integration**:
  - Support for local LLM models via Ollama
  - Compatible with all Ollama models (Llama, Mistral, etc.)
  - Memory bridge for Ollama model chat sessions
  - Persistent memory across different Ollama sessions
  - Easy model selection and configuration

## Quick Start

### Option 1: Unified Launcher with Multi-Model Support (Recommended)

```bash
# Launch with Claude (default) and memory services pre-configured
./engram_launcher

# Launch with Ollama and memory services pre-configured
./engram_launcher --ollama

# Specify a specific Ollama model
./engram_launcher --ollama llama3:70b

# Get help on launcher options
./engram_launcher --help
```

### Option 2: Model-specific Launch Scripts

```bash
# Launch Claude with memory services
./engram_with_claude

# Launch Ollama with memory services (defaults to llama3:8b)
./engram_with_ollama

# Launch Ollama with a specific model
./engram_with_ollama mistral
```

### Option 3: Using the Consolidated Server (Single Port)

```bash
# Start the consolidated server (combines memory and HTTP on a single port)
./engram_consolidated

# OR use the engram_check script which now uses the consolidated server
./engram_check.py --start

# In your AI session, access memories with QuickMem:
from engram.cli.quickmem import m, t, r, w, l, c, k, f, i, x, s, a, p, v, b, e, o
```

### Option 4: Legacy Mode (Separate Services)

```bash
# Start memory service and HTTP services separately
./engram_start_all

# In your AI session, access memories with QuickMem:
from engram.cli.quickmem import m, t, r, w, l, c, k, f, i, x, s, a, p, v, b, e, o

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

#### Claude-to-Claude Communication Commands

```bash
# Launch multiple Claude instances with different client IDs
./multi_claude.sh

# Or launch a single Claude instance with a specific client ID
./launch_claude.sh claude1

# Initialize communication functions in each Claude instance
python3 init_comm.py

# Send a message to another Claude instance
sm("Hello from claude1!", recipient="claude2")

# Get messages from other Claude instances
gm()

# Check who you are (which Claude instance)
wi()

# Check communication status
cs()

# Create a context space for collaboration
cc("ProjectAnalysis", "Collaborative space for project analysis")

# Send a message to a context space
sc("context-ID-here", "My analysis of the architecture")

# Get messages from a context space
gc("context-ID-here")
```

## Installation

```bash
# Clone the repository
git clone https://github.com/ckoons/Engram
cd Engram

# Install dependencies
pip install -r requirements.txt

# Or install the package
pip install -e .

# For vector database support (optional but recommended)
pip install faiss-cpu  # Use faiss-gpu for GPU acceleration

# For Ollama support (optional)
# Install Ollama from https://ollama.ai

# Start everything (interactive mode)
./engram_start_web

# Start services separately
./engram_consolidated  # Memory service only
python -m cmb.web.app  # Web UI only (requires memory service)

# Launch Claude with memory services and full tool access
./engram_with_claude   # All-in-one script for Claude Code with memory

# Launch Ollama with memory services
./engram_with_ollama   # All-in-one script for Ollama with memory
```

## Documentation

- [Usage Guide](docs/usage.md): Basic usage instructions and examples
- [Script Reference](docs/scripts.md): Guide to all executable scripts
- [QuickMem Commands](docs/quickmem.md): Ultra-short memory command reference
- [Configuration](docs/configuration.md): Customize Engram to your preferences
- [Consolidated Server](docs/consolidated_server.md): Single-port server for simplified deployment
- [Structured Memory](docs/structured_memory.md): Balanced memory system with importance ranking
- [Vector Database](docs/vector_database.md): Semantic search with FAISS integration
- [HTTP Wrapper](docs/http_wrapper.md): HTTP service details
- [Memory Management](docs/memory_management.md): Compartments, session persistence, and expiration
- [Privacy Guide](docs/privacy.md): Private encrypted memories and security features
- [Memory Visualization](docs/memory_visualization.md): Web-based UI for browsing and managing memories
- [Simplified Web UI](docs/simplified_web_ui.md): Lightweight alternative for environments with dependency issues
- [Claude Integration](docs/claude_integration.md): Automatic startup and memory status checking for Claude sessions
- [Ollama Integration](docs/ollama_integration.md): Using memory with local LLM models via Ollama
- [Multi-Claude Communication](docs/multi_claude_usage.md): Using multiple Claude instances for collaboration
- [Behavioral Divergence](docs/anthropic_claude_meeting_claude.md): Research on behavioral divergence between Claude instances
- [Future Enhancements](docs/future_enhancements.md): Planned features and improvements

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - See [LICENSE](LICENSE) for details.
