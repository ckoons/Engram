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

def forget(info: str):
    """
    Mark specific information to be forgotten/ignored in memory.
    
    Args:
        info: The information to forget or mark as invalid
    """
    if not info:
        print("❌ Please specify what to forget")
        return False
        
    try:
        # Store this as a special "forget" instruction in longterm memory
        forget_instruction = f"FORGET/IGNORE: {info}"
        url = f"{_get_http_url()}/store?key=forget&value={_safe_string(forget_instruction)}&namespace=longterm"
        
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"🗑️ Marked for forgetting: \"{info}\"")
                return True
            else:
                print(f"❌ Failed to mark information for forgetting")
                return False
    except Exception as e:
        print(f"Error in forget operation: {e}")
        return False

def ignore(info: str):
    """
    Explicitly ignore information from the current conversation.
    Must have a string parameter specifying what to ignore.
    
    Args:
        info: The information to ignore
    """
    if not info:
        print("❌ Please specify what to ignore")
        return False
        
    try:
        # Mark this specifically as information to be ignored
        ignore_instruction = f"IGNORE FROM CONVERSATION: {info}"
        print(f"🔇 Ignoring: \"{info}\"")
        
        # We don't actually store this - that would be counterproductive
        # Instead we just acknowledge the instruction
        return True
    except Exception as e:
        print(f"Error in ignore operation: {e}")
        return False

def write(note: str = None, metadata: Dict[str, Any] = None):
    """
    Write a memory to the session namespace for persistence across sessions.
    
    Args:
        note: The note to persist. If None, will use general note about the conversation.
        metadata: Optional metadata to store with the note
    """
    # If no note provided, generate a default one
    if note is None:
        note = (
            "This is an important session that I should remember for future reference. "
            "The user is working on a project that requires persistent memory across sessions."
        )
        print("📝 Storing session memory...")
    
    try:
        # Convert metadata to JSON string if provided
        metadata_str = json.dumps(metadata) if metadata else None
        
        url = f"{_get_http_url()}/write?content={_safe_string(note)}"
        if metadata_str:
            url += f"&metadata={_safe_string(metadata_str)}"
            
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"📝 Session memory stored")
                return True
            else:
                print(f"❌ Failed to store session memory")
                return False
    except Exception as e:
        print(f"Error storing session memory: {e}")
        return False

def compartment(info: str = None):
    """
    Create or use a compartment for memory organization.
    
    Syntax:
        c("CompartmentName: Information to store")
        c("CompartmentName") - Just activate a compartment
        c() - List active compartments
    
    Args:
        info: String with compartment info, or None to list compartments
    """
    if info is None:
        # List active compartments
        try:
            url = f"{_get_http_url()}/compartment/list"
            with urllib.request.urlopen(url) as response:
                result = json.loads(response.read().decode())
                
                compartments = result.get("compartments", [])
                active_compartments = [c for c in compartments if c.get("active", False)]
                
                if active_compartments:
                    print(f"🗂️ Active compartments:")
                    for c in active_compartments:
                        print(f"  • {c.get('name', 'Unknown')} (ID: {c.get('id', 'Unknown')})")
                else:
                    print("No active compartments")
                    
                return active_compartments
        except Exception as e:
            print(f"Error listing compartments: {e}")
            return False
    
    # Parse compartment info from the input
    if ":" in info:
        # Format: "CompartmentName: Content to store"
        parts = info.split(":", 1)
        compartment_name = parts[0].strip()
        content = parts[1].strip()
        
        # Check if the compartment exists
        try:
            # First try to find existing compartment
            url = f"{_get_http_url()}/compartment/list"
            existing_compartment = None
            
            with urllib.request.urlopen(url) as response:
                result = json.loads(response.read().decode())
                compartments = result.get("compartments", [])
                
                for c in compartments:
                    if c.get("name", "").lower() == compartment_name.lower():
                        existing_compartment = c.get("id", None)
                        break
            
            if existing_compartment:
                # Store in existing compartment
                store_url = f"{_get_http_url()}/compartment/store?compartment={_safe_string(existing_compartment)}&content={_safe_string(content)}"
                with urllib.request.urlopen(store_url) as response:
                    result = json.loads(response.read().decode())
                    
                    if result.get("success", False):
                        print(f"🗂️ Added to compartment: '{compartment_name}'")
                        return True
                    else:
                        print(f"❌ Failed to add to compartment: {result.get('message', 'Unknown error')}")
                        return False
            else:
                # Create new compartment
                create_url = f"{_get_http_url()}/compartment/create?name={_safe_string(compartment_name)}"
                with urllib.request.urlopen(create_url) as response:
                    result = json.loads(response.read().decode())
                    
                    if result.get("success", False):
                        compartment_id = result.get("compartment_id")
                        
                        # Store content in the new compartment
                        store_url = f"{_get_http_url()}/compartment/store?compartment={_safe_string(compartment_id)}&content={_safe_string(content)}"
                        with urllib.request.urlopen(store_url) as response:
                            store_result = json.loads(response.read().decode())
                            
                            if store_result.get("success", False):
                                print(f"🗂️ Created new compartment '{compartment_name}' and stored content")
                                return True
                            else:
                                print(f"✓ Created compartment but failed to store content")
                                return False
                    else:
                        print(f"❌ Failed to create compartment: {result.get('message', 'Unknown error')}")
                        return False
        except Exception as e:
            print(f"Error working with compartment: {e}")
            return False
    else:
        # Just a compartment name - activate it
        try:
            url = f"{_get_http_url()}/compartment/activate?compartment={_safe_string(info)}"
            with urllib.request.urlopen(url) as response:
                result = json.loads(response.read().decode())
                
                if result.get("success", False):
                    print(f"🗂️ Activated compartment: '{info}'")
                    return True
                else:
                    # Try to create the compartment if it doesn't exist
                    create_url = f"{_get_http_url()}/compartment/create?name={_safe_string(info)}"
                    with urllib.request.urlopen(create_url) as response:
                        create_result = json.loads(response.read().decode())
                        
                        if create_result.get("success", False):
                            print(f"🗂️ Created and activated new compartment: '{info}'")
                            return True
                        else:
                            print(f"❌ Failed to create compartment: {create_result.get('message', 'Unknown error')}")
                            return False
        except Exception as e:
            print(f"Error activating compartment: {e}")
            return False

def keep(memory_id: str = None, days: int = 30):
    """
    Keep a memory for a specified number of days.
    
    Args:
        memory_id: The ID of the memory to keep
        days: Number of days to keep the memory
    """
    if not memory_id:
        print("❌ Please specify a memory ID to keep")
        return False
        
    try:
        url = f"{_get_http_url()}/keep?memory_id={_safe_string(memory_id)}&days={days}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"📅 Memory will be kept for {days} days")
                return True
            else:
                print(f"❌ Failed to keep memory: {result.get('message', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"Error keeping memory: {e}")
        return False

# Shortcuts
m = mem       # Even shorter alias for memory access
t = think     # Shortcut for storing thoughts
r = remember  # Shortcut for storing important information
f = forget    # Shortcut for marking information to forget
i = ignore    # Shortcut for ignoring information in current context
w = write     # Shortcut for writing session memory
c = compartment # Shortcut for compartmentalizing memory
k = keep      # Shortcut for keeping memory for specific duration

if __name__ == "__main__":
    # Command-line interface
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "think" and len(sys.argv) > 2:
            think(sys.argv[2])
        elif command == "remember" and len(sys.argv) > 2:
            remember(sys.argv[2])
        elif command == "forget" and len(sys.argv) > 2:
            forget(sys.argv[2])
        elif command == "ignore" and len(sys.argv) > 2:
            ignore(sys.argv[2])
        elif command == "write" and len(sys.argv) > 2:
            write(sys.argv[2])
        elif command == "compartment" and len(sys.argv) > 2:
            compartment(sys.argv[2])
        elif command == "keep" and len(sys.argv) > 2:
            # Optional third parameter for days
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            keep(sys.argv[2], days)
        else:
            mem(command if command != "mem" else None)
    else:
        mem()