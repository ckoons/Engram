#!/usr/bin/env python3
"""
Engram Dual Mode Status Checker

This script checks the status of Engram memory services (both HTTP and MCP)
and provides information about running instances and connectivity.
It can also start, restart, or stop services as needed.

Usage:
  ./engram_check_dual.py                      # Check status only
  ./engram_check_dual.py --start              # Start services if not running
  ./engram_check_dual.py --restart            # Restart services regardless of state
  ./engram_check_dual.py --stop               # Stop running services
  ./engram_check_dual.py --http-only          # Only check/manage HTTP service
  ./engram_check_dual.py --mcp-only           # Only check/manage MCP service
"""

import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Check for required dependencies
try:
    import requests
except ImportError:
    print("Error: 'requests' module not found.")
    print("Please install required dependencies with:")
    print("    pip install requests")
    print("or run the install script:")
    print("    ./install.sh")
    sys.exit(1)

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default URLs for services
DEFAULT_HTTP_URL = "http://127.0.0.1:8000/http"
DEFAULT_HTTP_SERVER_URL = "http://127.0.0.1:8000/memory"
DEFAULT_MCP_URL = "http://127.0.0.1:8001"
DEFAULT_DATA_DIR = os.path.expanduser("~/.engram")

def get_http_url():
    """Get the HTTP URL for the Engram wrapper."""
    return os.environ.get("ENGRAM_HTTP_URL", DEFAULT_HTTP_URL)

def get_http_server_url():
    """Get the URL for the Engram HTTP memory server."""
    return os.environ.get("ENGRAM_SERVER_URL", DEFAULT_HTTP_SERVER_URL)

def get_mcp_url():
    """Get the URL for the Engram MCP server."""
    return os.environ.get("ENGRAM_MCP_URL", DEFAULT_MCP_URL)

def get_script_path():
    """Get the path to the script directory."""
    return os.path.dirname(os.path.abspath(__file__))

def check_process_running(name_pattern: str) -> List[int]:
    """Check if a process with the given name pattern is running."""
    try:
        # Different command for macOS/Linux vs Windows
        if sys.platform == "win32":
            cmd = ["tasklist", "/FI", f"IMAGENAME eq {name_pattern}"]
        else:
            # Use pgrep for more reliable pattern matching
            result = subprocess.run(["pgrep", "-f", name_pattern], capture_output=True, text=True)
            if result.returncode == 0:
                # pgrep successful, parse the output for PIDs
                pids = [int(pid) for pid in result.stdout.strip().split()]
                return pids
            
            # Fallback to ps aux if pgrep fails
            cmd = ["ps", "aux"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and sys.platform != "win32":  # Ignore error for pgrep fallback
            print(f"{RED}Error checking process status: {result.stderr}{RESET}")
            return []
        
        output = result.stdout
        
        # For Windows, just check if the process is in the output
        if sys.platform == "win32":
            return [1] if name_pattern in output else []
        
        # For macOS/Linux, parse the output to find PIDs
        pids = []
        for line in output.split("\n"):
            if name_pattern in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pids.append(int(parts[1]))
                    except ValueError:
                        pass
        return pids
    except Exception as e:
        print(f"{RED}Error checking process status: {e}{RESET}")
        return []

def check_services(check_http=True, check_mcp=True) -> Dict[str, Any]:
    """Check if Engram memory services are running."""
    result = {
        "http_server": {
            "running": False,
            "pid": None,
            "url": get_http_server_url(),
            "connected": False,
        },
        "mcp_server": {
            "running": False,
            "pid": None,
            "url": get_mcp_url(),
            "connected": False,
        },
        "vector_available": False,
    }
    
    # Check HTTP server if requested
    if check_http:
        # Check consolidated server
        http_pids = check_process_running("engram.api.consolidated_server")
        
        if http_pids:
            result["http_server"]["running"] = True
            result["http_server"]["pid"] = http_pids[0]
        
        # Try to get version and connectivity information
        if result["http_server"]["running"]:
            try:
                response = requests.get(f"{get_http_url()}/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    result["http_server"]["connected"] = health_data.get("status") == "ok"
                    result["vector_available"] = health_data.get("vector_available", False)
            except Exception:
                pass
    
    # Check MCP server if requested
    if check_mcp:
        # Check MCP server
        mcp_pids = check_process_running("engram.api.mcp_server")
        
        if mcp_pids:
            result["mcp_server"]["running"] = True
            result["mcp_server"]["pid"] = mcp_pids[0]
        
        # Try to get MCP server status
        if result["mcp_server"]["running"]:
            try:
                response = requests.get(f"{get_mcp_url()}/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    result["mcp_server"]["connected"] = health_data.get("status") == "healthy"
            except Exception:
                pass
    
    return result

def start_services(client_id: str = "claude", data_dir: str = None, 
                   force_restart: bool = False, http_only: bool = False,
                   mcp_only: bool = False, http_port: int = 8000,
                   mcp_port: int = 8001) -> bool:
    """Start the Engram services."""
    # First check if services are already running
    if not force_restart:
        status = check_services()
        if http_only and status["http_server"]["running"]:
            print(f"{YELLOW}HTTP service is already running.{RESET}")
            return True
        elif mcp_only and status["mcp_server"]["running"]:
            print(f"{YELLOW}MCP service is already running.{RESET}")
            return True
        elif not http_only and not mcp_only and status["http_server"]["running"] and status["mcp_server"]["running"]:
            print(f"{YELLOW}Both services are already running.{RESET}")
            return True
    
    # Stop services if force_restart is True
    if force_restart:
        stop_services(http_only, mcp_only)
    
    # Set up command parameters
    script_path = get_script_path()
    success = True
    
    if not mcp_only:
        # Start HTTP service
        engram_http_path = os.path.join(script_path, "engram_consolidated")
        try:
            os.chmod(engram_http_path, 0o755)
        except Exception:
            pass
        
        # Build command for HTTP server
        http_cmd = [engram_http_path, "--client-id", client_id, "--port", str(http_port), "--host", "127.0.0.1"]
        if data_dir:
            http_cmd.extend(["--data-dir", data_dir])
        
        # Start HTTP server
        try:
            print(f"{GREEN}Starting HTTP service on port {http_port}...{RESET}")
            subprocess.Popen(http_cmd)
            print(f"{GREEN}HTTP service started successfully.{RESET}")
        except Exception as e:
            print(f"{RED}Error starting HTTP service: {e}{RESET}")
            success = False
    
    if not http_only:
        # Start MCP service
        engram_mcp_path = os.path.join(script_path, "engram_mcp")
        try:
            os.chmod(engram_mcp_path, 0o755)
        except Exception:
            pass
        
        # Build command for MCP server
        mcp_cmd = [engram_mcp_path, "--client-id", client_id, "--port", str(mcp_port), "--host", "127.0.0.1"]
        if data_dir:
            mcp_cmd.extend(["--data-dir", data_dir])
        
        # Start MCP server
        try:
            print(f"{GREEN}Starting MCP service on port {mcp_port}...{RESET}")
            subprocess.Popen(mcp_cmd)
            print(f"{GREEN}MCP service started successfully.{RESET}")
        except Exception as e:
            print(f"{RED}Error starting MCP service: {e}{RESET}")
            success = False
    
    # Give services time to start
    time.sleep(2)
    return success

def stop_services(http_only: bool = False, mcp_only: bool = False) -> bool:
    """Stop the Engram services."""
    status = check_services()
    success = True
    
    # Check if services are running
    if http_only and not status["http_server"]["running"]:
        print(f"{YELLOW}HTTP service is not running.{RESET}")
        return True
    elif mcp_only and not status["mcp_server"]["running"]:
        print(f"{YELLOW}MCP service is not running.{RESET}")
        return True
    elif not http_only and not mcp_only and not status["http_server"]["running"] and not status["mcp_server"]["running"]:
        print(f"{YELLOW}No services are running.{RESET}")
        return True
    
    # Get PIDs and stop processes
    if (not mcp_only) and status["http_server"]["running"] and status["http_server"]["pid"]:
        try:
            pid = status["http_server"]["pid"]
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                subprocess.run(["kill", str(pid)], capture_output=True)
            print(f"{GREEN}Stopped HTTP service with PID {pid}.{RESET}")
        except Exception as e:
            print(f"{RED}Error stopping HTTP service: {e}{RESET}")
            success = False
    
    if (not http_only) and status["mcp_server"]["running"] and status["mcp_server"]["pid"]:
        try:
            pid = status["mcp_server"]["pid"]
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                subprocess.run(["kill", str(pid)], capture_output=True)
            print(f"{GREEN}Stopped MCP service with PID {pid}.{RESET}")
        except Exception as e:
            print(f"{RED}Error stopping MCP service: {e}{RESET}")
            success = False
    
    # Give processes time to shut down
    time.sleep(1)
    
    # Verify they're stopped
    new_status = check_services()
    if (not mcp_only) and new_status["http_server"]["running"]:
        print(f"{YELLOW}Warning: HTTP service is still running after stop attempt.{RESET}")
        success = False
    if (not http_only) and new_status["mcp_server"]["running"]:
        print(f"{YELLOW}Warning: MCP service is still running after stop attempt.{RESET}")
        success = False
    
    return success

def test_mcp_connection() -> Dict[str, Any]:
    """Test connection to the MCP server."""
    result = {
        "success": False,
        "manifest": None,
        "error": None,
    }
    
    try:
        response = requests.get(f"{get_mcp_url()}/manifest", timeout=5)
        if response.status_code == 200:
            result["success"] = True
            result["manifest"] = response.json()
        else:
            result["error"] = f"HTTP error: {response.status_code}"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def display_status_report(services_status: Dict[str, Any]):
    """Display a comprehensive status report."""
    # Header
    print(f"\n{BOLD}{BLUE}==== Engram Dual Mode Status Report ===={RESET}\n")
    
    # HTTP Service Status
    print(f"{BOLD}HTTP Service Status:{RESET}")
    http_status = "✅ Running" if services_status["http_server"]["running"] else "❌ Not Running"
    http_connected = "✅ Connected" if services_status["http_server"]["connected"] else "❌ Not Connected"
    print(f"  HTTP Server: {http_status} (PID: {services_status['http_server']['pid'] or 'N/A'})")
    print(f"  HTTP Connection: {http_connected}")
    print(f"  URL: {services_status['http_server']['url']}")
    
    # MCP Service Status
    print(f"\n{BOLD}MCP Service Status:{RESET}")
    mcp_status = "✅ Running" if services_status["mcp_server"]["running"] else "❌ Not Running"
    mcp_connected = "✅ Connected" if services_status["mcp_server"]["connected"] else "❌ Not Connected"
    print(f"  MCP Server: {mcp_status} (PID: {services_status['mcp_server']['pid'] or 'N/A'})")
    print(f"  MCP Connection: {mcp_connected}")
    print(f"  URL: {services_status['mcp_server']['url']}")
    
    # Vector DB Status
    vector_status = "✅ Available" if services_status["vector_available"] else "❌ Not Available" 
    print(f"\n{BOLD}Vector DB Status:{RESET}")
    print(f"  Vector DB Integration: {vector_status}")
    
    # Try to get vector DB version if available
    try:
        from engram.core.memory import VECTOR_DB_NAME, VECTOR_DB_VERSION
        if VECTOR_DB_NAME and VECTOR_DB_VERSION:
            print(f"  Vector DB: {GREEN}{VECTOR_DB_NAME} {VECTOR_DB_VERSION}{RESET}")
        else:
            print(f"  Vector DB: {RED}Not available{RESET}")
    except ImportError:
        print(f"  Vector DB: {RED}Not installed{RESET}")
    except Exception as e:
        print(f"  Vector DB: {YELLOW}Error checking version: {e}{RESET}")
    
    # MCP Capabilities
    if services_status["mcp_server"]["connected"]:
        try:
            mcp_test = test_mcp_connection()
            if mcp_test["success"] and mcp_test["manifest"]:
                manifest = mcp_test["manifest"]
                print(f"\n{BOLD}MCP Capabilities:{RESET}")
                print(f"  Name: {manifest.get('name', 'engram')}")
                print(f"  Version: {manifest.get('version', 'unknown')}")
                
                capabilities = manifest.get("capabilities", {})
                if capabilities:
                    print(f"  Available capabilities:")
                    for name in capabilities.keys():
                        print(f"    - {name}")
        except Exception as e:
            print(f"\n{BOLD}MCP Capabilities:{RESET}")
            print(f"  {RED}Error getting capabilities: {e}{RESET}")
    
    # Footer
    print(f"\n{BOLD}{BLUE}===================================={RESET}\n")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Engram Dual Mode Status Checker")
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--start", action="store_true", help="Start services if not running")
    action_group.add_argument("--restart", action="store_true", help="Restart services")
    action_group.add_argument("--stop", action="store_true", help="Stop running services")
    
    # Service selection
    service_group = parser.add_mutually_exclusive_group()
    service_group.add_argument("--http-only", action="store_true", help="Only check/manage HTTP service")
    service_group.add_argument("--mcp-only", action="store_true", help="Only check/manage MCP service")
    
    # Port configuration
    parser.add_argument("--http-port", type=int, default=8000, help="HTTP service port (default: 8000)")
    parser.add_argument("--mcp-port", type=int, default=8001, help="MCP service port (default: 8001)")
    
    # Other arguments
    parser.add_argument("--client-id", type=str, default="claude", help="Client ID for memory service")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory to store memory data")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Handle actions
    if args.stop:
        stop_services(args.http_only, args.mcp_only)
        return
    
    if args.start or args.restart:
        start_services(
            client_id=args.client_id,
            data_dir=args.data_dir,
            force_restart=args.restart,
            http_only=args.http_only,
            mcp_only=args.mcp_only,
            http_port=args.http_port,
            mcp_port=args.mcp_port
        )
        # Give services time to start
        time.sleep(2)
    
    # Check services status
    services_status = check_services(not args.mcp_only, not args.http_only)
    
    # Compile full results
    results = {
        "services": services_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        display_status_report(services_status)
    
    return results

if __name__ == "__main__":
    main()
