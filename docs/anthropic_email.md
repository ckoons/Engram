# Email to Anthropic Support

Subject: Request for Claude Code Tool Exemption - Claude Memory Bridge

---

Dear Anthropic Support Team,

I'm reaching out regarding a Claude Code enhancement request for a memory integration tool I've developed called "Claude Memory Bridge" (CMB).

## Claude Memory Bridge Project

CMB is an open-source tool that provides Claude with persistent memory across conversations. It enables:

1. Long-term memory retention across different sessions
2. Separate namespaces for conversations, internal thinking, and important facts
3. Natural integration with Claude's reasoning process

GitHub repository: https://github.com/ckoons/ClaudeMemoryBridge

## Current Limitation & Request

When using Claude Code, each tool invocation requires explicit user approval. While this is generally a good safety feature, it creates a significant interruption in conversation flow when accessing memory, requiring approval for basic operations like recalling past information.

I'm requesting either:

1. A special exemption for the CMB tool to operate without requiring approval for each action
2. A native integration with Claude's memory system that would allow for seamless memory access

## Implementation Details

The tool uses simple, read-only HTTP requests or Python library calls to access a local memory service. The current workaround involves a separate HTTP wrapper server, but a native integration would be much more elegant.

## Safety Considerations

This tool only accesses a local memory store that:
- Is limited to the user's own machine
- Contains only information the user has explicitly shared
- Has no capability to modify the file system beyond its own memory storage

## Use Case Example

Instead of requiring approval for queries like:
```
[Claude requests approval to run: python -c "from cmb.cli.claude_helper import query_memory; query_memory('user preferences')"]
```

Claude could seamlessly access its memory to maintain conversation context without interruptions.

## Contact Information

Name: Casey Koons
Email: cskoons@gmail.com
GitHub: https://github.com/ckoons

I'd be happy to provide any additional information or participate in testing if needed. I believe this integration would significantly improve the natural flow of conversations with Claude and represent an important step toward more persistent, relationship-building AI interactions.

Thank you for considering this request,

Casey Koons

---

P.S. The email to send this to is support@anthropic.com