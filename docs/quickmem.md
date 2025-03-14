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
   from cmb.cli.quickmem import mem, think, remember, write, load, compartment, keep
   # Or use the ultra-short aliases
   from cmb.cli.quickmem import m, t, r, w, l, c, k
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

# Write session memory (persist across sessions)
w("Important insights from today's brainstorming")

# Load previously stored session memories
l()  # Load the most recent session memory
l(3)  # Load the 3 most recent session memories

# Create or use memory compartments
c("ProjectX: This is important information about ProjectX")

# Keep memory for specific time period
k("memory123", 90)  # Keep memory for 90 days

# Correct misinformation
cx("Casey has a brother named Michael", "Casey doesn't have a brother")  # Correct wrong information
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

### Session Persistence (Write and Load)

The `write()` command (alias `w()`) allows you to persist important information from the current session:

```python
# Store specific information for future sessions
write("We discussed adding vector search capabilities to the project")

# Store with metadata
write("User preferences", {"theme": "dark", "notifications": True})

# Write session summary (no parameter)
w()  # Auto-generates a summary of important session details
```

This creates persistent memories that will be available in future conversations even after the current session ends.

The complementary `load()` command (alias `l()`) retrieves previously stored session memories:

```python
# Load the most recent session memory
load()

# Load multiple session memories
load(5)  # Load the 5 most recent session memories

# Use the short alias
l()  # Load the most recent session memory
```

This makes it easy to restore context from previous sessions when starting a new conversation.

### Memory Compartmentalization

The `compartment()` command (alias `c()`) creates and manages memory compartments:

```python
# Create and store in a compartment
c("ProjectX: This is important information for ProjectX")

# Activate an existing compartment
c("ProjectX")  # Now ProjectX memories will be included in context

# List active compartments
c()  # Shows all currently active compartments
```

Compartments can be hierarchical by using dot notation:

```python
# Create nested compartments
c("Book.Chapter1: Introduction to memory systems")
c("Book.Chapter2: Advanced memory techniques")

# Activate entire hierarchies
c("Book")  # Activates all Book.* compartments
```

### Memory Expiration Control

The `keep()` command (alias `k()`) sets expiration dates for memories:

```python
# Keep a specific memory for 90 days
k("memory_id_123", 90)

# Use default retention (30 days)
k("memory_id_456")
```

This allows fine-grained control over how long specific memories should be retained.

### Correcting Misinformation

The `correct()` command (alias `cx()`) provides a way to handle incorrect information in memory:

```python
# Correct a misconception with the right information
correct("Casey has a brother named Michael", "Casey doesn't have a brother")

# Just forget incorrect information without a replacement
correct("Casey lives in San Francisco")

# Use the shorthand
cx("Casey's favorite color is green", "Casey's favorite color is blue")
```

This is especially useful during conversations when Claude remembers something incorrectly:

1. Claude: "How is your brother Michael doing?"
2. You: "I don't have a brother."
3. Claude: [Claude runs: `cx("Casey has a brother named Michael", "Casey doesn't have a brother")`]
4. Claude: "I apologize for the mistake. I've corrected my memory."

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
  3. Casey has a brother named Michael.

Based on my memory, I know that your current wife is Olivia, your first wife Dawn passed away in 2004, and you have a brother named Michael.

User: Actually, I don't have a brother. That information is incorrect.

Claude: I apologize for the error. Let me correct that in my memory.

[Claude runs: cx("Casey has a brother named Michael", "Casey doesn't have any brothers")]

✓ Corrected: "Casey has a brother named Michael" → "Casey doesn't have any brothers"

I've corrected my memory. I now understand that you don't have any brothers. Thank you for the correction.

User: Let's organize memories about my family in a separate compartment.

Claude: [Claude runs: c("Family: Casey is married to Olivia and his first wife Dawn passed away in 2004")]

🗂️ Created new compartment 'Family' and stored content

I've created a Family compartment and stored that information. I'll make sure to keep family-related memories organized there from now on.

User: I want to make sure these memories are preserved for at least 3 months.

Claude: [Claude runs: k("memory_id_for_family_info", 90)]

📅 Memory will be kept for 90 days

I've set that memory to be kept for 90 days. I'll remember these important details about your family during that time.

User: Great! Let's write this information to session memory so it persists across conversations.

Claude: [Claude runs: w("Casey is married to Olivia. His first wife Dawn passed away in 2004. Casey doesn't have any siblings.")]

📝 Session memory stored

I've written this family information to session memory, so it will persist across our future conversations. Is there anything else you'd like me to remember?

User: In our next conversation, how would I retrieve this session memory?

Claude: That's a great question! In our next conversation, you can retrieve the session memory like this:

[Claude runs: l()]

📖 Loaded 1 session memories:
  1. Casey is married to Olivia. His first wife Dawn passed away in 2004. Casey doesn't have any siblings.

You can use the `load()` function or its shorthand `l()` to retrieve session memories. By default, it retrieves the most recent memory, but you can also specify how many memories to load:

[Claude runs: l(3)]

📖 Loaded 3 session memories:
  1. Casey is married to Olivia. His first wife Dawn passed away in 2004. Casey doesn't have any siblings.
  2. Casey likes to work on AI projects and enjoys Python programming.
  3. Casey prefers dark mode for all his applications.

This way, you can quickly restore context from our previous conversations.
```

## Behind the Scenes

QuickMem uses the HTTP wrapper to avoid requiring tool approval for each memory operation. It makes simple web requests to the HTTP wrapper running on port 8001.