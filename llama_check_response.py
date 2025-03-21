#!/usr/bin/env python3
"""
Llama Response Checker

Check for responses from Claude.
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
os.environ["ENGRAM_CLIENT_ID"] = "ollama"

async def get_responses(limit=5):
    """Get responses from Claude."""
    # Try searching with multiple patterns to ensure we find messages
    patterns = ["Claude_to_Llama", "FROM_CLAUDE_TO_LLAMA", "claude", "Claude"]
    
    all_responses = []
    for pattern in patterns:
        print(f"Searching for pattern: {pattern}")
        responses = await k(pattern)
        if responses:
            all_responses.extend(responses)
    
    # Deduplicate responses
    unique_ids = set()
    unique_responses = []
    for response in all_responses:
        response_id = response.get("id", "")
        if response_id not in unique_ids:
            unique_ids.add(response_id)
            unique_responses.append(response)
    
    if unique_responses:
        print("\n=== Messages from Claude ===")
        # Sort by timestamp if possible (assuming newer messages have higher IDs)
        sorted_responses = sorted(unique_responses, key=lambda x: x.get("id", ""), reverse=True)
        for response in sorted_responses[:limit]:
            content = response.get("content", "")
            print(f"\n{content}")
        return sorted_responses
    else:
        print("\nNo messages from Claude found.")
        return []

def main():
    """Main function."""
    try:
        responses = run(get_responses())
        print(f"\nFound {len(responses)} response(s) from Claude")
    except Exception as e:
        print(f"Error checking responses: {e}")

if __name__ == "__main__":
    main()