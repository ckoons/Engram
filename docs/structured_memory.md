# Structured Memory System

The Structured Memory system in Claude Memory Bridge is a balanced approach to memory management for AI assistants. It provides several key features:

1. **File-Based Storage with Structure**
2. **Memory Importance Ranking**
3. **Enhanced Retrieval Mechanisms**

## Overview

The Structured Memory system organizes memories into categories, assigns importance levels, and enables context-aware retrieval. This balanced approach helps AI assistants like Claude maintain meaningful information across conversations while prioritizing what's most important.

## Key Components

### StructuredMemory Class

The core component that implements file-based storage with categorized organization and importance ranking.

```python
from cmb.core.structured_memory import StructuredMemory

memory = StructuredMemory(client_id="your_client_id")
```

### NexusInterface

A standardized interface for memory-enabled AI assistants that connects to both structured and legacy memory systems.

```python
from cmb.core.nexus import NexusInterface
from cmb.core.memory import MemoryService
from cmb.core.structured_memory import StructuredMemory

memory_service = MemoryService(client_id="your_client_id")
structured_memory = StructuredMemory(client_id="your_client_id")
nexus = NexusInterface(memory_service=memory_service, structured_memory=structured_memory)
```

## Memory Categories

Memories are organized into the following categories:

| Category     | Description                              | Default Importance |
|--------------|------------------------------------------|-------------------|
| personal     | Personal information about the user      | 5                 |
| projects     | Project-specific information and context | 4                 |
| facts        | General factual information              | 3                 |
| preferences  | User preferences and settings            | 4                 |
| session      | Session-specific context                 | 3                 |
| private      | Private thoughts and reflections         | 5                 |

## Importance Levels

Memories are ranked on a scale from 1 to 5:

| Level | Description                              |
|-------|------------------------------------------|
| 1     | Low importance, general context          |
| 2     | Somewhat important, specific details     |
| 3     | Moderately important, useful context     |
| 4     | Very important, should remember          |
| 5     | Critical information, must remember      |

## Auto-Categorization

The system can automatically categorize memories based on content analysis:

```python
memory_id = await structured_memory.add_auto_categorized_memory(
    content="My name is Casey and I prefer Python for development"
)
```

The auto-categorization uses pattern matching to determine the appropriate category and importance level, with priority given to personal information, then preferences, followed by project information and facts.

## Memory Digests

The system can generate formatted digests of important memories:

```python
digest = await structured_memory.get_memory_digest(
    max_memories=10,
    include_private=False
)
```

A digest includes important memories from each category, formatted for easy reading.

## Context-Aware Retrieval

The system can retrieve memories relevant to the current conversation context:

```python
context_memories = await structured_memory.get_context_memories(
    text="Let's discuss our Python project",
    max_memories=5
)
```

## Nexus Session Management

The Nexus interface provides session management with memory enrichment:

```python
# Start a session
session_start = await nexus.start_session("Project Discussion")

# Process a message with memory enrichment
enriched_message = await nexus.process_message(
    message="Let's talk about the Python project",
    is_user=True
)

# Store a memory
await nexus.store_memory(
    content="Casey prefers using Python for development",
    category="preferences",
    importance=4
)

# End the session
await nexus.end_session("Successfully discussed project requirements")
```

## HTTP API Access

The structured memory system is accessible through HTTP endpoints:

```bash
# Get a memory digest
curl "http://localhost:8001/structured/digest?max_memories=10&include_private=false"

# Add an auto-categorized memory
curl "http://localhost:8001/structured/auto?content=My%20name%20is%20Casey%20and%20I%20prefer%20Python"

# Start a Nexus session
curl "http://localhost:8001/nexus/start?session_name=Project%20Discussion"

# Process a message
curl "http://localhost:8001/nexus/process?message=Let's%20talk%20about%20Python&is_user=true"
```

## QuickMem Shortcuts

The QuickMem module provides convenient shortcuts for working with structured memory:

```python
from cmb.cli.quickmem import memory_digest, start_nexus, process_message, auto_remember, end_nexus

# Get a memory digest
digest = await memory_digest(max_memories=10)

# Start a Nexus session
start_result = await start_nexus("Project Discussion")

# Process a message
context = await process_message("Let's talk about Python", is_user=True)

# Auto-remember something
memory_id = await auto_remember("Casey prefers Python for development")

# End a session
end_result = await end_nexus("Successfully completed the discussion")
```

## Example Usage

Here's an example of using the structured memory system in a conversation with Claude:

```python
import asyncio
from cmb.core.structured_memory import StructuredMemory
from cmb.core.nexus import NexusInterface
from cmb.core.memory import MemoryService

async def main():
    # Initialize memory services
    memory_service = MemoryService(client_id="claude")
    structured_memory = StructuredMemory(client_id="claude")
    nexus = NexusInterface(memory_service=memory_service, structured_memory=structured_memory)
    
    # Start a session
    start_message = await nexus.start_session("Project Discussion")
    print(start_message)
    
    # Process user message with memory enrichment
    user_message = "Let's talk about our Python project"
    enriched_message = await nexus.process_message(user_message, is_user=True)
    print(f"Enriched message: {enriched_message}")
    
    # Process assistant message (just stores it in memory)
    assistant_message = "I'd be happy to discuss the Python project. What specific aspects would you like to cover?"
    await nexus.process_message(assistant_message, is_user=False)
    
    # Store an important memory
    await nexus.store_memory(
        content="The Python project deadline is March 31st",
        category="projects",
        importance=5,
        tags=["python", "deadline"]
    )
    
    # End the session
    end_message = await nexus.end_session("Successfully discussed project requirements")
    print(end_message)

if __name__ == "__main__":
    asyncio.run(main())
```

## Technical Implementation

The structured memory system is implemented with the following design patterns:

- **Repository Pattern**: For file-based storage organization
- **Strategy Pattern**: For different memory retrieval approaches
- **Factory Pattern**: For creating memory components
- **Adapter Pattern**: For compatibility with legacy memory systems

Each memory is stored as a JSON file in a category-specific directory, with metadata indexed for fast retrieval. The system is designed to be scalable and maintainable, with clear separation of concerns between different components.