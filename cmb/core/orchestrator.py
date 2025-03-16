#!/usr/bin/env python3
"""
Claude Orchestrator - Manage multiple Claude instances for collaborative tasks

This module provides functionality to orchestrate multiple Claude instances,
assign tasks, and coordinate their activities.
"""

import os
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.orchestrator")

class ClaudeOrchestrator:
    """
    Orchestrate multiple Claude instances for collaborative tasks.
    
    This class manages the lifecycle of multiple Claude instances,
    assigns tasks, coordinates communication, and monitors progress.
    """
    
    def __init__(self, max_instances: int = 3, data_dir: Optional[str] = None):
        """
        Initialize the Claude orchestrator.
        
        Args:
            max_instances: Maximum number of Claude instances to spawn
            data_dir: Directory to store orchestration data
        """
        self.max_instances = max_instances
        self.active_instances = {}
        self.tasks = []
        
        # Set up data directory
        if data_dir is None:
            data_dir = os.path.expanduser("~/.cmb/orchestrator")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load any existing instance data
        self._load_instances()
        
        logger.info(f"Initialized Claude orchestrator with max {max_instances} instances")
    
    def _load_instances(self) -> None:
        """
        Load information about previously spawned instances.
        """
        instance_file = self.data_dir / "instances.json"
        if instance_file.exists():
            try:
                with open(instance_file, "r") as f:
                    self.active_instances = json.load(f)
                logger.info(f"Loaded {len(self.active_instances)} existing instances")
            except Exception as e:
                logger.error(f"Error loading instance data: {e}")
    
    def _save_instances(self) -> None:
        """
        Save information about active instances.
        """
        instance_file = self.data_dir / "instances.json"
        try:
            with open(instance_file, "w") as f:
                json.dump(self.active_instances, f, indent=2)
            logger.info(f"Saved {len(self.active_instances)} instances")
        except Exception as e:
            logger.error(f"Error saving instance data: {e}")
            
    async def spawn_instance(self, role: str, task_description: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Spawn a new Claude instance with a specific role.
        
        Args:
            role: The role for the new instance (e.g., "analyst", "coder")
            task_description: Description of the task to perform
            client_id: Optional specific client ID to use
            
        Returns:
            Dict with information about the spawned instance
        """
        # Check if we've reached the maximum instances
        if len(self.active_instances) >= self.max_instances:
            logger.warning(f"Cannot spawn new instance: maximum of {self.max_instances} reached")
            return {"success": False, "error": "Maximum instances reached"}
        
        # Generate instance ID if not provided
        if client_id is None:
            client_id = f"claude_{role}_{int(time.time())}"
        
        # Check if the instance ID already exists
        if client_id in self.active_instances:
            logger.warning(f"Instance ID {client_id} already exists")
            return {"success": False, "error": "Instance ID already exists"}
        
        # In a real implementation, this would use subprocess or API calls
        # to start a new Claude instance
        logger.info(f"Spawning new Claude instance with ID {client_id}")
        logger.info(f"Role: {role}, Task: {task_description}")
        
        # Record instance information
        self.active_instances[client_id] = {
            "role": role,
            "task": task_description,
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "process_id": None  # Would be set in a real implementation
        }
        
        # Save updated instance data
        self._save_instances()
        
        # For a real implementation, you would launch the process
        try:
            # This is a placeholder - in a real implementation, this would
            # actually spawn a new Claude instance
            cmd = [
                "cat",  # Placeholder for the actual command
                "-",  # Placeholder, would be actual arguments
            ]
            
            # For demonstration only - this doesn't actually work
            # process = subprocess.Popen(cmd)
            # self.active_instances[client_id]["process_id"] = process.pid
            # self._save_instances()
            
            # Create a task file that the spawned instance would read
            task_file = self.data_dir / f"{client_id}_task.json"
            with open(task_file, "w") as f:
                json.dump({
                    "client_id": client_id,
                    "role": role,
                    "task": task_description,
                    "created_at": datetime.now().isoformat()
                }, f, indent=2)
            
            return {
                "success": True,
                "instance_id": client_id,
                "task_file": str(task_file)
            }
            
        except Exception as e:
            logger.error(f"Error spawning Claude instance: {e}")
            # Clean up if spawn failed
            if client_id in self.active_instances:
                del self.active_instances[client_id]
                self._save_instances()
            return {"success": False, "error": str(e)}
    
    async def terminate_instance(self, client_id: str) -> Dict[str, Any]:
        """
        Terminate a running Claude instance.
        
        Args:
            client_id: ID of the instance to terminate
            
        Returns:
            Dict with result of the termination attempt
        """
        if client_id not in self.active_instances:
            logger.warning(f"Cannot terminate unknown instance: {client_id}")
            return {"success": False, "error": "Instance not found"}
        
        instance = self.active_instances[client_id]
        logger.info(f"Terminating Claude instance {client_id}")
        
        # In a real implementation, this would terminate the process
        try:
            # process_id = instance.get("process_id")
            # if process_id:
            #     os.kill(process_id, signal.SIGTERM)
            
            # Update instance status
            instance["status"] = "terminated"
            instance["terminated_at"] = datetime.now().isoformat()
            self._save_instances()
            
            return {"success": True, "instance_id": client_id, "status": "terminated"}
            
        except Exception as e:
            logger.error(f"Error terminating Claude instance: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_task(self, client_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a task to a specific Claude instance.
        
        Args:
            client_id: ID of the target instance
            task: Task details to send
            
        Returns:
            Dict with result of sending the task
        """
        if client_id not in self.active_instances:
            logger.warning(f"Cannot send task to unknown instance: {client_id}")
            return {"success": False, "error": "Instance not found"}
        
        logger.info(f"Sending task to Claude instance {client_id}")
        
        # In a real implementation, this would use some form of IPC
        # or shared memory to send the task to the other instance
        try:
            # Create a task file for the instance to read
            task_file = self.data_dir / f"{client_id}_task_{int(time.time())}.json"
            with open(task_file, "w") as f:
                json.dump(task, f, indent=2)
            
            # Record the task
            self.tasks.append({
                "client_id": client_id,
                "task": task,
                "created_at": datetime.now().isoformat(),
                "status": "sent",
                "task_file": str(task_file)
            })
            
            return {
                "success": True,
                "client_id": client_id,
                "task_file": str(task_file)
            }
            
        except Exception as e:
            logger.error(f"Error sending task to Claude instance: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get status of all managed instances.
        
        Returns:
            Dict with status information for all instances
        """
        # Update status of all instances
        for client_id, instance in self.active_instances.items():
            # In a real implementation, this would check if the process is still running
            # and update the status accordingly
            pass
        
        return {
            "max_instances": self.max_instances,
            "active_count": len(self.active_instances),
            "instances": self.active_instances,
            "tasks": self.tasks,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_instance_info(self, client_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific instance.
        
        Args:
            client_id: ID of the instance to get info for
            
        Returns:
            Dict with instance information
        """
        if client_id not in self.active_instances:
            logger.warning(f"Cannot get info for unknown instance: {client_id}")
            return {"success": False, "error": "Instance not found"}
        
        # Get instance information
        instance = self.active_instances[client_id]
        
        # Get all tasks for this instance
        instance_tasks = [t for t in self.tasks if t["client_id"] == client_id]
        
        return {
            "success": True,
            "instance": instance,
            "tasks": instance_tasks,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self) -> Dict[str, Any]:
        """
        Terminate all instances and clean up resources.
        
        Returns:
            Dict with cleanup results
        """
        logger.info("Cleaning up all Claude instances")
        
        results = {
            "terminated": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Terminate all instances
        for client_id in list(self.active_instances.keys()):
            try:
                result = await self.terminate_instance(client_id)
                if result.get("success", False):
                    results["terminated"].append(client_id)
                else:
                    results["failed"].append({
                        "client_id": client_id,
                        "error": result.get("error", "Unknown error")
                    })
            except Exception as e:
                logger.error(f"Error terminating instance {client_id}: {e}")
                results["failed"].append({
                    "client_id": client_id,
                    "error": str(e)
                })
        
        return results

if __name__ == "__main__":
    # Simple command-line interface for testing
    import asyncio
    import sys
    
    async def main():
        orchestrator = ClaudeOrchestrator(max_instances=3)
        
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "spawn" and len(sys.argv) > 3:
                role = sys.argv[2]
                task = sys.argv[3]
                result = await orchestrator.spawn_instance(role, task)
                print(json.dumps(result, indent=2))
                
            elif command == "terminate" and len(sys.argv) > 2:
                client_id = sys.argv[2]
                result = await orchestrator.terminate_instance(client_id)
                print(json.dumps(result, indent=2))
                
            elif command == "status":
                result = await orchestrator.get_status()
                print(json.dumps(result, indent=2))
                
            elif command == "info" and len(sys.argv) > 2:
                client_id = sys.argv[2]
                result = await orchestrator.get_instance_info(client_id)
                print(json.dumps(result, indent=2))
                
            elif command == "cleanup":
                result = await orchestrator.cleanup()
                print(json.dumps(result, indent=2))
                
            else:
                print(f"Unknown command: {command}")
                print("Available commands: spawn, terminate, status, info, cleanup")
        else:
            print("Available commands: spawn, terminate, status, info, cleanup")
    
    asyncio.run(main())