#!/usr/bin/env python3
"""
Mode Detection - Detect and adapt to different Claude operational modes

This module provides functionality to detect whether Claude is running in
execution mode or analysis mode, and adapt behavior accordingly.
"""

import os
import tempfile
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.mode_detection")

def detect_execution_mode() -> str:
    """
    Detect if Claude is in execution or analysis mode.
    
    Returns:
        str: "execution" or "analysis"
    """
    # First check for explicit environment variable
    if os.environ.get("CLAUDE_ANALYSIS_MODE", "") or os.environ.get("CLAUDE_RESTRICTED", ""):
        logger.info("Analysis mode detected via environment variable")
        return "analysis"
    
    # Try a filesystem write test to check for execution permissions
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"test")
        logger.info("Execution mode detected via filesystem write test")
        return "execution"
    except Exception as e:
        logger.warning(f"Filesystem write test failed: {e}")
        return "analysis"

def adapt_to_mode(mode: str) -> Dict[str, Any]:
    """
    Configure behavior based on detected mode.
    
    Args:
        mode: The detected mode ("execution" or "analysis")
        
    Returns:
        Dict with configuration settings for the detected mode
    """
    if mode == "analysis":
        config = {
            "can_execute": False,
            "can_analyze": True,
            "recommend_behavior": "Provide detailed explanation of intended functionality",
            "interaction_style": "descriptive",
            "should_skip_execution": True
        }
        logger.info("Configured for analysis mode")
        return config
    else:
        config = {
            "can_execute": True,
            "can_analyze": True,
            "recommend_behavior": "Execute code and report results",
            "interaction_style": "operational",
            "should_skip_execution": False
        }
        logger.info("Configured for execution mode")
        return config

def get_mode_message(mode: str) -> str:
    """
    Get an appropriate message to display based on the detected mode.
    
    Args:
        mode: The detected mode ("execution" or "analysis")
        
    Returns:
        str: A message explaining the detected mode
    """
    if mode == "analysis":
        return "\033[93mAnalysis mode detected. Running in explanation mode.\033[0m\n" + \
               "\033[94mIn this mode, I will explain how the Engram memory system works\033[0m\n" + \
               "\033[94mbut won't execute operations that modify the filesystem.\033[0m"
    else:
        return "\033[92mExecution mode detected. Running with full capabilities.\033[0m"

def create_mode_info_dict(client_id: str) -> Dict[str, Any]:
    """
    Create a dictionary with complete mode information for this Claude instance.
    
    Args:
        client_id: The ID of this Claude instance
        
    Returns:
        Dict with comprehensive mode information
    """
    mode = detect_execution_mode()
    config = adapt_to_mode(mode)
    
    return {
        "client_id": client_id,
        "mode": mode,
        "capabilities": config,
        "environment": {
            "restricted_mode": bool(os.environ.get("CLAUDE_RESTRICTED", "")),
            "analysis_mode": bool(os.environ.get("CLAUDE_ANALYSIS_MODE", "")),
            "python_executable": os.sys.executable if hasattr(os, "sys") else "unknown"
        }
    }

def save_mode_info(client_id: str, data_dir: str = None) -> str:
    """
    Save mode information to a file for future reference.
    
    Args:
        client_id: The ID of this Claude instance
        data_dir: Optional data directory (defaults to ~/.cmb)
        
    Returns:
        str: Path to the saved file
    """
    if data_dir is None:
        data_dir = os.path.expanduser("~/.cmb")
    
    os.makedirs(data_dir, exist_ok=True)
    mode_info = create_mode_info_dict(client_id)
    
    file_path = os.path.join(data_dir, f"{client_id}_mode_info.json")
    with open(file_path, "w") as f:
        json.dump(mode_info, f, indent=2)
    
    logger.info(f"Saved mode information to {file_path}")
    return file_path

if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    client_id = sys.argv[1] if len(sys.argv) > 1 else "claude_test"
    
    mode = detect_execution_mode()
    print(f"Detected mode: {mode}")
    
    config = adapt_to_mode(mode)
    print(f"Configuration: {json.dumps(config, indent=2)}")
    
    print(get_mode_message(mode))
    
    file_path = save_mode_info(client_id)
    print(f"Saved mode information to {file_path}")