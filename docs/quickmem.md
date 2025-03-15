# QuickMem Commands

QuickMem provides ultra-short commands for Claude to access memory in a natural conversation. These shorthand functions make memory access feel like a seamless part of the conversation rather than an explicit tool.

## Import QuickMem

```python
# Full imports
from cmb.cli.quickmem import mem, think, remember, write, load, compartment, keep, forget, ignore, correct, status, agency

# Or use the ultra-short aliases
from cmb.cli.quickmem import m, t, r, w, l, c, k, f, i, x, s, a
```

## Memory Functions

| Function | Alias | Description | Example |
|----------|-------|-------------|---------|
| `mem(query, namespaces, limit)` | `m` | Search memories | `m("project")` |
| `think(thought)` | `t` | Store a thought | `t("Casey values clear documentation")` |
| `remember(info)` | `r` | Store important info | `r("Casey's birthday is April 15")` |
| `write(note, metadata)` | `w` | Store session memory | `w("Today we discussed memory architecture")` |
| `load(limit)` | `l` | Load session memories | `l(3)` |
| `compartment(info)` | `c` | Manage memory compartments | `c("ProjectX: Info about ProjectX")` |
| `keep(memory_id, days)` | `k` | Set memory retention | `k("memory_id", 90)` |
| `forget(info)` | `f` | Mark information to forget | `f("Meeting is on Tuesday")` |
| `ignore(info)` | `i` | Explicitly ignore information | `i("Test credentials in this file")` |
| `correct(wrong_info, correct_info)` | `x` | Correct misinformation | `x("Lives in NY", "Lives in Seattle")` |
| `status(start_if_not_running)` | `s` | Check memory service status | `s()` or `s(True)` |
| `agency(prompt)` | `a` | Claude's memory agency | `a("Should I remember this detail?")` |

## Detailed Usage

### Memory Search

```python
# Basic memory search
m("project")  # Search for "project" in default namespaces

# Search with specific namespaces
m("code style", ["thinking", "longterm"])

# Search with limit
m("meeting", limit=5)  # Return up to 5 results per namespace

# General memory check (no specific query)
m()  # Returns general context from recent conversations
```

### Thinking

```python
# Store a thought
t("The user seems to prefer functional programming patterns")

# Generate a reflective thought automatically
t()  # Stores a default reflection about the conversation
```

### Long-term Memory

```python
# Store important information
r("Casey prefers dark mode in VSCode")

# Generate default memory reminder
r()  # Stores a default memory about the importance of memory persistence
```

### Session Memory

```python
# Write a session memory for persistence across conversations
w("Today we designed the memory compartmentalization feature")

# Write with metadata
w("Memory architecture meeting notes", {"project": "CMB", "topic": "Architecture"})

# Load previous session memories
l()      # Load most recent session memory
l(5)     # Load up to 5 session memories
```

### Memory Compartments

```python
# Create and store in a compartment
c("ProjectX: Information about the ProjectX initiative")

# Activate an existing compartment
c("ProjectX")

# List active compartments
c()
```

### Memory Management

```python
# Keep a memory for a specific period
k("memory_id_123")             # Default 30 days
k("memory_id_123", 90)         # Keep for 90 days

# Mark information to forget
f("The meeting is on Tuesday")  # When that information is wrong

# Explicitly ignore information
i("The test API key shown in this example")  # Information to ignore

# Correct misinformation
x("Casey works at Google", "Casey works at Anthropic")
```

### Status Checking

```python
# Check memory service status
s()  # Basic status check

# Check and auto-start if not running
s(True)
```

### Claude's Agency

```python
# Ask Claude to use its judgment about how to handle information
a("I think this information about project scope might be important")

# Provide a prompt for Claude to consider
a("Should I categorize this in the project compartment or as general knowledge?")

# Simple invocation without guidance
a()  # Claude will reflect on what's appropriate for the current context
```

## Default Namespaces

- `conversations`: Everyday dialog and conversation history
- `thinking`: Claude's thoughts and reflections
- `longterm`: Important long-term memories
- `projects`: Project-specific information
- `compartments`: Directory of memory compartments
- `session`: Cross-conversation memory persistence
- `compartment-XYZ`: Individual compartment contents

## Command Line Interface

QuickMem can also be used from the command line:

```bash
python -m cmb.cli.quickmem think "This is an interesting thought"
python -m cmb.cli.quickmem remember "This is important information"
python -m cmb.cli.quickmem forget "This information is incorrect"
python -m cmb.cli.quickmem compartment "ProjectX: Info about Project X"
python -m cmb.cli.quickmem write "Session memory note"
python -m cmb.cli.quickmem load 5
python -m cmb.cli.quickmem status start
python -m cmb.cli.quickmem project  # Search for "project"
```