# Claude Memory Bridge Development Notes

## Project Overview

Claude Memory Bridge (CMB) is a project to give Claude persistent memory across different sessions. The project aims to:

1. Allow Claude to remember past conversations
2. Enable Claude to store and retrieve its own thoughts
3. Maintain longterm, high-priority memories
4. Share context across different projects

## Key Features

- Multiple memory namespaces for different types of information
- Both vector-based (using mem0) and fallback memory implementations
- Simple Claude helper interface for store/retrieve operations
- Easy-to-use CLI for starting the memory service

## Code Style and Conventions

### Python

- Use f-strings for string formatting
- Add type hints to function signatures
- Follow PEP 8 guidelines
- 4 spaces for indentation
- Use docstrings for all functions and classes

### Comments

- Include brief comments for complex sections
- Add TODOs for future improvements
- Document any workarounds or tricky implementations

### Error Handling

- Use try/except blocks for operations that could fail
- Log errors with appropriate level (info, warning, error)
- Return meaningful error messages

## Common Commands

```bash
# Start memory bridge
cd ~/projects/github/ClaudeMemoryBridge
./cmb_start.sh

# With custom client ID
./cmb_start.sh --client-id project-x

# Run tests
cd ~/projects/github/ClaudeMemoryBridge
python -m pytest tests

# Install development version
cd ~/projects/github/ClaudeMemoryBridge
pip install -e .
```

## Future Enhancements

1. Web UI for memory browsing and management
2. Memory summarization and pruning
3. Enhanced vector retrieval with better ranking
4. Multi-user support
5. Integration with other AI systems beyond Claude

## Deployment Notes

The memory bridge should be run as a separate service, ideally started when the system boots. It can be run:

1. Directly: `./cmb_start.sh`
2. Via system service: Create a systemd or launchd service
3. As a background process: `nohup ./cmb_start.sh &`

For production use, consider running behind a proper web server like nginx with authentication.