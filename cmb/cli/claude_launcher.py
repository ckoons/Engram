#!/usr/bin/env python3
"""
Claude Instance Launcher

This script provides a programmatic way to launch and manage multiple
Claude instances with different configurations.
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.claude_launcher")

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
sys.path.insert(0, project_root)

# Try to import mode detection
try:
    from cmb.core.mode_detection import detect_execution_mode, adapt_to_mode, get_mode_message
except ImportError:
    logger.warning("Mode detection module not available. Some functionality will be limited.")
    
    def detect_execution_mode():
        return "execution"
    
    def adapt_to_mode(mode):
        return {"can_execute": mode == "execution"}
    
    def get_mode_message(mode):
        return f"Running in {mode} mode"

def find_claude_binary() -> str:
    """
    Find the Claude binary executable.
    
    Returns:
        Path to Claude binary
    """
    # Look for claude in PATH
    claude_path = None
    
    # Check common locations
    common_paths = [
        "/usr/local/bin/claude",
        "/usr/bin/claude",
        os.path.expanduser("~/.local/bin/claude"),
        os.path.expanduser("~/bin/claude")
    ]
    
    # Try CLAUDE_PATH environment variable
    if "CLAUDE_PATH" in os.environ:
        common_paths.insert(0, os.environ["CLAUDE_PATH"])
    
    # Check each location
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            claude_path = path
            break
    
    # If not found, try to find in PATH
    if claude_path is None:
        try:
            # Use which command to find claude
            result = subprocess.run(["which", "claude"], capture_output=True, text=True)
            if result.returncode == 0:
                claude_path = result.stdout.strip()
        except Exception:
            pass
    
    # If still not found, default to hoping it's in PATH
    if claude_path is None:
        claude_path = "claude"
    
    logger.info(f"Using Claude at: {claude_path}")
    return claude_path

def generate_startup_code(client_id: str, data_dir: Optional[str] = None) -> str:
    """
    Generate Python code that will initialize Claude with memory services.
    
    Args:
        client_id: ID for this Claude instance
        data_dir: Optional data directory
        
    Returns:
        Python code string to execute when starting Claude
    """
    # Base imports and setup
    code = f"""
import os
import sys
import json
from pathlib import Path

# Set client ID
os.environ['CMB_CLIENT_ID'] = '{client_id}'

# Add project path if needed
project_path = '{project_root}'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

try:
    # Try to import mode detection
    try:
        from cmb.core.mode_detection import detect_execution_mode, adapt_to_mode, get_mode_message
        mode = detect_execution_mode()
        config = adapt_to_mode(mode)
        print(get_mode_message(mode))
    except ImportError:
        mode = "execution"  # Default
        config = {{"can_execute": True}}
        print(f"Mode detection not available. Assuming {{mode}} mode.")
        
    # Import memory functions based on execution mode
    if config["can_execute"]:
        # Load memory functions
        try:
            from cmb.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
            print("\\033[92m💭 Memory functions loaded (Client: {client_id})!\\033[0m")
        except ImportError:
            try:
                from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z
                print("\\033[92m💭 Memory functions loaded (Client: {client_id})!\\033[0m")
            except ImportError:
                print("\\033[93m⚠️ Memory functions not available\\033[0m")
                # Create dummy functions to avoid errors
                def dummy_func(*args, **kwargs): return print("Memory function not available")
                m = t = r = w = l = c = k = s = a = p = v = d = n = q = y = z = dummy_func
        
        # Load Claude-to-Claude communication functions
        try:
            from cmb.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
            print("\\033[92m💬 Claude communication functions loaded!\\033[0m")
            
            # Show communication status
            print("\\nClaude-to-Claude Communication Status:")
            my_id = wi()
            comm_status = cs()
        except ImportError:
            try:
                from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
                print("\\033[92m💬 Claude communication functions loaded!\\033[0m")
                
                # Show communication status  
                print("\\nClaude-to-Claude Communication Status:")
                my_id = wi()
                comm_status = cs()
            except ImportError:
                print("\\033[93m⚠️ Claude communication functions not available\\033[0m")
                # Create dummy functions to avoid errors
                def dummy_func(*args, **kwargs): return print("Communication function not available")
                sm = gm = ho = cc = lc = sc = gc = cs = wi = dummy_func
                
        # Check memory status
        status = s()
        
        # Try to get recent memories
        try:
            previous = l(3)
        except:
            previous = None
    else:
        # In analysis mode, just print info about functions
        print("\\033[93mAnalysis mode detected. Memory functions will be explained but not executed.\\033[0m")
        print("Available memory functions in execution mode: m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z")
        print("Available communication functions in execution mode: sm, gm, ho, cc, lc, sc, gc, cs, wi")
        
    # Store session start in memory if in execution mode
    if config.get("can_execute", False):
        try:
            t(f"Session started in {{mode}} mode - {client_id}")
        except:
            pass
            
except Exception as e:
    print(f"\\033[91mError initializing Claude: {{e}}\\033[0m")

print("")  # Add empty line at end
"""
    return code

def launch_claude(client_id: str, mode: str = "interactive", script_path: Optional[str] = None, 
                 data_dir: Optional[str] = None, allowed_tools: Optional[str] = None) -> subprocess.Popen:
    """
    Launch a Claude instance with memory services.
    
    Args:
        client_id: ID for this Claude instance
        mode: Launch mode (interactive or script)
        script_path: Path to script to run (if mode is script)
        data_dir: Optional data directory
        allowed_tools: Tools to allow for Claude
        
    Returns:
        subprocess.Popen object for the launched process
    """
    # Generate startup code
    startup_code = generate_startup_code(client_id, data_dir)
    
    # Create a temporary file for the startup code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(startup_code)
        startup_file = f.name
    
    # Find claude binary
    claude_binary = find_claude_binary()
    
    # Construct command
    cmd = [claude_binary]
    
    # Add environment variable for client ID
    os.environ["CMB_CLIENT_ID"] = client_id
    
    # Add allowed tools if specified
    if allowed_tools:
        cmd.extend(["--allowedTools", allowed_tools])
    else:
        cmd.extend(["--allowedTools", "Bash(*),Edit,View,Replace,BatchTool,GlobTool,GrepTool,LS,ReadNotebook,NotebookEditCell,WebFetchTool"])
    
    # Add startup code
    cmd.extend(["-e", f"exec(open('{startup_file}').read())"])
    
    # Add script to run if specified
    if mode == "script" and script_path:
        cmd.extend([script_path])
    
    # Log the command
    logger.info(f"Launching Claude: {' '.join(cmd)}")
    
    # Launch claude
    try:
        process = subprocess.Popen(cmd)
        logger.info(f"Launched Claude with PID {process.pid}")
        
        # Store the process info
        process_info = {
            "pid": process.pid,
            "client_id": client_id,
            "startup_file": startup_file,
            "command": " ".join(cmd),
            "start_time": time.time()
        }
        
        # Return the process
        return process, process_info
    except Exception as e:
        logger.error(f"Error launching Claude: {e}")
        os.remove(startup_file)
        raise

def save_process_info(process_info: Dict[str, Any], data_dir: Optional[str] = None) -> str:
    """
    Save information about a launched Claude process.
    
    Args:
        process_info: Process information dictionary
        data_dir: Optional data directory
        
    Returns:
        Path to the saved file
    """
    # Set up data directory
    if data_dir is None:
        data_dir = os.path.expanduser("~/.cmb/launcher")
    
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    # Create file path
    client_id = process_info["client_id"]
    pid = process_info["pid"]
    file_path = data_path / f"{client_id}_{pid}.json"
    
    # Add timestamp
    process_info["saved_at"] = time.time()
    
    # Save to file
    with open(file_path, "w") as f:
        json.dump(process_info, f, indent=2)
    
    logger.info(f"Saved process info to {file_path}")
    return str(file_path)

def launch_multiple_instances(specs: List[Dict[str, Any]], data_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Launch multiple Claude instances with different configurations.
    
    Args:
        specs: List of instance specifications
        data_dir: Optional data directory
        
    Returns:
        List of process information dictionaries
    """
    processes = []
    
    for i, spec in enumerate(specs):
        # Get spec parameters
        client_id = spec.get("client_id", f"claude_{i+1}")
        mode = spec.get("mode", "interactive")
        script_path = spec.get("script_path")
        allowed_tools = spec.get("allowed_tools")
        
        # Launch instance
        try:
            process, process_info = launch_claude(
                client_id=client_id,
                mode=mode,
                script_path=script_path,
                data_dir=data_dir,
                allowed_tools=allowed_tools
            )
            
            # Save process info
            info_path = save_process_info(process_info, data_dir)
            process_info["info_path"] = info_path
            
            # Add process object
            process_info["process"] = process
            
            processes.append(process_info)
            
            # Wait a bit before launching the next instance
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error launching instance {client_id}: {e}")
    
    return processes

def load_spec_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load Claude instance specifications from a JSON file.
    
    Args:
        file_path: Path to the specification file
        
    Returns:
        List of instance specifications
    """
    with open(file_path, "r") as f:
        specs = json.load(f)
    
    # Ensure it's a list
    if not isinstance(specs, list):
        specs = [specs]
    
    return specs

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Claude Instance Launcher")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Launch command
    launch_parser = subparsers.add_parser("launch", help="Launch a Claude instance")
    launch_parser.add_argument("--client-id", type=str, default="claude",
                            help="Client ID for this Claude instance")
    launch_parser.add_argument("--mode", type=str, choices=["interactive", "script"],
                            default="interactive", help="Launch mode")
    launch_parser.add_argument("--script", type=str, 
                            help="Path to script to run (if mode is script)")
    launch_parser.add_argument("--data-dir", type=str,
                            help="Data directory for Claude memory")
    launch_parser.add_argument("--allowed-tools", type=str,
                            help="Comma-separated list of allowed tools")
    
    # Launch multiple command
    multi_parser = subparsers.add_parser("multi", help="Launch multiple Claude instances")
    multi_parser.add_argument("--spec", type=str, required=True,
                           help="Path to instance specification file")
    multi_parser.add_argument("--data-dir", type=str,
                           help="Data directory for Claude memory")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    if args.command == "launch":
        # Launch a single instance
        process, process_info = launch_claude(
            client_id=args.client_id,
            mode=args.mode,
            script_path=args.script,
            data_dir=args.data_dir,
            allowed_tools=args.allowed_tools
        )
        
        # Save process info
        save_process_info(process_info, args.data_dir)
        
        # Wait for process to finish
        process.wait()
        
    elif args.command == "multi":
        # Launch multiple instances
        specs = load_spec_file(args.spec)
        processes = launch_multiple_instances(specs, args.data_dir)
        
        # Wait for all processes to finish
        for process_info in processes:
            process = process_info["process"]
            process.wait()
    
    else:
        print("Please specify a command: launch or multi")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())