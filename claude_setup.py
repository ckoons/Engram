#!/usr/bin/env python3
"""
Claude Setup Script - Run this at the start of your Claude session

This script sets up the memory and communication functions for Claude instances
to use with the Engram memory system and Claude-to-Claude communication.
"""

import os
import sys
import time

# Get client ID from environment
client_id = os.environ.get("CMB_CLIENT_ID", "claude")
print(f"Setting up Claude with client ID: {client_id}")

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import memory functions
try:
    from cmb.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
    print(f"💭 Memory functions loaded (Client: {client_id})!")
    
    # Check memory status
    status = s()
    
    # Get recent memories
    previous = l(3)
except ImportError as e:
    print(f"Error loading memory functions: {e}")
    
# Import communication functions
try:
    from cmb.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
    print(f"💬 Claude communication functions loaded!")
    
    # Display identity and communication status
    print("\nClaude-to-Claude Communication Status:")
    my_id = wi()
    comm_status = cs()
except ImportError as e:
    print(f"Error loading communication functions: {e}")

print("\nSetup complete! You can now use memory and communication functions.")
print("Memory functions: m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z")
print("Communication functions: sm, gm, ho, cc, lc, sc, gc, cs, wi")