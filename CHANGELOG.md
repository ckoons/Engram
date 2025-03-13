# Changelog

All notable changes to the Claude Memory Bridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-03-13

### Added

- Initial release of Claude Memory Bridge
- Core memory service with namespace support:
  - `conversations`: General dialog and facts
  - `thinking`: Claude's internal thought processes
  - `longterm`: High-priority persistent memories
  - `projects`: Project-specific context
- Memory persistence across sessions via local storage
- Support for both mem0 vector storage and fallback JSON storage
- CLI commands for starting services:
  - `cmb_executable`: Main memory bridge
  - `cmb_http`: HTTP wrapper for tool-approval-free access
  - `cmb_start_all`: Start all services in background
- Helper libraries for Claude Code:
  - `claude_helper.py`: Standard memory helper
  - `http_helper.py`: Tool-approval-free helper
  - `quickmem.py`: Ultra-short memory commands
- Short memory command aliases:
  - `m()`: Memory lookup
  - `t()`: Store thoughts
  - `r()`: Remember important information
  - `f()`: Forget incorrect information
  - `i()`: Ignore current conversation content
- Memory filtering based on forget instructions
- Comprehensive documentation
- Example scripts demonstrating usage

### Future Plans

- Clipboard integration for easier imports
- Web UI for memory management
- Memory summarization and pruning
- Enhanced vector search capabilities
- Cross-device memory synchronization
- Native Claude integration

## Co-Authors

- Casey Koons <cskoons@gmail.com>
- Claude <noreply@anthropic.com>

---

*Note: The version numbers in this file follow the format [MAJOR.MINOR.PATCH] where:*
- *MAJOR: Incompatible API changes*
- *MINOR: Add functionality in a backward compatible manner*
- *PATCH: Backward compatible bug fixes*