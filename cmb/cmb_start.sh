#!/bin/bash
# Claude Memory Bridge Startup Script
# This script starts the memory bridge service from any directory

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Default values
CLIENT_ID="claude"
PORT=8000
HOST="127.0.0.1"
DATA_DIR="$HOME/.cmb"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --client-id)
      CLIENT_ID="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --data-dir)
      DATA_DIR="$2"
      shift 2
      ;;
    --help)
      echo "Claude Memory Bridge"
      echo "Usage: cmb_start.sh [options]"
      echo ""
      echo "Options:"
      echo "  --client-id <id>   Client ID for memory service (default: claude)"
      echo "  --port <port>      Port to run the server on (default: 8000)"
      echo "  --host <host>      Host to bind the server to (default: 127.0.0.1)"
      echo "  --data-dir <dir>   Directory to store memory data (default: ~/.cmb)"
      echo "  --help             Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage information"
      exit 1
      ;;
  esac
done

# Change to the script directory
cd "$SCRIPT_DIR"

# Check for virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found in $SCRIPT_DIR/venv"
    echo "Using system Python environment"
fi

# Make sure the data directory exists
mkdir -p "$DATA_DIR"

echo "Starting Claude Memory Bridge..."
echo "Client ID: $CLIENT_ID"
echo "Server: $HOST:$PORT"
echo "Data directory: $DATA_DIR"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python -m cmb.api.server --client-id "$CLIENT_ID" --port "$PORT" --host "$HOST" --data-dir "$DATA_DIR"