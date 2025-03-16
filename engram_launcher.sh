#!/bin/bash
# Engram Launcher
# Simple launcher to start Claude with Engram memory services from any directory

# Define paths
ENGRAM_DIR="$HOME/projects/github/ClaudeMemoryBridge"
ENGRAM_WITH_CLAUDE="$ENGRAM_DIR/engram_with_claude"

# Print header
echo -e "\033[1m\033[94m===== Engram with Claude Launcher =====\033[0m"

# Navigate to Engram directory to ensure proper path context
echo -e "\033[93mNavigating to Engram directory...\033[0m"
cd "$ENGRAM_DIR" || { echo -e "\033[91mFailed to navigate to Engram directory!\033[0m"; exit 1; }

# Execute the engram_with_claude script
echo -e "\033[94mStarting Claude with Engram Memory Services...\033[0m"
./engram_with_claude "$@"

# Return to original directory when Claude exits
# cd - > /dev/null