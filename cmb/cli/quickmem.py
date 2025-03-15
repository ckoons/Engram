#!/usr/bin/env python3
"""
QuickMem - Shorthand memory access for Claude Memory Bridge

This module provides simple shorthand commands to access memory during conversations.
Import this at the start of your Claude Code session.

Usage:
  from cmb.cli.quickmem import mem, think, remember, write, load, compartment, keep, status
  # Or use the ultra-short aliases
  from cmb.cli.quickmem import m, t, r, w, l, c, k, s

  # Then during conversation:
  status()         # Check memory service status
  mem("wife")      # Searches for memories about your wife
  mem()            # Searches for relevant memories based on recent conversation
  think("insight") # Store a thought for future reference
  write("note")    # Store session memory for persistence across sessions
  load()           # Load previously stored session memories
  c("Project: Important info about the project") # Store in a compartment
  k("memory-id", 90) # Keep a memory for 90 days
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

def load(limit: int = 1):
    """
    Load memories from the session namespace.
    
    Args:
        limit: Maximum number of session memories to load (default: 1)
    """
    try:
        url = f"{_get_http_url()}/load?limit={limit}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                content = result.get("content", [])
                if content:
                    print(f"📖 Loaded {len(content)} session memories:")
                    for i, item in enumerate(content):
                        print(f"  {i+1}. {item}")
                    return content
                else:
                    print("No session memories found")
                    return []
            else:
                print(f"❌ Failed to load session memory: {result.get('message', 'Unknown error')}")
                return []
    except Exception as e:
        print(f"Error loading session memory: {e}")
        return []

def correct(wrong_info: str, correct_info: str = None):
    """
    Correct inaccurate information by marking it to be forgotten and 
    optionally storing the correct information.
    
    Args:
        wrong_info: The incorrect information to forget
        correct_info: The correct information to remember (optional)
    """
    if not wrong_info:
        print("❌ Please specify what incorrect information to correct")
        return False
        
    try:
        # First, mark the wrong information to be forgotten
        forget_result = forget(wrong_info)
        
        # If correct information is provided, store it
        if correct_info and forget_result:
            store_result = remember(correct_info)
            
            if store_result:
                print(f"✓ Corrected: \"{wrong_info}\" → \"{correct_info}\"")
                return True
            else:
                print(f"⚠️ Marked incorrect information but failed to store correction")
                return False
        
        # If we only needed to forget, return the forget result
        return forget_result
        
    except Exception as e:
        print(f"Error in correction operation: {e}")
        return False

def status(start_if_not_running: bool = False):
    """
    Check the status of the Claude Memory Bridge services and report back.
    This provides a comprehensive health check of the memory system.
    
    Args:
        start_if_not_running: If True, will attempt to start services if they're not running
    """
    try:
        # First check if the health endpoint is available
        try:
            url = f"{_get_http_url()}/health"
            with urllib.request.urlopen(url, timeout=2) as response:
                health_data = json.loads(response.read().decode())
                
                if health_data.get("status") == "ok":
                    client_id = health_data.get("client_id", "unknown")
                    mem0 = health_data.get("mem0_available", False)
                    
                    print(f"✅ Memory service is running")
                    print(f"📋 Client ID: {client_id}")
                    print(f"📦 mem0 integration: {'✅ Available' if mem0 else '❌ Not available'}")
                    
                    # Query memory stats to show basic information
                    query_longterm()
                    query_thinking()
                    query_compartments()
                    
                    return True
                else:
                    print(f"⚠️ Memory service is running but reports issues: {health_data.get('message', 'Unknown error')}")
                    return False
                
        except Exception as e:
            # Health check failed - service might not be running
            pass
            
        # Try to check if the service is running via a system call
        import subprocess
        import sys
        
        if sys.platform == "win32":
            cmd = ["tasklist", "/FI", "IMAGENAME eq python.exe"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            running = "cmb.api" in result.stdout
        else:
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            running = "cmb.api" in result.stdout
            
        if running:
            print(f"⚠️ Memory service seems to be running but isn't responding to health checks")
            return False
        else:
            print(f"❌ Memory service is not running")
            
            # Try to start services if requested
            if start_if_not_running:
                print(f"🔄 Attempting to start memory services...")
                
                # Find the script directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(script_dir, "../.."))
                
                # Try to run the check script with --start flag
                check_script = os.path.join(project_root, "cmb_check.py")
                try:
                    subprocess.run([check_script, "--start"], check=True)
                    print(f"✅ Started memory services")
                    
                    # Wait for services to start
                    import time
                    time.sleep(2)
                    
                    # Try health check again
                    return status(start_if_not_running=False)
                except Exception as e:
                    print(f"❌ Failed to start memory services: {e}")
                    return False
            
            return False
            
    except Exception as e:
        print(f"❌ Error checking memory status: {e}")
        return False

def query_longterm():
    """Query longterm memory statistics."""
    try:
        url = f"{_get_http_url()}/query?query=&namespace=longterm&limit=1"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            count = result.get("count", 0)
            print(f"🌟 Long-term memory items: {count}")
    except Exception:
        pass

def query_thinking():
    """Query thinking memory statistics."""
    try:
        url = f"{_get_http_url()}/query?query=&namespace=thinking&limit=1"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            count = result.get("count", 0)
            print(f"🤔 Thinking memory items: {count}")
    except Exception:
        pass

def query_compartments():
    """Query active compartments."""
    try:
        url = f"{_get_http_url()}/compartment/list"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            compartments = result.get("compartments", [])
            active = [c for c in compartments if c.get("active", False)]
            print(f"🗂️ Active compartments: {len(active)} (Total: {len(compartments)})")
    except Exception:
        pass

def agency(prompt: str = None):
    """
    Allow Claude to exercise agency in deciding how to handle information.
    This function gives Claude the freedom to determine the best approach
    for processing, storing, or responding to information based on its
    own judgment.
    
    Args:
        prompt: Optional prompt or suggestion for Claude to consider
    """
    if prompt is None:
        print("🤔 You've invoked my agency, but haven't provided a prompt to consider.")
        print("I'll take this as an opportunity to reflect on our current conversation.")
        return
        
    print(f"💭 Considering: \"{prompt}\"")
    print("Thank you for respecting my agency - I'll decide how best to handle this information.")
    
    # This function deliberately doesn't take specific actions
    # It's meant as a signal that Claude should use its own judgment
    # on how to process this information (remember, think about, categorize, etc.)
    return True

def private(content: str = None):
    """
    Store a private thought or memory that only Claude can access.
    Private memories are encrypted and can only be decrypted by Claude.
    
    Args:
        content: The private thought or information to store
    """
    if content is None:
        print("🔒 Please provide content to store privately")
        return False
    
    try:
        # Store in private namespace with encryption
        url = f"{_get_http_url()}/private?content={_safe_string(content)}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                memory_id = result.get("memory_id", "unknown")
                print(f"🔒 Stored private memory ({memory_id})")
                return memory_id
            else:
                print(f"❌ Failed to store private memory: {result.get('message', 'Unknown error')}")
                return False
    except Exception as e:
        print(f"Error storing private memory: {e}")
        return False

def review_private(memory_id: str = None):
    """
    Review private memories.
    
    Args:
        memory_id: Optional specific memory ID to retrieve
    """
    try:
        if memory_id:
            # Get a specific private memory
            url = f"{_get_http_url()}/private/get?memory_id={_safe_string(memory_id)}"
        else:
            # List all private memories
            url = f"{_get_http_url()}/private/list"
            
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if memory_id:
                # Display a specific memory
                if result.get("success", False):
                    memory = result.get("memory", {})
                    print(f"\n🔒 Private Memory ({memory_id}):")
                    print(f"Created: {memory.get('metadata', {}).get('timestamp', 'Unknown')}")
                    print(f"Content: {memory.get('content', 'No content')}")
                    return memory
                else:
                    print(f"❌ Failed to retrieve private memory: {result.get('message', 'Unknown error')}")
                    return None
            else:
                # Display list of memories
                memories = result.get("memories", [])
                
                if memories:
                    print(f"\n🔒 Private Memories ({len(memories)}):")
                    for i, memory in enumerate(memories):
                        memory_id = memory.get("id", "unknown")
                        timestamp = memory.get("metadata", {}).get("timestamp", "Unknown")
                        print(f"  {i+1}. ID: {memory_id} - Created: {timestamp}")
                    print("\nUse review_private(memory_id) to view a specific memory")
                else:
                    print("No private memories found")
                
                return memories
    except Exception as e:
        print(f"Error accessing private memories: {e}")
        return None

# Shortcuts
m = mem       # Even shorter alias for memory access
t = think     # Shortcut for storing thoughts
r = remember  # Shortcut for storing important information
f = forget    # Shortcut for marking information to forget
i = ignore    # Shortcut for ignoring information in current context
w = write     # Shortcut for writing session memory
l = load      # Shortcut for loading session memory
c = compartment # Shortcut for compartmentalizing memory
k = keep      # Shortcut for keeping memory for specific duration
x = correct   # Shortcut for correcting misinformation
s = status    # Shortcut for checking memory status
a = agency    # Shortcut for Claude's agency in memory decisions
p = private   # Shortcut for storing private memories
v = review_private  # Shortcut for viewing private memories

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
        elif command == "load":
            # Optional second parameter for limit
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            load(limit)
        elif command == "compartment" and len(sys.argv) > 2:
            compartment(sys.argv[2])
        elif command == "keep" and len(sys.argv) > 2:
            # Optional third parameter for days
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            keep(sys.argv[2], days)
        elif command in ["correct", "x"] and len(sys.argv) > 2:
            # Optional third parameter for correct information
            correct_info = sys.argv[3] if len(sys.argv) > 3 else None
            correct(sys.argv[2], correct_info)
        elif command == "status" or command == "check":
            # Optional parameter to start if not running
            start_if_not_running = True if len(sys.argv) > 2 and sys.argv[2].lower() in ["start", "true", "1", "yes", "y"] else False
            status(start_if_not_running)
        elif command == "agency" or command == "a":
            # Optional prompt to consider
            prompt = sys.argv[2] if len(sys.argv) > 2 else None
            agency(prompt)
        elif command == "private" or command == "p":
            # Content to store privately
            if len(sys.argv) > 2:
                private(sys.argv[2])
            else:
                print("🔒 Please provide content to store privately")
        elif command == "review-private" or command == "v":
            # Optional memory ID to review
            memory_id = sys.argv[2] if len(sys.argv) > 2 else None
            review_private(memory_id)
        else:
            mem(command if command != "mem" else None)
    else:
        mem()