# Claude Memory Bridge Usage Guide

This guide explains how to use Claude Memory Bridge (CMB) to give Claude persistent memory across sessions.

## Starting the Memory Bridge

To start the memory bridge services:

```bash
# Start all services (memory bridge and HTTP wrapper)
./cmb_start_all

# Start with default settings (client ID: "claude", port: 8000)
./cmb

# Start HTTP wrapper (port: 8001)
./cmb_http

# Use a custom client ID
./cmb --client-id my-project

# Use a different port
./cmb --port 8080

# Specify a custom data directory
./cmb --data-dir /path/to/data

# Full options
./cmb --client-id my-project --port 8080 --host 0.0.0.0 --data-dir ~/cmb-data
```

The memory bridge service must be running whenever you want to use Claude's memory capabilities.

## Using QuickMem (Recommended)

For the easiest experience, use the QuickMem shortcuts:

```python
# Import the ultra-short memory commands
from cmb.cli.quickmem import m, t, r, w, c, k

# Access memories with one command
m("project")  # Check memories about your project

# Store thoughts about the conversation
t("User prefers clean code with detailed comments")

# Remember important information
r("User's project deadline is next Friday")

# Write session memory for persistence
w("Today we worked on implementing memory compartments")

# Create or use memory compartments
c("ProjectX: This is important info about ProjectX")

# Control memory expiration
k("memory_id_123", 90)  # Keep for 90 days
```

See [QuickMem Commands](quickmem.md) for detailed usage.

## Using HTTP Helper (No Tool Approval)

For more complete functionality without tool approval:

```python
# Import the HTTP helper
from cmb.cli.http_helper import query_memory, store_memory, store_thinking, store_longterm

# Check if Claude remembers anything about a topic
memories = query_memory("project structure")

# Store an important fact in conversation memory
store_memory("fact", "Casey prefers VSCode for Python development")

# Store Claude's own thoughts
store_thinking("I notice Casey prefers concise explanations with examples")

# Store critically important information
store_longterm("Casey and I are collaborating on a memory management project")
```

## Using Direct Helper (With Tool Approval)

For direct access to all features (requires tool approval):

```python
# Import the helper functions
from cmb.core.claude_helper import query_memory, store_memory, store_thinking, store_longterm

# Check if Claude remembers anything about a topic
memories = query_memory("project structure")

# Store an important fact in conversation memory
store_memory("fact", "Casey prefers VSCode for Python development")

# Store Claude's own thoughts
store_thinking("I notice Casey prefers concise explanations with examples")

# Store critically important information
store_longterm("Casey and I are collaborating on a memory management project")
```

## Memory Namespaces

Claude Memory Bridge organizes memories into different namespaces:

1. **conversations**: General dialog and facts from your interactions
2. **thinking**: Claude's internal thought processes, observations, and reasoning
3. **longterm**: High-priority information that Claude should always remember
4. **projects**: Project-specific context and information
5. **compartments**: Topic-specific organized memories (new in v0.2.0)
6. **session**: Cross-conversation persistent memories (new in v0.2.0)

You can query, store, and clear memories in each namespace separately.

## Memory Management Features

### Compartmentalization

Organize memories into distinct categories using the `c()` function:

```python
# Create and store in a compartment
c("ProjectX: This is important information for ProjectX")

# Activate an existing compartment
c("ProjectX")  # Now ProjectX memories will be included in context

# List active compartments
c()  # Shows all currently active compartments

# Create hierarchical compartments
c("Book.Chapter1: Introduction to memory systems")
c("Book.Chapter2: Advanced memory techniques")
```

### Session Persistence

Maintain important information across sessions with the `w()` function:

```python
# Store specific information for future sessions
w("We discussed adding vector search capabilities to the project")

# Store with metadata for better organization
w("User preferences", {"theme": "dark", "notifications": True})

# Write a general session summary
w()  # Auto-generates a summary of important details
```

### Memory Expiration Control

Control how long memories are retained with the `k()` function:

```python
# Keep a specific memory for 90 days
k("memory_id_123", 90)

# Use default retention (30 days)
k("memory_id_456")
```

## Example Workflow

Here's a typical workflow with the advanced memory features:

1. **Start Services**: Run `./cmb_start_all` in a terminal
2. **Begin Claude Code Session**: Start a new Claude Code session
3. **Import QuickMem**: `from cmb.cli.quickmem import m, t, r, w, c, k`
4. **Create Project Compartment**: `c("MyProject: Working on memory features")`
5. **Activate Compartment**: `c("MyProject")` 
6. **Retrieve Context**: `m("project requirements")`
7. **Work and Store Information**: Use `t()`, `r()`, and `c()` during work
8. **Persist Important Info**: Use `w()` to save key information for next time
9. **Control Retention**: Use `k()` for important memories

## Example: Using Compartments

```
User: Let's organize our project information in compartments.

Claude: Good idea. Let me create a compartment for our project structure.

[Claude runs: from cmb.cli.quickmem import c]

[Claude runs: c("ProjectStructure: ClaudeMemoryBridge has a core module, API layer, and CLI interface")]

🗂️ Created new compartment 'ProjectStructure' and stored content

I've created a "ProjectStructure" compartment and stored basic information about our codebase organization. Let's add more details to it:

[Claude runs: c("ProjectStructure: The core module handles vector search and memory persistence")]

🗂️ Added to compartment: 'ProjectStructure'

Now I'll activate this compartment so its information is included in our context:

[Claude runs: c("ProjectStructure")]

🗂️ Activated compartment: 'ProjectStructure'

Great! Now when we discuss the project structure, I'll automatically include this information in my responses. Would you like to create any other compartments?
```

## CLI Commands

For testing and debugging:

```bash
# Check health status
curl http://localhost:8001/health

# Query memory
curl "http://localhost:8001/query?query=project%20structure&namespace=conversations"

# Store memory
curl "http://localhost:8001/store?key=fact&value=This%20is%20important"

# Create a compartment
curl "http://localhost:8001/compartment/create?name=ProjectX"

# Write session memory
curl "http://localhost:8001/write?content=Session%20notes%20here"
```

## Troubleshooting

If you encounter issues, check the following:

1. **Services Not Running**: Ensure both `cmb` and `cmb_http` are running
2. **Connection Errors**: Verify the correct ports (8000/8001) are being used
3. **Import Errors**: Ensure packages are in your Python path
4. **Vector Search Issues**: Install mem0ai: `pip install mem0ai>=0.1.65`
5. **Compartment Not Found**: Check if the compartment exists with `c()`

The memory bridge server logs to stdout, so check the terminal for error messages.

## Custom Environment Variables

You can configure CMB using environment variables:

- `CMB_URL`: Memory Bridge server URL (default: "http://127.0.0.1:8000")
- `CMB_HTTP_URL`: HTTP wrapper URL (default: "http://127.0.0.1:8001")
- `CMB_CLIENT_ID`: Default client ID (default: "claude")
- `CMB_DATA_DIR`: Data directory path (default: "~/.cmb")