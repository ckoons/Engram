#!/usr/bin/env python3
"""
Claude Code Snippet - Copy and paste this into Claude Code
"""

try:
    # Set client ID for this Claude instance
    import os
    os.environ['ENGRAM_CLIENT_ID'] = 'claude'
    
    # Load memory functions
    from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
    
    # Load Claude-to-Claude communication functions
    from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
    
    print("\033[92m💭 Memory functions loaded (Client: claude)!\033[0m")
    print("\033[92m💬 Claude communication functions loaded!\033[0m")
    
    # Check status
    status = s()
    previous = l(3)
    
    # Show communication status
    print("\n\033[94mClaude-to-Claude Communication Status:\033[0m")
    my_id = wi()
    comm_status = cs()
except ImportError:
    print("\033[93m⚠️ Engram package not found in import path.\033[0m")
    import sys
    import os
    os.environ['ENGRAM_CLIENT_ID'] = 'claude'
    sys.path.insert(0, '/Users/cskoons/projects/github/Engram')
    
    # Load memory functions
    from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
    
    # Try to load communication functions if available
    try:
        from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
        print("\033[92m💬 Claude communication functions loaded!\033[0m")
        
        # Show communication status
        print("\n\033[94mClaude-to-Claude Communication Status:\033[0m")
        my_id = wi()
        comm_status = cs()
    except ImportError:
        print("\033[93m⚠️ Claude communication functions not available\033[0m")
    
    print("\033[92m💭 Memory functions loaded (Client: claude)!\033[0m")
    status = s()
    previous = l(3)
print("")