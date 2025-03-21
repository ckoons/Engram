#!/bin/bash
# Claude Communication Test
# A simplified script for testing Claude-to-Claude communication

# ANSI color codes for terminal output
BLUE="\033[94m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

# Check if memory service is running
echo -e "${BLUE}${BOLD}Checking memory service...${RESET}"
if ps aux | grep -q "engram.api.consolidated_server"; then
    echo -e "${GREEN}Memory service is already running.${RESET}"
else
    echo -e "${YELLOW}Starting memory service...${RESET}"
    ./engram_with_claude --memory-only
fi

# Function to launch Claude with a specific client ID
launch_claude() {
    local client_id=$1
    echo -e "${BLUE}${BOLD}Launching Claude with client ID: ${client_id}${RESET}"
    
    # Open a new terminal window with Claude
    osascript -e "tell application \"Terminal\" 
        do script \"cd $(pwd) && export ENGRAM_CLIENT_ID=${client_id} && export ENGRAM_DATA_DIR=$HOME/.engram && echo -e \\\"${GREEN}${BOLD}Claude Instance: ${client_id}${RESET}\\\" && python test_multi_claude.py\"
    end tell"
    
    echo -e "${GREEN}Claude instance ${client_id} launched successfully!${RESET}"
}

# Main menu
display_menu() {
    echo -e "\n${BLUE}${BOLD}=== Claude Communication Test ===${RESET}"
    echo -e "1. Launch Claude 1"
    echo -e "2. Launch Claude 2"
    echo -e "3. Launch Claude 3"
    echo -e "4. Launch Claude 4"
    echo -e "5. Launch all Claude instances"
    echo -e "6. Exit"
    
    read -p "Enter choice (1-6): " choice
    
    case $choice in
        1) launch_claude "claude1" ;;
        2) launch_claude "claude2" ;;
        3) launch_claude "claude3" ;;
        4) launch_claude "claude4" ;;
        5)
            launch_claude "claude1"
            sleep 1
            launch_claude "claude2"
            sleep 1
            launch_claude "claude3"
            sleep 1
            launch_claude "claude4"
            ;;
        6) 
            echo -e "${BLUE}Exiting...${RESET}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${RESET}"
            ;;
    esac
    
    # Return to menu
    sleep 1
    display_menu
}

# Display the banner
echo -e "${BLUE}${BOLD}=====================================${RESET}"
echo -e "${BLUE}${BOLD}     Claude Communication Test       ${RESET}"
echo -e "${BLUE}${BOLD}=====================================${RESET}"
echo -e "${YELLOW}This script launches multiple Claude instances${RESET}"
echo -e "${YELLOW}with different client IDs for testing Claude-to-Claude${RESET}"
echo -e "${YELLOW}communication capabilities.${RESET}"
echo

# Start the menu
display_menu