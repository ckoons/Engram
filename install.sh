#!/bin/bash
# Engram Installation Script
# This script installs Engram and its dependencies

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BIN_DIR="$HOME/bin"

# Create bin directory if it doesn't exist
if [ ! -d "$BIN_DIR" ]; then
    echo "Creating $BIN_DIR directory..."
    mkdir -p "$BIN_DIR"
    
    # Check if $BIN_DIR is in PATH, if not, add it
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "Adding $BIN_DIR to PATH in your shell profile..."
        
        # Determine shell profile
        if [ -f "$HOME/.zshrc" ]; then
            PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            PROFILE="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            PROFILE="$HOME/.bash_profile"
        else
            PROFILE="$HOME/.profile"
        fi
        
        # Add to profile
        echo 'export PATH="$HOME/bin:$PATH"' >> "$PROFILE"
        echo "Added $BIN_DIR to PATH in $PROFILE"
        echo "You'll need to restart your terminal or run 'source $PROFILE' for this to take effect"
    fi
fi

# Create symbolic link for engram launcher
echo "Creating symbolic link for 'engram' command..."
ln -sf "$SCRIPT_DIR/engram_launcher.sh" "$BIN_DIR/engram"
chmod +x "$BIN_DIR/engram"

# Install Python dependencies if pip is available
if command -v pip &> /dev/null; then
    echo "Installing Python dependencies..."
    
    # Try to install in the user's virtual environment if it exists
    if [ -d "$SCRIPT_DIR/venv" ]; then
        echo "Found virtual environment, installing dependencies there..."
        source "$SCRIPT_DIR/venv/bin/activate"
        pip install -r "$SCRIPT_DIR/requirements.txt"
        pip install requests urllib3 pydantic==2.10.6 fastapi python-dotenv
        deactivate
    else
        echo "Installing dependencies globally..."
        pip install -r "$SCRIPT_DIR/requirements.txt"
        pip install requests urllib3 pydantic==2.10.6 fastapi python-dotenv
    fi
fi

# Make sure scripts are executable
chmod +x "$SCRIPT_DIR/engram_launcher.sh"
chmod +x "$SCRIPT_DIR/engram_with_claude"
chmod +x "$SCRIPT_DIR/engram_check.py"
chmod +x "$SCRIPT_DIR/engram_consolidated"

echo ""
echo "Engram installed successfully!"
echo ""
echo "Usage:"
echo "  engram                     # Start Claude with Engram memory service"
echo ""
echo "In Claude Code sessions:"
echo "  from cmb.cli.quickmem import m, t, r, w, l, c, k, f, i, x, s, a, p, v"
echo ""