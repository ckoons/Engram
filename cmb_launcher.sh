#!/bin/bash
# Claude Memory Bridge Launcher
# Simple launcher to start Claude with memory services from any directory

# Define paths
CMB_DIR="$HOME/projects/github/ClaudeMemoryBridge"
CLAUDE_WITH_MEM="$CMB_DIR/claude_with_memory"

# Print header
echo -e "\033[1m\033[94m===== Claude Memory Bridge Launcher =====\033[0m"

# Navigate to CMB directory to ensure proper path context
echo -e "\033[93mNavigating to CMB directory...\033[0m"
cd "$CMB_DIR" || { echo -e "\033[91mFailed to navigate to CMB directory!\033[0m"; exit 1; }

# Execute the claude_with_memory script with consolidated server
echo -e "\033[94mStarting Claude with Memory (Consolidated Server)...\033[0m"
./claude_with_memory "$@"

# Return to original directory when Claude exits
# cd - > /dev/null