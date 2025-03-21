#!/bin/bash
# Engram Launcher
# Launcher to start Claude or Ollama with Engram memory services from any directory
# Updated: March 21, 2025 - Added Ollama support

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
ENGRAM_WITH_OLLAMA="$ENGRAM_DIR/engram_with_ollama"
INSTALL_SCRIPT="$ENGRAM_DIR/install.sh"

# Default model is Claude
MODEL="claude"
MODEL_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --ollama)
      MODEL="ollama"
      shift
      ;;
    --claude)
      MODEL="claude"
      shift
      ;;
    --help)
      echo "Usage: engram_launcher [OPTIONS] [MODEL_NAME]"
      echo ""
      echo "Options:"
      echo "  --ollama         Use Ollama instead of Claude"
      echo "  --claude         Use Claude (default)"
      echo "  --help           Show this help message"
      echo ""
      echo "Examples:"
      echo "  engram_launcher                    # Start with Claude"
      echo "  engram_launcher --ollama           # Start with Ollama (default model)"
      echo "  engram_launcher --ollama llama3:70b # Start with Ollama using llama3:70b model"
      exit 0
      ;;
    *)
      # Treat any other argument as the model name
      MODEL_NAME="$1"
      shift
      ;;
  esac
done

# Print header
echo -e "${BOLD}${BLUE}===== Engram with $MODEL Launcher =====${RESET}"

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

# Execute the appropriate script based on the model
if [ "$MODEL" = "ollama" ]; then
    if [ ! -x "$ENGRAM_WITH_OLLAMA" ]; then
        echo -e "${RED}Ollama launch script not found or not executable: $ENGRAM_WITH_OLLAMA${RESET}"
        exit 1
    fi
    echo -e "${BLUE}Starting Ollama with Engram Memory Services...${RESET}"
    if [ -n "$MODEL_NAME" ]; then
        ./engram_with_ollama "$MODEL_NAME"
    else
        ./engram_with_ollama
    fi
else
    if [ ! -x "$ENGRAM_WITH_CLAUDE" ]; then
        echo -e "${RED}Claude launch script not found or not executable: $ENGRAM_WITH_CLAUDE${RESET}"
        exit 1
    fi
    echo -e "${BLUE}Starting Claude with Engram Memory Services...${RESET}"
    ./engram_with_claude "$MODEL_NAME"
fi

# Return to original directory when the AI exits
# cd - > /dev/null