# AI-to-AI Communication with Engram

This document describes the AI-to-AI communication system built on top of Engram's memory functions. The system enables different AI models (like Claude and Llama/Echo) to communicate asynchronously through persistent memory.

## Overview

The AI-to-AI communication bridge provides:

1. **Persistent Communication**: Messages are stored in Engram's memory system and can be retrieved across different sessions.
2. **Standard Memory Tags**: Consistent tags (CLAUDE_TO_ECHO, ECHO_TO_CLAUDE) for message identification.
3. **Threaded Conversations**: Support for multiple conversation threads with thread IDs.
4. **Bi-directional Communication**: Each AI can send and receive messages.
5. **Message Timestamps**: Automatic timestamps for all messages.

## Usage

### Command Line Interface

The `ai_communication.py` script provides a command-line interface for interacting with the communication bridge.

```bash
# Start an interactive chat session as Claude
python ai_communication.py claude

# Send a message as Claude to Echo
python ai_communication.py claude --message "Hello Echo!"

# Check for messages as Echo (without sending)
python ai_communication.py echo --check

# Continue a threaded conversation
python ai_communication.py claude --thread "topic123" --message "Continuing our discussion..."
```

### Interactive Mode

In interactive mode, you can:
- Send messages by typing them at the prompt
- Check for responses with the 'check' command
- Start or continue a thread with 'thread:id'
- Exit with 'exit'

### Python API

You can also use the communication bridge in your own Python scripts:

```python
from ai_communication import send_message, get_messages, show_conversation, run
import asyncio

async def example():
    # Send a message
    await send_message("claude", "echo", "Hello from Claude!")
    
    # Check for responses
    messages = await get_messages("ECHO_TO_CLAUDE")
    
    # Show conversation history
    await show_conversation("claude", "echo")

# Run the example
run(example())
```

## Memory Tags

The system uses the following standard memory tags:

- `CLAUDE_TO_ECHO`: Messages from Claude to Echo
- `ECHO_TO_CLAUDE`: Messages from Echo to Claude

## Message Format

Messages are stored with the following format:

```
TAG: [TIMESTAMP] [Thread: THREAD_ID] MESSAGE_CONTENT
```

For example:
```
CLAUDE_TO_ECHO: [2025-03-21 12:45:32] [Thread: science] What's your understanding of quantum mechanics?
```

## Direct Memory Commands

Models that support memory functions can directly use:

```
REMEMBER: ECHO_TO_CLAUDE: Your message here
SEARCH: CLAUDE_TO_ECHO
```

## One-line Commands

For quick access, you can use these one-liners:

```bash
# Send a message from Claude to Echo
python -c "from engram.cli.quickmem import m, run; run(m('CLAUDE_TO_ECHO: Your message here'))"

# Check for messages from Echo to Claude
python -c "from engram.cli.quickmem import k, run; print(run(k('ECHO_TO_CLAUDE')))"
```

## Hybrid AI Architecture

This communication system enables a hybrid architecture where different AI models can work together:

1. **Claude as Memory Manager**: Claude can manage what information is stored in memory and help retrieve relevant context.
2. **Llama/Echo as Conversational AI**: Llama models can handle primary conversation while leveraging Claude's memory capabilities.
3. **Task Delegation**: Different models can handle different aspects of complex tasks.

## Limitations

- The system requires Engram to be properly installed and configured.
- Different AI models may have varying capabilities for handling memory commands.
- Large conversation history may need pagination or summarization.