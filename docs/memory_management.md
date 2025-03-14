# Memory Management in Claude Memory Bridge

This document provides details on advanced memory management features in Claude Memory Bridge, including compartmentalization, session persistence, expiration control, and memory correction.

## Memory Compartmentalization

Memory compartmentalization allows you to organize memories into distinct categories or projects. This helps with:

- Keeping project-related memories separate
- Focusing Claude's attention on relevant context
- Providing structured organization of information
- Supporting hierarchical memory organization

### Creating and Using Compartments

Compartments can be created and managed using the `compartment()` function (alias `c()`):

```python
from cmb.cli.quickmem import compartment, c

# Create a new compartment and store information
compartment("ProjectX: This is important information about Project X")

# Or use the shorthand
c("ProjectX: Information about the project goals and timeline")

# Activate an existing compartment (without adding new information)
c("ProjectX")  # Now ProjectX memories will be included in context

# List all active compartments
c()
```

### Hierarchical Compartments

Compartments support hierarchical organization using dot notation:

```python
# Create nested compartments
c("Book.Chapter1: Introduction to memory systems")
c("Book.Chapter2: Advanced memory techniques")

# Activate entire hierarchies
c("Book")  # Activates all Book.* compartments
```

This allows for structured organization of related information across multiple levels.

### Deactivating Compartments

When you no longer need a compartment's memories included in context:

```python
# Using the HTTP helper directly
from cmb.cli.http_helper import deactivate_compartment

# Deactivate a specific compartment
deactivate_compartment("ProjectX")
```

## Session Persistence

Session persistence lets you maintain important information across different conversation sessions with Claude.

### Writing Session Memories

Use the `write()` function (alias `w()`) to persist information:

```python
from cmb.cli.quickmem import write, w

# Store specific information for future sessions
write("We discussed adding vector search capabilities to the project")

# Store with metadata for better organization
write("User preferences", {"theme": "dark", "notifications": True})

# Write a session summary (no parameter)
w()  # Auto-generates a summary of important session details
```

Session memories are automatically included in future contexts, ensuring continuity between conversations.

### Use Cases for Session Persistence

- Recording progress on long-term projects
- Saving important decisions and rationales
- Maintaining context across multiple coding sessions
- Preserving complex technical explanations
- Tracking project status and next steps

## Memory Expiration Control

Memory expiration control enables you to manage how long specific memories are retained.

### Setting Expiration Dates

Use the `keep()` function (alias `k()`) to set expiration dates:

```python
from cmb.cli.quickmem import keep, k

# Keep a specific memory for 90 days
k("memory_id_123", 90)

# Use default retention (30 days)
k("memory_id_456")
```

### Finding Memory IDs

To apply expiration control, you need the memory's ID. You can find this:

1. Through the memory visualization UI (coming soon)
2. By checking the HTTP response when storing a memory
3. By using the memory search function with verbose output

```python
# Store a memory and capture its ID
from cmb.cli.http_helper import store_memory
result = store_memory("key", "value")
memory_id = result.get("memory_id")

# Now use that ID to set expiration
k(memory_id, 60)  # Keep for 60 days
```

## Memory Correction

The memory correction feature helps address the issue of incorrect information in Claude's memory. This can happen when:

- Information was misheard or misinterpreted
- Facts have changed since the information was stored
- Information was incorrectly entered initially
- Requirements or specifications have changed

### Correcting Misinformation

Use the `correct()` function (alias `cx()`) to handle incorrect information:

```python
from cmb.cli.quickmem import correct, cx

# Correct a fact with replacement
correct("Casey lives in San Francisco", "Casey lives in Seattle")

# Using the shorthand alias
cx("Project deadline is March 15", "Project deadline is March 30")

# Just forget without replacement
correct("Casey enjoys playing golf")
```

### Real-Time Corrections During Conversations

The correction feature is particularly valuable during conversations when Claude references incorrect information:

```
Claude: "How's your brother Michael doing?"
You: "I don't have a brother."
Claude: [cx("Casey has a brother named Michael", "Casey doesn't have any brothers")]
Claude: "I apologize for my mistake. I've updated my memory and will remember that you don't have any brothers."
```

This pattern helps Claude maintain accurate memory without disrupting the conversation flow.

## Combining Management Features

These memory management features can be combined for powerful memory organization:

```python
# Create a project compartment
c("ClientProject: New project for client XYZ")

# Add information to the compartment
c("ClientProject: The project deadline is March 15")

# Ensure this information is kept for at least 90 days
# (First get the memory ID from the compartment)
memory_id = "..." # ID from compartment store operation
k(memory_id, 90)

# Correct information if needed
cx("The project deadline is March 15", "The project deadline is March 30")

# At the end of your session, write a summary
w("Made progress on ClientProject, discussed architecture options")
```

## Technical Implementation

Behind the scenes, these features use:

- Memory namespaces for compartment storage
- Timestamp metadata for expiration control
- JSON storage for session persistence
- Activation flags for determining context inclusion

The HTTP wrapper exposes these features through simple endpoints that don't require tool approval when used from Claude Code.

## Best Practices

- Use compartments for distinct projects or topics
- Set appropriate expiration dates based on information relevance
- Write session summaries at the end of important conversations
- Use hierarchical compartments for complex information structures
- Regularly review and clean up unused compartments