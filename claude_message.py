#!/usr/bin/env python3
"""
Claude Message Sender

Send a message from Claude to Llama using command line arguments.
"""

import os
import sys
import asyncio
from datetime import datetime

# Import Engram memory functions
try:
    from engram.cli.quickmem import m, k, run
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

# Set client ID
os.environ["ENGRAM_CLIENT_ID"] = "claude"

async def send_message(message):
    """Send a message to Llama."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memory_text = f"Claude_to_Llama: [{timestamp}] {message}"
    result = await m(memory_text)
    print(f"Message sent at {timestamp}")
    return result

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python claude_message.py \"Your message to Llama\"")
        return
    
    message = sys.argv[1]
    print(f"Sending message to Llama: {message}")
    
    try:
        run(send_message(message))
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    main()