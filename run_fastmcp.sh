#!/bin/bash

# Run Engram FastMCP Server
# This script launches the Engram FastMCP server

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Environment variables
export ENGRAM_CLIENT_ID=${ENGRAM_CLIENT_ID:-"claude"}
export ENGRAM_DATA_DIR=${ENGRAM_DATA_DIR:-"${SCRIPT_DIR}/data"}
export ENGRAM_PORT=${ENGRAM_PORT:-8001}
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "====================================="
echo "   Engram FastMCP Server"
echo "====================================="
echo "Client ID: $ENGRAM_CLIENT_ID"
echo "Data Directory: $ENGRAM_DATA_DIR"
echo "Port: $ENGRAM_PORT"
echo "====================================="

# Create data directory if it doesn't exist
mkdir -p "$ENGRAM_DATA_DIR"

# Launch FastMCP server
python -m engram.api.fastmcp_server --client-id "$ENGRAM_CLIENT_ID" --data-dir "$ENGRAM_DATA_DIR" --port "$ENGRAM_PORT"