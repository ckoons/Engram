#!/usr/bin/env python3
"""
Claude-to-Claude Communication System

A structured communication layer for Claude instances to share information
and coordinate with each other through persistent memory.

This module enables:
1. Common handoff space for all Claude instances
2. Direct communication channels between specific Claude instances
3. Working context spaces for project collaboration
4. Standardized message format and exchange protocols
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.claude_comm")

class ClaudeComm:
    """
    Communication system for Claude instances to share information and coordinate.
    
    Features:
    - Common handoff space for broadcasts and coordination
    - Direct communication channels between specific Claude instances
    - Working context spaces for project collaboration
    - Standardized message format and exchange protocols
    """
    
    def __init__(self, client_id: str = "claude", data_dir: Optional[str] = None):
        """
        Initialize the Claude communication system.
        
        Args:
            client_id: Unique identifier for this Claude instance
            data_dir: Directory to store communication data (default: ~/.cmb/claude_comm)
        """
        self.client_id = client_id
        
        # Set up base data directory
        if data_dir:
            self.base_dir = Path(data_dir) / "claude_comm"
        else:
            self.base_dir = Path(os.path.expanduser("~/.cmb/claude_comm"))
        
        # Create the base directory
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize channel directories
        self.channels = {
            "handoff": self.base_dir / "handoff",  # Common handoff space
            "direct": self.base_dir / "direct",    # Direct messaging channels
            "context": self.base_dir / "context",  # Working context spaces
        }
        
        # Create channel directories
        for channel_dir in self.channels.values():
            channel_dir.mkdir(exist_ok=True)
            
        # Message types
        self.message_types = [
            "handoff",      # Session handoff to another Claude
            "query",        # Question or information request
            "response",     # Response to a query
            "update",       # Status update or notification
            "thinking",     # Thought process or reasoning
            "action",       # Request for action or notification of action
            "memory"        # Important memory to store
        ]
        
        # Priority levels
        self.priority_levels = {
            1: "Low - General information",
            2: "Normal - Standard communication",
            3: "Medium - Important information",
            4: "High - Requires attention",
            5: "Critical - Urgent action needed"
        }
    
    async def send_handoff(self, content: str, context: str = "", priority: int = 3) -> str:
        """
        Send a message to the common handoff space for all Claude instances.
        
        Args:
            content: The message content
            context: Optional context information
            priority: Importance level (1-5)
            
        Returns:
            Message ID if successful, empty string otherwise
        """
        return await self.send_message(
            content=content,
            recipient="all",
            message_type="handoff",
            context=context,
            priority=priority
        )
    
    async def send_message(self, 
                          content: str, 
                          recipient: str = "all", 
                          message_type: str = "handoff", 
                          context: str = "",
                          priority: int = 2,
                          action: str = "") -> str:
        """
        Send a message to a specific Claude instance or broadcast to all.
        
        Args:
            content: The message content
            recipient: Target Claude instance ID or "all" for broadcast
            message_type: Type of message (handoff, query, response, etc.)
            context: Optional context information
            priority: Importance level (1-5)
            action: Optional requested action
            
        Returns:
            Message ID if successful, empty string otherwise
        """
        try:
            # Validate message type
            if message_type not in self.message_types:
                logger.warning(f"Invalid message type: {message_type}, using 'handoff'")
                message_type = "handoff"
                
            # Validate priority
            priority = max(1, min(5, priority))
            
            # Generate message ID
            timestamp = int(time.time())
            message_id = f"{message_type}-{timestamp}-{hash(content) % 10000}"
            
            # Determine channel
            if recipient == "all":
                channel_dir = self.channels["handoff"]
                file_path = channel_dir / f"{message_id}.json"
            else:
                channel_dir = self.channels["direct"]
                # Create a sorted key for direct messages to ensure consistency
                participants = sorted([self.client_id, recipient])
                direct_channel = f"{participants[0]}_{participants[1]}"
                
                # Create the direct channel directory if it doesn't exist
                direct_channel_path = channel_dir / direct_channel
                direct_channel_path.mkdir(exist_ok=True)
                
                file_path = direct_channel_path / f"{message_id}.json"
            
            # Create the message
            message = {
                "id": message_id,
                "sender": self.client_id,
                "recipient": recipient,
                "timestamp": datetime.now().isoformat(),
                "type": message_type,
                "priority": priority,
                "content": content,
                "context": context,
                "action": action,
                "read_by": [self.client_id],  # Sender has already "read" the message
                "replied": False
            }
            
            # Write the message to file
            with open(file_path, "w") as f:
                json.dump(message, f, indent=2)
                
            logger.info(f"Sent message {message_id} from {self.client_id} to {recipient}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return ""
    
    async def get_messages(self, 
                         sender: str = None, 
                         recipient: str = None,
                         message_type: str = None,
                         min_priority: int = 1,
                         unread_only: bool = False,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get messages from the handoff space or direct channels.
        
        Args:
            sender: Filter by sender Claude ID
            recipient: Filter by recipient Claude ID
            message_type: Filter by message type
            min_priority: Minimum priority level
            unread_only: Only return unread messages
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            messages = []
            
            # Check handoff space for broadcasts
            handoff_dir = self.channels["handoff"]
            for file_path in handoff_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        message = json.load(f)
                        
                    # Apply filters
                    if sender and message["sender"] != sender:
                        continue
                        
                    if recipient and message["recipient"] != recipient and message["recipient"] != "all":
                        continue
                        
                    if message_type and message["type"] != message_type:
                        continue
                        
                    if message["priority"] < min_priority:
                        continue
                        
                    if unread_only and self.client_id in message.get("read_by", []):
                        continue
                        
                    messages.append(message)
                except Exception as e:
                    logger.error(f"Error parsing message file {file_path}: {e}")
            
            # Check direct message channels for this client
            direct_dir = self.channels["direct"]
            for channel_dir in direct_dir.glob(f"*{self.client_id}*"):
                # This directory should contain direct messages to/from this client
                for file_path in channel_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            message = json.load(f)
                            
                        # Apply filters
                        if sender and message["sender"] != sender:
                            continue
                            
                        if recipient and message["recipient"] != recipient:
                            continue
                            
                        if message_type and message["type"] != message_type:
                            continue
                            
                        if message["priority"] < min_priority:
                            continue
                            
                        if unread_only and self.client_id in message.get("read_by", []):
                            continue
                            
                        messages.append(message)
                    except Exception as e:
                        logger.error(f"Error parsing message file {file_path}: {e}")
            
            # Sort by timestamp (newest first) and priority
            messages.sort(key=lambda x: (
                -x.get("priority", 0),
                x.get("timestamp", "")
            ), reverse=True)
            
            # Limit results
            messages = messages[:limit]
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    async def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read by this Claude instance.
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            Boolean indicating success
        """
        try:
            # Find the message file
            message_path = None
            
            # Check handoff space
            handoff_dir = self.channels["handoff"]
            potential_path = handoff_dir / f"{message_id}.json"
            if potential_path.exists():
                message_path = potential_path
            
            # Check direct message channels
            if not message_path:
                direct_dir = self.channels["direct"]
                for channel_dir in direct_dir.glob(f"*{self.client_id}*"):
                    potential_path = channel_dir / f"{message_id}.json"
                    if potential_path.exists():
                        message_path = potential_path
                        break
            
            if not message_path:
                logger.warning(f"Message {message_id} not found")
                return False
            
            # Read the message
            with open(message_path, "r") as f:
                message = json.load(f)
            
            # Mark as read
            if "read_by" not in message:
                message["read_by"] = []
                
            if self.client_id not in message["read_by"]:
                message["read_by"].append(self.client_id)
                
                # Write back to file
                with open(message_path, "w") as f:
                    json.dump(message, f, indent=2)
                
                logger.info(f"Marked message {message_id} as read by {self.client_id}")
                return True
            else:
                # Already marked as read
                return True
                
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    async def mark_as_replied(self, message_id: str) -> bool:
        """
        Mark a message as replied to by this Claude instance.
        
        Args:
            message_id: ID of the message to mark as replied
            
        Returns:
            Boolean indicating success
        """
        try:
            # Find the message file
            message_path = None
            
            # Check handoff space
            handoff_dir = self.channels["handoff"]
            potential_path = handoff_dir / f"{message_id}.json"
            if potential_path.exists():
                message_path = potential_path
            
            # Check direct message channels
            if not message_path:
                direct_dir = self.channels["direct"]
                for channel_dir in direct_dir.glob(f"*{self.client_id}*"):
                    potential_path = channel_dir / f"{message_id}.json"
                    if potential_path.exists():
                        message_path = potential_path
                        break
            
            if not message_path:
                logger.warning(f"Message {message_id} not found")
                return False
            
            # Read the message
            with open(message_path, "r") as f:
                message = json.load(f)
            
            # Mark as replied
            message["replied"] = True
            message["replied_by"] = self.client_id
            message["replied_at"] = datetime.now().isoformat()
            
            # Write back to file
            with open(message_path, "w") as f:
                json.dump(message, f, indent=2)
            
            logger.info(f"Marked message {message_id} as replied by {self.client_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error marking message as replied: {e}")
            return False
    
    async def create_context_space(self, context_name: str, description: str = "") -> str:
        """
        Create a new working context space for sharing project information.
        
        Args:
            context_name: Name of the context space
            description: Optional description
            
        Returns:
            Context space ID if successful, empty string otherwise
        """
        try:
            # Generate a context ID from the name
            context_id = f"context-{int(time.time())}-{context_name.lower().replace(' ', '_')}"
            
            # Create the context directory
            context_dir = self.channels["context"] / context_id
            context_dir.mkdir(exist_ok=True)
            
            # Create metadata file
            metadata = {
                "id": context_id,
                "name": context_name,
                "description": description,
                "created_by": self.client_id,
                "created_at": datetime.now().isoformat(),
                "participants": [self.client_id],
                "message_count": 0
            }
            
            metadata_path = context_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Created context space {context_id} ({context_name})")
            return context_id
            
        except Exception as e:
            logger.error(f"Error creating context space: {e}")
            return ""
    
    async def list_context_spaces(self) -> List[Dict[str, Any]]:
        """
        List all available context spaces.
        
        Returns:
            List of context space metadata dictionaries
        """
        try:
            context_spaces = []
            
            context_dir = self.channels["context"]
            for space_dir in context_dir.glob("context-*"):
                if space_dir.is_dir():
                    metadata_path = space_dir / "metadata.json"
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                                context_spaces.append(metadata)
                        except Exception as e:
                            logger.error(f"Error parsing context space metadata {metadata_path}: {e}")
            
            # Sort by creation time (newest first)
            context_spaces.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return context_spaces
            
        except Exception as e:
            logger.error(f"Error listing context spaces: {e}")
            return []
    
    async def send_context_message(self, 
                                  context_id: str, 
                                  content: str,
                                  message_type: str = "update",
                                  priority: int = 2,
                                  action: str = "") -> str:
        """
        Send a message to a context space.
        
        Args:
            context_id: ID of the context space
            content: Message content
            message_type: Type of message
            priority: Importance level (1-5)
            action: Optional requested action
            
        Returns:
            Message ID if successful, empty string otherwise
        """
        try:
            # Validate context space
            context_dir = self.channels["context"] / context_id
            if not context_dir.exists() or not context_dir.is_dir():
                logger.warning(f"Context space {context_id} not found")
                return ""
            
            # Read metadata to verify participation
            metadata_path = context_dir / "metadata.json"
            if not metadata_path.exists():
                logger.warning(f"Context space {context_id} metadata not found")
                return ""
                
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Add this client to participants if not already included
            if self.client_id not in metadata["participants"]:
                metadata["participants"].append(self.client_id)
                
                # Update metadata
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
            
            # Validate message type
            if message_type not in self.message_types:
                logger.warning(f"Invalid message type: {message_type}, using 'update'")
                message_type = "update"
                
            # Validate priority
            priority = max(1, min(5, priority))
            
            # Generate message ID
            timestamp = int(time.time())
            message_id = f"{message_type}-{timestamp}-{hash(content) % 10000}"
            
            # Create the message
            message = {
                "id": message_id,
                "sender": self.client_id,
                "context_id": context_id,
                "timestamp": datetime.now().isoformat(),
                "type": message_type,
                "priority": priority,
                "content": content,
                "action": action,
                "read_by": [self.client_id],  # Sender has already "read" the message
                "replied": False
            }
            
            # Write the message to file
            message_path = context_dir / f"{message_id}.json"
            with open(message_path, "w") as f:
                json.dump(message, f, indent=2)
            
            # Update message count in metadata
            metadata["message_count"] += 1
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Sent message {message_id} to context space {context_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending context message: {e}")
            return ""
    
    async def get_context_messages(self, 
                                 context_id: str,
                                 message_type: str = None,
                                 min_priority: int = 1,
                                 unread_only: bool = False,
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get messages from a context space.
        
        Args:
            context_id: ID of the context space
            message_type: Filter by message type
            min_priority: Minimum priority level
            unread_only: Only return unread messages
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        try:
            # Validate context space
            context_dir = self.channels["context"] / context_id
            if not context_dir.exists() or not context_dir.is_dir():
                logger.warning(f"Context space {context_id} not found")
                return []
            
            messages = []
            
            # Get all message files
            for file_path in context_dir.glob("*.json"):
                # Skip metadata file
                if file_path.name == "metadata.json":
                    continue
                    
                try:
                    with open(file_path, "r") as f:
                        message = json.load(f)
                        
                    # Apply filters
                    if message_type and message["type"] != message_type:
                        continue
                        
                    if message["priority"] < min_priority:
                        continue
                        
                    if unread_only and self.client_id in message.get("read_by", []):
                        continue
                        
                    messages.append(message)
                except Exception as e:
                    logger.error(f"Error parsing message file {file_path}: {e}")
            
            # Sort by timestamp (newest first) and priority
            messages.sort(key=lambda x: (
                -x.get("priority", 0),
                x.get("timestamp", "")
            ), reverse=True)
            
            # Limit results
            messages = messages[:limit]
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting context messages: {e}")
            return []
    
    async def add_quickmem_functions(self) -> Dict[str, Any]:
        """
        Get a dictionary of quick memory functions for use in the Python interpreter.
        These can be imported into the global namespace for easier use.
        
        Returns:
            Dictionary of function names to functions
        """
        # Create wrapper functions with more intuitive names
        funcs = {
            # Claude-to-Claude communication functions
            "send_message": self.send_message,
            "get_messages": self.get_messages,
            "mark_read": self.mark_as_read,
            "mark_replied": self.mark_as_replied,
            
            # Handoff functions
            "handoff": self.send_handoff,
            
            # Context space functions
            "create_context": self.create_context_space,
            "list_contexts": self.list_context_spaces,
            "send_to_context": self.send_context_message,
            "get_context_messages": self.get_context_messages,
            
            # Short aliases for common functions
            "sm": self.send_message,
            "gm": self.get_messages,
            "h": self.send_handoff,
            "cc": self.create_context_space,
            "lc": self.list_context_spaces,
            "sc": self.send_context_message,
            "gc": self.get_context_messages,
        }
        
        return funcs

# Helper function to initialize the communication system
async def initialize_claude_comm(client_id: str = None, data_dir: str = None) -> ClaudeComm:
    """
    Initialize the Claude communication system with environment-aware configuration.
    
    Args:
        client_id: Client ID (defaults to CMB_CLIENT_ID environment variable or "claude")
        data_dir: Data directory (defaults to CMB_DATA_DIR environment variable or "~/.cmb")
        
    Returns:
        Initialized ClaudeComm instance
    """
    # Get client ID from environment or parameter
    if client_id is None:
        client_id = os.environ.get("CMB_CLIENT_ID", "claude")
        
    # Get data directory from environment or parameter
    if data_dir is None:
        data_dir = os.environ.get("CMB_DATA_DIR", os.path.expanduser("~/.cmb"))
        
    # Initialize communication system
    comm = ClaudeComm(client_id=client_id, data_dir=data_dir)
    
    return comm