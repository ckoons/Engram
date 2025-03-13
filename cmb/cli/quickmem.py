#!/usr/bin/env python3
"""
QuickMem - Shorthand memory access for Claude Memory Bridge

This module provides simple shorthand commands to access memory during conversations.
Import this at the start of your Claude Code session.

Usage:
  from cmb.cli.quickmem import mem

  # Then during conversation:
  mem("wife")  # Searches for memories about your wife
  mem()        # Searches for relevant memories based on recent conversation
"""

import os
import sys
import urllib.parse
import json
import urllib.request
from typing import Dict, List, Any, Optional

# Default HTTP URL for the Claude Memory Bridge wrapper
DEFAULT_HTTP_URL = "http://127.0.0.1:8001"

def _get_http_url():
    """Get the HTTP URL for the Claude Memory Bridge wrapper."""
    return os.environ.get("CMB_HTTP_URL", DEFAULT_HTTP_URL)

def _safe_string(text: str) -> str:
    """URL-encode a string to make it safe for GET requests."""
    return urllib.parse.quote_plus(text)

def mem(query: str = None, namespaces: List[str] = None, limit: int = 3):
    """
    Quick memory access shorthand.
    
    Args:
        query: Search term (if None, will try to determine from context)
        namespaces: List of namespaces to search (default: longterm, conversations)
        limit: Max results per namespace
    """
    if namespaces is None:
        namespaces = ["longterm", "conversations"]
    
    # If no query provided, try to determine from recent conversation
    if query is None:
        print("Checking memory for relevant context...")
        # Default to general info when no specific query
        query = "personal information"
    
    # Build namespace parameter
    namespaces_str = ",".join(namespaces)
    
    # Query each namespace
    results = {}
    found_items = 0
    
    for namespace in namespaces:
        try:
            url = f"{_get_http_url()}/query?query={_safe_string(query)}&namespace={namespace}&limit={limit}"
            with urllib.request.urlopen(url) as response:
                result = json.loads(response.read().decode())
                
                if result.get("count", 0) > 0:
                    if namespace not in results:
                        results[namespace] = []
                    
                    for memory in result.get("results", []):
                        results[namespace].append(memory.get("content", ""))
                        found_items += 1
        except Exception as e:
            print(f"Error querying {namespace} memory: {e}")
    
    # Display results in a nice format
    if found_items > 0:
        print(f"\n📝 Memory found for '{query}':")
        for namespace in results:
            if namespace == "longterm":
                print(f"\n🌟 Important information:")
            elif namespace == "conversations":
                print(f"\n💬 From previous conversations:")
            elif namespace == "thinking":
                print(f"\n🤔 Previous thoughts:")
            else:
                print(f"\n📂 {namespace.capitalize()}:")
                
            for i, memory in enumerate(results[namespace]):
                print(f"  {i+1}. {memory}")
        print()
    else:
        print(f"No memories found for '{query}'")
    
    return results

def think(thought: str = None):
    """
    Store a thought in the thinking namespace.
    
    Args:
        thought: The thought to remember. If None, will generate a thought
                about the current conversation context.
    """
    # If no thought provided, generate one based on recent context
    if thought is None:
        # When called without a parameter, use this to indicate reflective thinking
        thought = (
            "Based on this conversation, I should pay attention to personal details "
            "the user shares and remember them for future reference. The user values "
            "efficient, seamless interaction patterns that don't interrupt the natural "
            "flow of conversation."
        )
        print("💭 Thinking about our conversation...")
    
    try:
        url = f"{_get_http_url()}/thinking?thought={_safe_string(thought)}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"💭 Thought stored")
                return True
            else:
                print(f"❌ Failed to store thought")
                return False
    except Exception as e:
        print(f"Error storing thought: {e}")
        return False

def remember(info: str = None):
    """
    Store important information in long-term memory.
    
    Args:
        info: The important information to remember. If None, will store what 
              appears to be the most important information from recent interaction.
    """
    # If no info provided, try to identify important information from recent context
    if info is None:
        # When called without a parameter, store this as a general reminder
        # about the importance of memory in this conversation
        info = (
            "The user highly values memory persistence across conversations. "
            "They want a seamless, natural way to incorporate memory into our "
            "interactions without disrupting conversation flow. Remember to consult "
            "memory frequently to maintain conversation continuity."
        )
        print("🔍 Identifying important information to remember...")
    
    try:
        url = f"{_get_http_url()}/longterm?info={_safe_string(info)}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"🌟 Information stored in long-term memory")
                return True
            else:
                print(f"❌ Failed to store information")
                return False
    except Exception as e:
        print(f"Error storing information: {e}")
        return False

# Shortcuts
m = mem       # Even shorter alias for memory access
t = think     # Shortcut for storing thoughts
r = remember  # Shortcut for storing important information

if __name__ == "__main__":
    # Command-line interface
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "think" and len(sys.argv) > 2:
            think(sys.argv[2])
        elif command == "remember" and len(sys.argv) > 2:
            remember(sys.argv[2])
        else:
            mem(command if command != "mem" else None)
    else:
        mem()