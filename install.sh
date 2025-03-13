#!/bin/bash
# Claude Memory Bridge Installation Script
# This script installs the CMB to be accessible from anywhere

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

# Create symbolic link for cmb
echo "Creating symbolic link for 'cmb' command..."
ln -sf "$SCRIPT_DIR/cmb" "$BIN_DIR/cmb"
chmod +x "$BIN_DIR/cmb"

# Create symbolic link for claude_helper.py to make it importable
echo "Creating symbolic link for claude_helper.py..."
ln -sf "$SCRIPT_DIR/cmb/cli/claude_helper.py" "$BIN_DIR/claude_helper.py"
chmod +x "$BIN_DIR/claude_helper.py"

# Install Python dependencies if pip is available
if command -v pip &> /dev/null; then
    echo "Installing Python dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

echo ""
echo "Claude Memory Bridge installed successfully!"
echo ""
echo "Usage:"
echo "  cmb                         # Start CMB with default settings"
echo "  cmb --client-id my-client   # Start with a specific client ID"
echo "  cmb --help                  # Show help and options"
echo ""
echo "In Claude Code sessions:"
echo "  from claude_helper import query_memory, store_memory, store_thinking, store_longterm"
echo ""