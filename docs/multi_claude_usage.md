# Multi-Claude System Usage Guide

This guide provides instructions for using the multi-Claude system for Claude-to-Claude communication and collaboration.

## Prerequisites

1. Ensure the Engram memory system is installed and configured
2. Verify that all required dependencies are installed (see requirements.txt)
3. Make sure the `claude` binary is available in your PATH

## Quick Start

### 1. Launch Multiple Claude Instances

Use the `multi_claude.sh` script to launch multiple Claude instances with different client IDs:

```bash
./multi_claude.sh
```

This will launch Claude instances based on the configuration in `claude_instances.json`.

### 2. Test Communication Between Instances

In each Claude instance, you can use the following functions to communicate:

#### Sending Messages

```python
# Send a message to another Claude instance
sm("Hello from claude1! What are you working on?", recipient="claude2")

# Send a high-priority message
sm("Urgent: Need your analysis on this data", recipient="claude2", priority=4)

# Broadcast a message to all instances
sm("I've completed the initial analysis", recipient="all")
```

#### Receiving Messages

```python
# Get all messages
messages = gm()

# Get unread messages only
unread = gm(unread_only=True)

# Get messages from a specific sender
from_claude1 = gm(sender="claude1")

# Get high-priority messages
important = gm(min_priority=3)
```

#### Mark Messages as Read/Replied

```python
# Mark a message as read
mr("message-id-here")

# Mark a message as replied
mp("message-id-here")
```

### 3. Create Context Spaces for Collaboration

```python
# Create a context space for a specific project
context_id = cc("Data Analysis Project")

# Send a message to the context space
sc(context_id, "Here's my initial analysis of the dataset")

# Get messages from the context space
messages = gc(context_id)
```

### 4. Get Communication Status

```python
# Check which Claude instances are active
status = cs()

# Check your instance ID
my_id = wi()
```

## Demo Script

For a complete demonstration, run the `demo_multi_claude.py` script:

```bash
./demo_multi_claude.py
```

This will:
1. Start the memory service
2. Log behavior events for analysis
3. Generate example perspectives from each Claude instance
4. Generate a multi-perspective report
5. Launch Claude instances for interactive testing

## Advanced Usage

### Behavior Logging and Analysis

The system tracks how different Claude instances behave with the `BehaviorLogger` class:

```python
from cmb.core.behavior_logger import BehaviorLogger

# Create a logger
logger = BehaviorLogger()

# Log a behavior event
logger.log_behavior(
    client_id="claude1",
    event_type="execution",
    details={"action": "file_write", "path": "/tmp/example.txt"}
)

# Analyze divergence between instances
analysis = logger.analyze_divergence(["claude1", "claude2"])
print(f"Divergence score: {analysis['divergence_score']}")
```

### Multi-Perspective Reports

Generate reports that combine perspectives from multiple Claude instances:

```python
from cmb.core.report_generator import MultiClaudeReport

# Create a report generator
report_gen = MultiClaudeReport(["claude1", "claude2"])

# Save perspectives from each instance
report_gen.save_perspective(
    claude_id="claude1",
    topic="AI Ethics",
    perspective="My analysis of AI ethics focuses on..."
)

# Generate a report combining all perspectives
report = report_gen.generate_report(
    title="Perspectives on AI Ethics",
    introduction="This report combines views from multiple Claude instances..."
)
```

## Function Reference

### Communication Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `sm` | Send a message | content, recipient="all", message_type="handoff", context="", priority=2, action="" |
| `gm` | Get messages | sender=None, recipient=None, message_type=None, min_priority=1, unread_only=False, limit=10 |
| `mr` | Mark a message as read | message_id |
| `mp` | Mark a message as replied | message_id |
| `ho` | Send a handoff message | content, context="", priority=3 |
| `cc` | Create a context space | context_name, description="" |
| `lc` | List available context spaces | None |
| `sc` | Send a message to a context space | context_id, content, message_type="update", priority=2, action="" |
| `gc` | Get messages from a context space | context_id, message_type=None, min_priority=1, unread_only=False, limit=20 |
| `wi` | Get your instance ID | None |
| `cs` | Get communication status | None |

### Memory Functions

For information on memory functions, see the [Engram documentation](./structured_memory.md).

## Troubleshooting

### Common Issues

1. **Memory service not running**: Run `./engram_with_claude --memory-only` to start the memory service

2. **Communication functions not available**: Make sure you're using a client ID when launching Claude:
   ```bash
   ./engram_with_claude --client-id claude1
   ```

3. **Permission denied errors**: Ensure the scripts are executable:
   ```bash
   chmod +x multi_claude.sh demo_multi_claude.py
   ```

4. **Claude not found**: Make sure the `claude` binary is in your PATH

### Getting Help

If you encounter issues, check the log files in the `logs/` directory for error messages.

## Further Reading

- [Structured Memory Documentation](./structured_memory.md)
- [Claude Integration](./claude_integration.md)
- [Anthropic Findings](./anthropic_claude_meeting_claude.md)