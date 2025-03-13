# Claude Memory Bridge Usage Guide

This guide explains how to use Claude Memory Bridge (CMB) to give Claude persistent memory across sessions.

## Starting the Memory Bridge

To start the memory bridge service:

```bash
# Start with default settings (client ID: "claude", port: 8000)
cmb

# Use a custom client ID
cmb --client-id my-project

# Use a different port
cmb --port 8080

# Specify a custom data directory
cmb --data-dir /path/to/data

# Full options
cmb --client-id my-project --port 8080 --host 0.0.0.0 --data-dir ~/cmb-data
```

The memory bridge service must be running whenever you want to use Claude's memory capabilities.

## Using Memory in Claude Code

In your Claude Code sessions, import the helper functions and use them to store and retrieve memories:

```python
# Import the helper functions
from claude_helper import query_memory, store_memory, store_thinking, store_longterm

# Check if Claude remembers anything about a topic
memories = query_memory("project structure")

# Store an important fact in conversation memory
store_memory("fact", "Casey prefers VSCode for Python development")

# Store Claude's own thoughts (reflections, observations, reasoning)
store_thinking("I notice Casey prefers concise explanations with examples rather than theoretical discussions")

# Store critically important information that should be remembered long-term
store_longterm("Casey and I are collaborating on a book project alongside technical work")

# Store project-specific information
store_project_info("ClaudeMemoryBridge", "We started this project on March 13, 2025")

# Get formatted context for the current conversation
context = get_context("development preferences")
```

## Memory Namespaces

Claude Memory Bridge organizes memories into different namespaces:

1. **conversations**: General dialog and facts from your interactions
2. **thinking**: Claude's internal thought processes, observations, and reasoning
3. **longterm**: High-priority information that Claude should always remember
4. **projects**: Project-specific context and information

You can query, store, and clear memories in each namespace separately.

## Example Workflow

Here's a typical workflow when working with Claude:

1. **Start Memory Bridge**: Run `cmb` in a terminal window
2. **Begin Claude Code Session**: Start a new Claude Code session
3. **Import Memory Helper**: Import the helper functions
4. **Retrieve Relevant Context**: Have Claude check for relevant memories about the current task
5. **Work on Task**: Proceed with your conversation and work
6. **Store Important Information**: Have Claude store key information during the session
7. **End Session**: When done, have Claude summarize and store the session for future reference

## Example: Continuing a Project

```
User: Let's continue working on the ClaudeMemoryBridge project. What do you remember about it?

Claude: Let me check my memory about the ClaudeMemoryBridge project.

[Claude runs: from claude_helper import query_memory; memories = query_memory("ClaudeMemoryBridge", namespace="projects")]

I remember the following about the ClaudeMemoryBridge project:
1. We started this project on March 13, 2025
2. It provides namespaces for different types of memories: conversations, thinking, longterm, and projects
3. The core components include a memory service, API server, and helper library

Let's continue working on it. What aspect would you like to focus on today?
```

## CLI Commands

The `claude_helper.py` script can also be used as a CLI tool for testing:

```bash
# Check health status
python -m claude_helper health

# Query memory
python -m claude_helper query "project structure" --namespace conversations

# Store memory
python -m claude_helper store "key" "value" --namespace conversations

# Store thought
python -m claude_helper thinking "This is an important observation"

# Store longterm memory
python -m claude_helper longterm "This is critical information"

# Store project information
python -m claude_helper project "ProjectName" "Project information to remember"

# Get context
python -m claude_helper context "current topic"

# Clear namespace
python -m claude_helper clear conversations
```

## Advanced Features

### Memory Context for Enhanced Prompts

You can inject memory context directly into prompts to help guide Claude:

```python
from claude_helper import get_context

# Get memory context for the current topic
context = get_context("user preferences")

# Use it in your prompt
prompt = f"""
{context}

Based on what you know about the user, recommend a Python library for their current project.
"""
```

### Storing Conversation Summaries

At the end of sessions, you can store a summary:

```python
from claude_helper import store_memory

# Store session summary
store_memory(
    "session_summary", 
    "In this session, we implemented the API server for Claude Memory Bridge, " +
    "added namespace support, and created the startup script."
)
```

### Managing Memory Growth

For long-running projects, you may want to clear old or irrelevant memories:

```python
from claude_helper import clear_memories

# Clear a specific namespace
clear_memories("conversations")
```

## Troubleshooting

If you encounter issues, check the following:

1. **Memory Bridge Not Running**: Make sure the `cmb` service is running in a terminal
2. **Connection Errors**: Verify the correct port (default: 8000) is being used
3. **Import Errors**: Ensure `claude_helper.py` is accessible in your Python path
4. **mem0 Not Found**: If you want vector search, install mem0ai: `pip install mem0ai>=0.1.65`

The memory bridge server logs to stdout, so check the terminal where it's running for error messages.

## Custom Environment Variables

You can configure CMB using environment variables:

- `CMB_URL`: Memory Bridge server URL (default: "http://127.0.0.1:8000")
- `CMB_CLIENT_ID`: Default client ID (default: "claude")
- `CMB_DATA_DIR`: Data directory path (default: "~/.cmb")