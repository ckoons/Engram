#!/usr/bin/env python3
"""
Claude Memory Bridge startup script for Claude Code sessions.

This script should be executed at the beginning of a Claude Code session
to check the memory service status and import the memory functions.

Usage:
  # At the beginning of your Claude Code session:
  %run /path/to/claude_startup.py
  
  # Or in a Python cell:
  exec(open("/path/to/claude_startup.py").read())
"""

import os
import sys
import importlib.util
from pathlib import Path

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def find_cmb_module():
    """Find the CMB module in the current environment."""
    try:
        # First try to import as an installed package
        import cmb
        return cmb.__path__[0]
    except ImportError:
        # Not installed, try to find in sys.path
        for path in sys.path:
            if os.path.exists(os.path.join(path, "cmb")):
                return os.path.join(path, "cmb")
        
        # Try to find in common locations
        common_paths = [
            os.path.expanduser("~/projects/github/ClaudeMemoryBridge"),
            os.path.expanduser("~/ClaudeMemoryBridge"),
            os.path.expanduser("~/github/ClaudeMemoryBridge"),
        ]
        
        for path in common_paths:
            if os.path.exists(os.path.join(path, "cmb")):
                # Add to path
                sys.path.insert(0, path)
                return os.path.join(path, "cmb")
    
    return None

def import_quickmem():
    """Import and return the quickmem module."""
    cmb_path = find_cmb_module()
    
    if not cmb_path:
        print(f"{RED}Could not find ClaudeMemoryBridge module.{RESET}")
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(
            "quickmem", 
            os.path.join(cmb_path, "cli", "quickmem.py")
        )
        quickmem = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(quickmem)
        return quickmem
    except Exception as e:
        print(f"{RED}Error importing quickmem module: {e}{RESET}")
        return None

def check_services(quickmem):
    """Check if the memory services are running and start if needed."""
    if not quickmem:
        return False
    
    try:
        # Check service status
        service_running = quickmem.status(start_if_not_running=False)
        
        if not service_running:
            print(f"\n{YELLOW}Memory services are not running properly.{RESET}")
            start = input("Would you like to start them now? (y/n): ").lower()
            
            if start in ["y", "yes"]:
                return quickmem.status(start_if_not_running=True)
            else:
                print(f"{YELLOW}Memory services will not be available for this session.{RESET}")
                return False
        
        return service_running
    except Exception as e:
        print(f"{RED}Error checking memory services: {e}{RESET}")
        return False

def auto_load_memories(quickmem, limit=3):
    """Automatically load previous session memories."""
    try:
        memories = quickmem.load(limit)
        if memories:
            print(f"\n{GREEN}✅ Successfully loaded {len(memories)} previous session memories{RESET}")
            
            # Add default reflective thought
            quickmem.think("Starting a new session with loaded memories. I'll maintain continuity from previous sessions.")
            
            return memories
        else:
            print(f"\n{YELLOW}No previous session memories found to load{RESET}")
            return []
    except Exception as e:
        print(f"{YELLOW}Error loading memories: {e}{RESET}")
        return []

def main():
    """Main entry point."""
    print(f"\n{BOLD}{BLUE}===== Claude Memory Bridge Startup ====={RESET}\n")
    
    # Import the quickmem module
    quickmem = import_quickmem()
    
    if not quickmem:
        print(f"{RED}Failed to initialize Claude Memory Bridge.{RESET}")
        return
    
    # Check and start services if needed
    service_running = check_services(quickmem)
    
    # Import memory functions into globals
    if service_running:
        print(f"\n{GREEN}Importing memory functions into global namespace...{RESET}")
        globals()['mem'] = quickmem.mem
        globals()['think'] = quickmem.think
        globals()['remember'] = quickmem.remember
        globals()['forget'] = quickmem.forget
        globals()['ignore'] = quickmem.ignore
        globals()['write'] = quickmem.write
        globals()['load'] = quickmem.load
        globals()['compartment'] = quickmem.compartment
        globals()['keep'] = quickmem.keep
        globals()['correct'] = quickmem.correct
        globals()['status'] = quickmem.status
        globals()['agency'] = quickmem.agency
        globals()['private'] = quickmem.private
        globals()['review_private'] = quickmem.review_private
        
        # Short aliases
        globals()['m'] = quickmem.m
        globals()['t'] = quickmem.t
        globals()['r'] = quickmem.r
        globals()['f'] = quickmem.f
        globals()['i'] = quickmem.i
        globals()['w'] = quickmem.w
        globals()['l'] = quickmem.l
        globals()['c'] = quickmem.c
        globals()['k'] = quickmem.k
        globals()['x'] = quickmem.x
        globals()['s'] = quickmem.s
        globals()['a'] = quickmem.a
        globals()['p'] = quickmem.p
        globals()['v'] = quickmem.v
        
        # Auto-load previous memories
        auto_load_memories(quickmem)
        
        print(f"{GREEN}✅ Memory functions are now available!{RESET}")
        print(f"{BLUE}Use m() to search memories, t() to store thoughts, r() to remember important info...{RESET}")
    else:
        print(f"\n{YELLOW}Memory functions are not available for this session.{RESET}")
        print(f"{YELLOW}You can try again by running: from cmb.cli.quickmem import *{RESET}")
    
    print(f"\n{BOLD}{BLUE}===================================={RESET}\n")

if __name__ == "__main__":
    main()