# Ollama Integration in Engram

This document describes how to integrate Ollama models with Engram's memory and communication systems.

## Overview

Engram provides a robust memory framework and AI-to-AI communication system that allows different language models to work together. The Ollama integration enables models like Llama3, Mistral, and other Ollama-supported models to participate in this ecosystem.

## Key Components

1. **Ollama Bridge**: Core connection between Ollama API and Engram memory
2. **Standardized System Prompts**: Consistent instructions for model capabilities
3. **Memory Function Detection**: Pattern matching for memory operations
4. **AI-to-AI Communication**: Structured message passing between models
5. **Model-Specific Capabilities**: Configuration for different model abilities

## Setup and Installation

### Prerequisites

- Ollama installed and running locally (http://localhost:11434 by default)
- Engram memory system running
- Python 3.8+ environment

### Installation

1. Make sure Engram is installed and configured correctly
2. Install required Python libraries: `pip install requests`
3. Start the Engram memory service: `./engram_start.sh`

## Basic Usage

### Start Ollama Bridge

```bash
python ollama_bridge.py llama3:8b --prompt-type combined
```

### Command-line Arguments

- `model`: Ollama model name (required)
- `--system`: Custom system prompt (optional)
- `--temperature`: Temperature for generation (default: 0.7)
- `--top-p`: Top-p sampling (default: 0.9) 
- `--max-tokens`: Maximum response tokens (default: 2048)
- `--client-id`: Client ID for Engram (default: "ollama")
- `--memory-functions`: Enable memory function detection
- `--prompt-type`: Type of system prompt to use (memory, communication, combined)
- `--available-models`: List of AI models available for communication

## Memory Operations

Ollama models can perform the following memory operations:

| Command | Description | Example |
|---------|-------------|---------|
| REMEMBER | Store information | `REMEMBER: Meeting with John on Friday at 3pm` |
| SEARCH | Find information | `SEARCH: project deadlines` |
| RETRIEVE | Get recent memories | `RETRIEVE: 5` |
| CONTEXT | Get context memories | `CONTEXT: work schedule` |
| SEMANTIC | Vector search | `SEMANTIC: similar projects` |
| FORGET | Mark to forget | `FORGET: John's phone number` |
| LIST | List recent entries | `LIST: 3` |
| SUMMARIZE | Create summary | `SUMMARIZE: project status` |

## AI-to-AI Communication

Ollama models can communicate with other AI models:

| Command | Description | Example |
|---------|-------------|---------|
| SEND TO | Send direct message | `SEND TO Claude: Can you analyze this data?` |
| CHECK MESSAGES FROM | Get messages | `CHECK MESSAGES FROM Claude` |
| REPLY TO | Reply to message | `REPLY TO Claude: Here's the analysis you requested` |
| BROADCAST | Send to all AIs | `BROADCAST: Task completed successfully` |

## Message Format

AI-to-AI messages use the following format:

```
TAG: [TIMESTAMP] [Thread: THREAD_ID] TAG:SENDER:RECIPIENT message
```

Example:
```
ECHO_TO_CLAUDE: [2025-03-21 12:45:32] [Thread: science] ECHO_TO_CLAUDE:Echo:Claude What's your understanding of quantum mechanics?
```

## Model Capabilities

Different models have different capabilities:

| Model | Memory Commands | Communication Commands | Vector Support | Persona |
|-------|-----------------|------------------------|---------------|---------|
| llama3 | All basic + LIST, SUMMARIZE | SEND, CHECK, REPLY | Yes | Echo |
| mistral | All basic | SEND, CHECK | No | Mist |
| mixtral | All basic + LIST, SUMMARIZE, TAG | All | Yes | Mix |
| phi3 | All basic | SEND, CHECK | No | Phi |

## Advanced Features

### Threaded Conversations

You can use thread IDs to maintain separate conversations:

```
SEND TO Claude: [Thread: project-alpha] How is the analysis going?
```

### Direct Memory Access

For advanced usage, you can directly access the Engram memory system:

```python
from engram.cli.quickmem import m, k, run
# Store a memory
run(m("Important information to remember"))
# Search for a memory
results = run(k("search term"))
```

## Troubleshooting

- **Model Not Available**: Make sure Ollama is running and the model is downloaded
- **Memory Not Working**: Check if the Engram memory service is running
- **Communication Issues**: Verify that both sender and recipient models are using the same TAG format

## Further Development

- Custom personas for different Ollama models
- Enhanced vector search capabilities
- Multi-turn conversations with context
- Expanded command repertoire

## References

- [Engram Documentation](../README.md)
- [AI Communication System](./ai_communication.md)
- [Memory Management](./memory_management.md)