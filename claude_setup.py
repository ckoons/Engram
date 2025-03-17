#!/usr/bin/env python3
"""
Claude Setup Script - Run this at the start of your Claude session

This script sets up the memory and communication functions for Claude instances
to use with the Engram memory system and Claude-to-Claude communication.
"""

try:
    # Set client ID for this Claude instance
    import os
    os.environ['ENGRAM_CLIENT_ID'] = 'claude'
    
    # Try to load from the new engram namespace first
    try:
        # Load memory functions
        from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
        
        # Load Claude-to-Claude communication functions
        from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
        
        print("\033[92m💭 Memory functions loaded from engram package (Client: claude)!\033[0m")
        print("\033[92m💬 Claude communication functions loaded!\033[0m")
    except ImportError:
        print("\033[93m⚠️ Engram package not found in import path.\033[0m")
        print("\033[93m⚠️ Make sure Engram is installed or in your Python path.\033[0m")
    
    # Check status
    status = s()
    try:
        # Try to get recent memories (but don't fail if it doesn't work)
        from engram.cli.quickmem import latest_sync
        previous = latest_sync(3)
    except Exception:
        pass
    
    # Show communication status
    print("\n\033[94mClaude-to-Claude Communication Status:\033[0m")
    my_id = wi()
    comm_status = cs()
except ImportError:
    print("\033[93m⚠️ Using direct module path. Adding Engram directory to Python path.\033[0m")
    import sys
    import os
    os.environ['ENGRAM_CLIENT_ID'] = 'claude'
    sys.path.insert(0, '/Users/cskoons/projects/github/Engram')
    
    # Try engram namespace first
    try:
        # Load memory functions
        from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
        
        # Try to load communication functions if available
        try:
            from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
            print("\033[92m💬 Claude communication functions loaded from engram package!\033[0m")
            
            # Show communication status
            print("\n\033[94mClaude-to-Claude Communication Status:\033[0m")
            my_id = wi()
            comm_status = cs()
        except ImportError:
            print("\033[93m⚠️ Claude communication functions not available in engram package\033[0m")
        
        print("\033[92m💭 Memory functions loaded from engram package (Client: claude)!\033[0m")
    except ImportError:
        print("\033[93m⚠️ Engram package not found in import path.\033[0m")
        print("\033[93m⚠️ Make sure Engram is installed or in your Python path.\033[0m")
    
    # Check status
    status = s()
    try:
        # Try to get recent memories (but don't fail if it doesn't work)
        from engram.cli.quickmem import latest_sync
        previous = latest_sync(3)
    except Exception:
        pass
print("")

print("\nSetup complete! You can now use memory and communication functions.")
print("Memory functions: m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z")
print("Communication functions: sm, gm, ho, cc, lc, sc, gc, cs, wi")