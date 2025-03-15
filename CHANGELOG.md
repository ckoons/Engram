# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2025-03-15

### Added
- Structured Memory: Implemented a balanced memory system with:
  - File-based storage with categorized organization
  - Memory importance ranking (1-5 scale)
  - Enhanced retrieval mechanisms with context-aware loading
- Nexus Interface: Created a standardized interface for memory-enabled AI assistants
  - Context enrichment with relevant memories
  - Session management with memory digests
  - Automatic memory storage with categorization
  - Unified memory searching across systems
- Enhanced QuickMem module with new functions:
  - `memory_digest` - Get a formatted digest of important memories
  - `start_nexus` - Start a memory-enabled session with context
  - `process_message` - Process messages with memory enrichment
  - `auto_remember` - Store memories with automatic categorization
  - `end_nexus` - End a session with summary storage
- HTTP API endpoints for structured memory and Nexus functionality
- Comprehensive test suite for all new components

### Fixed
- Improved memory sorting by importance and timestamp
- Enhanced auto-categorization with prioritized patterns
- Fixed session end recording in memory systems

### Technical Details
- Implemented StructuredMemory class for file-based organization with JSON format
- Created NexusInterface as a bridge between memory systems and AI assistants
- Enhanced HTTP wrapper with endpoints for new functionality
- Added extensive tests for core components and API

## [0.3.0] - 2025-02-28

### Added
- Memory compartments for organizing related content
- Private memory storage with encryption
- Memory expiration settings
- Session memory for persistence across sessions
- Memory correction with forget/replace functionality

### Changed
- Improved memory retrieval with better relevance ranking
- Enhanced CLI with more intuitive commands
- Updated documentation with usage examples

## [0.2.0] - 2025-01-15

### Added
- Multiple memory namespaces (conversations, thinking, longterm)
- Basic HTTP wrapper for Claude access
- QuickMem module for quick memory operations
- Memory service with basic vector search

### Changed
- Refactored core memory storage for better performance
- Improved command-line interface

## [0.1.0] - 2024-12-10

### Added
- Initial release with basic memory storage
- Simple memory retrieval by keyword
- Command-line interface for memory operations