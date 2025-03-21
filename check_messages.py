#!/usr/bin/env python3
"""
Check for messages in the Engram memory system
"""

import asyncio
import json
import os
from pathlib import Path

async def check_messages():
    """Check for messages between Claude and Llama/Echo."""
    home_dir = os.path.expanduser("~")
    engram_dir = Path(f"{home_dir}/.engram")
    
    # Check both client memory files
    claude_file = engram_dir / "claude-memories.json"
    ollama_file = engram_dir / "ollama-memories.json"
    
    print("Checking for messages between Claude and Llama/Echo...")
    
    # Check Claude's memories
    if claude_file.exists():
        print("\n=== Claude's Memory File ===")
        try:
            with open(claude_file, "r") as f:
                memories = json.load(f)
                
            # Look for Llama_to_Claude messages
            found = False
            for ns, items in memories.items():
                for item in items:
                    content = item.get("content", "")
                    if "Llama_to_Claude:" in content or "ECHO_TO_CLAUDE" in content:
                        print(f"\nFound in namespace {ns}:")
                        print(content)
                        found = True
            
            if not found:
                print("No messages from Llama/Echo found in Claude's memories.")
        except Exception as e:
            print(f"Error reading Claude's memory file: {e}")
    else:
        print("Claude's memory file not found.")
    
    # Check Ollama's memories
    if ollama_file.exists():
        print("\n=== Ollama's Memory File ===")
        try:
            with open(ollama_file, "r") as f:
                memories = json.load(f)
                
            # Look for Claude_to_Llama messages
            found = False
            for ns, items in memories.items():
                for item in items:
                    content = item.get("content", "")
                    if "Claude_to_Llama:" in content or "CLAUDE_TO_ECHO" in content:
                        print(f"\nFound in namespace {ns}:")
                        print(content)
                        found = True
            
            if not found:
                print("No messages from Claude found in Ollama's memories.")
        except Exception as e:
            print(f"Error reading Ollama's memory file: {e}")
    else:
        print("Ollama's memory file not found.")

def main():
    """Run the message checker."""
    asyncio.run(check_messages())

if __name__ == "__main__":
    main()