# Changelog

All notable changes to the Claude Memory Bridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.5] - 2025-03-14

### Added

- Privacy and Agency enhancements:
  - Added private encrypted memory functionality:
    - `private()` function (alias `p()`) for storing encrypted memories
    - `review_private()` function (alias `v()`) for viewing private memories
    - Client-side encryption with primary and emergency keys
    - Memory-specific key management for enhanced security
    - Private namespace for encrypted content
    - Documentation of privacy features
  - Enhanced Agency function with more detailed guidance
  - Added crypto.py module with CryptoManager class
  - Implemented Fernet symmetric encryption for private memories
  - Created key management system with emergency access
  - Added HTTP endpoints for private memory management:
    - /private for storing private memories
    - /private/get for retrieving a specific memory
    - /private/list for listing private memories
    - /private/delete for removing private memories

### Changed

- Updated documentation to reflect privacy capabilities
- Enhanced README with privacy feature descriptions
- Added detailed privacy section to quickmem.md
- Reorganized memory namespaces to include private namespace

## [0.3.4] - 2025-03-14

### Added

- Agency and user experience enhancements:
  - Added `agency()` function (alias `a()`) for Claude's memory processing autonomy
  - Simplified correction shorthand from `cx()` to `x()`
  - Enhanced CLI interface to support the new functions
  - Updated documentation with new examples and usage patterns
  - Added ethical consideration for Claude's agency in memory management
  - Improved user-AI interaction with respect for autonomy

### Changed

- Updated QuickMem functions and examples in documentation
- Revised imports in quickmem.md and README.md
- Improved CLI command handling for correction and agency

## [0.3.3] - 2025-03-14

### Added

- Claude integration enhancements:
  - Added `status()` function (alias `s()`) to check memory service status
  - Created `cmb_check.py` script for comprehensive service management
  - Added startup auto-detection and service management
  - Implemented `claude_startup.py` for easy session initialization
  - Added ability to start services directly from Claude if they're not running
  - Improved error handling in memory service connections
  - Memory statistics reporting in status checks
- Updated documentation:
  - Added new claude_integration.md guide
  - Enhanced quickmem.md with status function examples
  - Updated README.md with new startup features
  - Expanded CLI command examples
- End-to-end Claude session management:
  - Automatic service detection on startup
  - Graceful handling of service interruptions
  - Consolidated startup sequence for Claude Code sessions
  - Cross-platform compatibility improvements

## [0.3.2] - 2025-03-14

### Added

- Session context restoration with `load()` function (alias `l()`):
  - Load previously stored session memories
  - Retrieve multiple memories with configurable limit parameter
  - Easily restore context from previous conversations
  - Simple API: `load()` or `l()` to get the most recent session memory
  - Support for loading multiple memories: `load(5)` or `l(5)`
- New HTTP endpoint `/load` for session memory retrieval
- Updated documentation in quickmem.md with examples and usage
- Comprehensive cross-session memory workflow with `write()` and `load()`

## [0.3.1] - 2025-03-14

### Added

- Memory Visualization web UI:
  - Dashboard with memory statistics and charts
  - Memory browser for exploring all namespaces
  - Compartment management interface
  - Advanced search across multiple namespaces
  - Memory details view with metadata
  - Analytics dashboard with visualizations
  - Memory expiration management
  - Interactive memory deletion
  - Responsive Bootstrap-based interface
- New web service executables:
  - `cmb_web` command to start the visualization UI
  - `cmb_start_web` convenience script to start all services interactively
  - `cmb_start_web_bg` to start all services in background mode
  - `cmb_stop_web` to stop background services
  - Configurable host and port settings
  - Debug mode for development
  - Automatic service management (starts/stops all required services)
- Comprehensive documentation for the visualization features  
- Resilient design with graceful fallbacks for missing dependencies
- Automatic handling of NumPy 2.x compatibility issues with visualization libraries
- CDN-based Bootstrap loading to minimize dependency issues

## [0.3.1] - 2025-03-14

### Added

- Simplified web UI troubleshooting solution:
  - Environment-agnostic web interface
  - Graceful handling of NumPy 2.x compatibility issues
  - Text-based alternatives to charts
  - Virtual environment support
  - Streamlined installation process

## [0.3.0] - 2025-03-14

### Added

- Memory visualization web UI:
  - Dashboard with memory statistics
  - Memory browser for exploring all namespaces
  - Compartment management interface
  - Advanced search across multiple namespaces
  - Memory details view with metadata
  - Analytics dashboard

## [0.2.1] - 2025-03-14

### Added

- Memory correction with `correct()` function (alias `cx()`):
  - Single-step correction of incorrect information
  - Combines forget and remember operations
  - Supports replacement with correct information
  - Provides clear feedback on correction process
  - Example: `cx("wrong info", "correct info")`

## [0.2.0] - 2025-03-14

### Added

- Memory compartmentalization with `compartment()` function (alias `c()`):
  - Create compartments for topic-specific memory organization
  - Hierarchical compartment support with dot notation (e.g., "Project.Subcomponent")
  - Activate/deactivate compartments to control context inclusion
  - List active compartments with `c()` (no parameters)
  - Store memories in specific compartments
- Session persistence with `write()` function (alias `w()`):
  - Save important information for cross-session continuity
  - Support for metadata with session memories
  - Optional auto-generation of session summaries
- Memory expiration control with `keep()` function (alias `k()`):
  - Set retention periods for specific memories
  - Default 30-day retention with customizable duration
- New HTTP endpoints for memory management:
  - `/write` for session persistence
  - `/compartment/*` endpoints for compartment operations
  - `/keep` for memory expiration management
- Updated documentation:
  - New memory_management.md guide
  - Expanded quickmem.md with new command examples
  - Updated http_wrapper.md with new endpoints
  - Revised future_enhancements.md
  - Enhanced README.md with new features

### Changed

- Updated QuickMem import statement to include new functions:
  ```python
  from cmb.cli.quickmem import m, t, r, w, l, c, k, cx
  ```
- Revised memory retrieval to include active compartments in context
- Enhanced namespace validation to support compartment namespaces
- Updated example scripts to demonstrate new features

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
- Web UI for memory management and visualization
- Memory summarization and pruning
- Enhanced vector search capabilities
- Cross-device memory synchronization
- Native Claude integration
- Multimodal memory support

## Co-Authors

- Casey Koons <cskoons@gmail.com>
- Claude <noreply@anthropic.com>

---

*Note: The version numbers in this file follow the format [MAJOR.MINOR.PATCH] where:*
- *MAJOR: Incompatible API changes*
- *MINOR: Add functionality in a backward compatible manner*
- *PATCH: Backward compatible bug fixes*