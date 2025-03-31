# Ollama Bridge Refactored Structure

This directory contains the refactored Ollama Bridge components for Engram. The original monolithic `ollama_bridge.py` has been split into multiple modules for better maintainability and readability.

## Directory Structure

- `api/`: Ollama API interaction functionality
  - `client.py`: Core API client for Ollama
  - `models.py`: Model management and capabilities

- `memory/`: Memory integration functionality
  - `handler.py`: Core memory handler for storing and retrieving memories
  - `operations.py`: Functions for processing memory operations in model outputs

- `communication/`: AI-to-AI communication functionality
  - `messenger.py`: Sending and receiving messages between AI models
  - `dialog.py`: Dialog mode functionality

- `cli/`: Command-line interface components
  - `args.py`: Command line argument parsing
  - `commands.py`: Special command handling

- `utils/`: Utility functions and helpers
  - `helpers.py`: Common helper functions
  - `pattern_matching.py`: Pattern matching for detecting operations

## Usage

The original `ollama_bridge.py` file is maintained as a compatibility layer that imports from this refactored structure, ensuring backwards compatibility while providing a more modular codebase.