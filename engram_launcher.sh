#!/bin/bash
# Engram Launcher
# Simple launcher to start Claude with Engram memory services from any directory

# ANSI color codes for terminal output
BLUE="\033[94m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

# Define paths
ENGRAM_DIR="$HOME/projects/github/Engram"
ENGRAM_WITH_CLAUDE="$ENGRAM_DIR/engram_with_claude"
INSTALL_SCRIPT="$ENGRAM_DIR/install.sh"

# Print header
echo -e "${BOLD}${BLUE}===== Engram with Claude Launcher =====${RESET}"

# Navigate to Engram directory to ensure proper path context
echo -e "${YELLOW}Navigating to Engram directory...${RESET}"
cd "$ENGRAM_DIR" || { echo -e "${RED}Failed to navigate to Engram directory!${RESET}"; exit 1; }

# Check if we need to install dependencies
if ! python3 -c "import requests" > /dev/null 2>&1; then
    echo -e "${YELLOW}${BOLD}Required Python dependencies missing${RESET}"
    echo -e "${BLUE}Running install script to set up dependencies...${RESET}"
    
    if [ -x "$INSTALL_SCRIPT" ]; then
        "$INSTALL_SCRIPT"
    else
        echo -e "${RED}Install script not found or not executable${RESET}"
        echo -e "${YELLOW}Installing minimal dependencies with pip...${RESET}"
        pip install requests urllib3 pydantic fastapi python-dotenv
    fi
fi

# Execute the engram_with_claude script
echo -e "${BLUE}Starting Claude with Engram Memory Services...${RESET}"
./engram_with_claude "$@"

# Return to original directory when Claude exits
# cd - > /dev/null