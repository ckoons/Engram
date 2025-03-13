# QuickMem - Shorthand Memory Commands

QuickMem provides ultra-simple shorthand commands for accessing and storing memories during Claude Code sessions.

## Setup

1. Start both the memory bridge and HTTP wrapper:
   ```bash
   # Terminal 1
   cd ~/projects/github/ClaudeMemoryBridge
   ./cmb
   
   # Terminal 2
   cd ~/projects/github/ClaudeMemoryBridge
   ./cmb_http
   ```

2. In your Claude Code session, import QuickMem:
   ```python
   from cmb.cli.quickmem import mem, think, remember
   # Or use the ultra-short aliases
   from cmb.cli.quickmem import m, t, r
   ```

## Usage

### Access Memories with One Word

```python
# Check memories about a specific topic
mem("wife")

# Check general personal information
mem()
```

Just say `mem("topic")` anytime during your conversation to check memories about that topic!

### Store New Memories Easily

```python
# Store thoughts about the conversation
think("Casey seems interested in making this interface simpler")

# Store important facts
remember("Casey works on AI projects and likes Python")

# Auto-generate thoughts based on current context (no parameter needed)
think()

# Auto-remember important information from the conversation
remember()
```

## Ultra-Short Aliases

If you want even shorter commands:

```python
# Access memories
m("family")

# Store a thought
t("This conversation is going well")

# Remember important information
r("Casey's birthday is in July")

# Automatic reflection and memory (no parameters needed)
t()  # Auto-generate a thought about the conversation
r()  # Auto-remember important aspects of the conversation

# Forget incorrect information (requires a parameter)
f("Casey has a brother named Michael")  # Mark this as incorrect information to ignore

# Ignore current information (requires a parameter)
i("Please don't store this part of our conversation")  # Ignore specific content
```

## Memory Management Commands

### Forgetting Information

The `forget()` command (alias `f()`) marks specific information as incorrect or to be ignored:

```python
# Mark incorrect or outdated information to be ignored
forget("Casey lives in San Francisco")

# Use the short alias
f("Casey's favorite color is green")
```

All `forget` commands require a parameter specifying exactly what to forget. The system will store this as a special "FORGET/IGNORE" instruction that you should check when retrieving memories.

### Ignoring Current Context

The `ignore()` command (alias `i()`) explicitly asks Claude to ignore specific information from the current conversation:

```python
# Ignore sensitive or irrelevant information
ignore("My password is 12345")

# Use the short alias
i("This sentence is just an example and should be ignored")
```

The `ignore` command acknowledges the request without storing it, allowing you to specify parts of a conversation that should not be remembered.

## Conversation Flow

Here's how to use QuickMem in a natural conversation:

```
User: Can you tell me what you remember about my family?

Claude: Let me check my memory for that information.

[Claude runs: m("family")]

📝 Memory found for 'family':

🌟 Important information:
  1. Casey's current wife's name is Olivia.
  2. Casey's first wife Dawn passed away in 2004.

Based on my memory, I know that your current wife is Olivia, and your first wife Dawn passed away in 2004.

User: Do I have any siblings?

Claude: I don't see any information about siblings in my memory. Would you like to tell me about them?

User: Yes, I have a brother named Michael.

Claude: [Claude runs: r("Casey has a brother named Michael")]

🌟 Information stored in long-term memory

I'll remember that you have a brother named Michael. Thank you for sharing that information with me.
```

## Behind the Scenes

QuickMem uses the HTTP wrapper to avoid requiring tool approval for each memory operation. It makes simple web requests to the HTTP wrapper running on port 8001.