#!/usr/bin/env python3
"""
comm_quickmem - Quick access functions for Claude-to-Claude communication

This module extends the quickmem functionality to include Claude-to-Claude
communication capabilities, allowing multiple Claude instances to exchange
messages and coordinate with each other.

Usage:
    from cmb.cli.comm_quickmem import send_message, get_messages, create_context
    # Or use the ultra-short aliases
    from cmb.cli.comm_quickmem import sm, gm, cc
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional

try:
    # Try to import from cmb namespace
    from cmb.core.claude_comm import ClaudeComm, initialize_claude_comm
except ImportError:
    try:
        # Fall back to engram namespace
        from engram.core.claude_comm import ClaudeComm, initialize_claude_comm
    except ImportError:
        print("Error: Unable to import Claude communication modules.")
        print("Make sure you're running from project root or have it installed.")
        raise

# Get client ID from environment variable
client_id = os.environ.get("CMB_CLIENT_ID", "claude")
data_dir = os.environ.get("CMB_DATA_DIR", os.path.expanduser("~/.cmb"))

# Initialize Claude communication system
claude_comm = None

try:
    # Create event loop if needed
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Initialize Claude communication
    claude_comm = loop.run_until_complete(initialize_claude_comm(client_id=client_id, data_dir=data_dir))
    
except Exception as e:
    print(f"Warning: Error initializing Claude communication system: {e}")

# Core communication functions

def send_message(content: str, recipient: str = "all", message_type: str = "handoff", context: str = "", priority: int = 2):
    """
    Send a message to another Claude instance or broadcast to all.
    
    Args:
        content: The message content
        recipient: Target Claude instance ID or "all" for broadcast
        message_type: Type of message (handoff, query, response, etc.)
        context: Optional context information
        priority: Importance level (1-5)
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.send_message(
            content=content,
            recipient=recipient,
            message_type=message_type,
            context=context,
            priority=priority
        ))
        print(f"✅ Message sent: {result}")
        return result
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return None

def get_messages(sender: str = None, recipient: str = None, message_type: str = None, 
                unread_only: bool = True, min_priority: int = 1, limit: int = 5):
    """
    Get messages from other Claude instances.
    
    Args:
        sender: Filter by sender Claude ID
        recipient: Filter by recipient Claude ID
        message_type: Filter by message type
        unread_only: Only return unread messages
        min_priority: Minimum priority level
        limit: Maximum number of messages to return
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        messages = loop.run_until_complete(claude_comm.get_messages(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            min_priority=min_priority,
            unread_only=unread_only,
            limit=limit
        ))
        
        if not messages:
            print("ℹ️ No messages found")
            return []
        
        print(f"📨 Found {len(messages)} messages:")
        for i, msg in enumerate(messages):
            sender = msg.get("sender", "unknown")
            timestamp = msg.get("timestamp", "")[:16]
            msg_type = msg.get("type", "")
            priority = "★" * msg.get("priority", 1)
            content = msg.get("content", "")
            print(f"{i+1}. [{priority}] {timestamp} FROM {sender} ({msg_type}): {content[:80]}")
            
            # Mark as read
            loop.run_until_complete(claude_comm.mark_as_read(msg["id"]))
            
        return messages
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        return []

def mark_as_read(message_id: str):
    """
    Mark a message as read.
    
    Args:
        message_id: ID of the message to mark as read
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return False
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.mark_as_read(message_id))
        if result:
            print(f"✅ Marked message {message_id} as read")
        return result
    except Exception as e:
        print(f"❌ Error marking message as read: {e}")
        return False

def mark_as_replied(message_id: str):
    """
    Mark a message as replied to.
    
    Args:
        message_id: ID of the message to mark as replied
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return False
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.mark_as_replied(message_id))
        if result:
            print(f"✅ Marked message {message_id} as replied")
        return result
    except Exception as e:
        print(f"❌ Error marking message as replied: {e}")
        return False

def handoff(content: str, context: str = "", priority: int = 3):
    """
    Send a handoff message to all Claude instances.
    
    Args:
        content: The handoff message
        context: Optional context information
        priority: Importance level (1-5)
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.send_handoff(
            content=content,
            context=context,
            priority=priority
        ))
        print(f"✅ Handoff sent: {result}")
        return result
    except Exception as e:
        print(f"❌ Error sending handoff: {e}")
        return None

def respond_to(message, response, priority: int = 2):
    """
    Respond to a specific message.
    
    Args:
        message: The message to respond to (either message object or ID)
        response: The response content
        priority: Importance level (1-5)
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        message_id = message.get("id") if isinstance(message, dict) else message
        sender = message.get("sender") if isinstance(message, dict) else "unknown"
        
        # Send response
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.send_message(
            content=response,
            recipient=sender,
            message_type="response",
            context=f"In response to message {message_id}",
            priority=priority
        ))
        
        # Mark original message as replied
        if message_id:
            loop.run_until_complete(claude_comm.mark_as_replied(message_id))
            
        print(f"✅ Response sent to {sender}: {result}")
        return result
    except Exception as e:
        print(f"❌ Error sending response: {e}")
        return None

# Context space functions

def create_context(name: str, description: str = ""):
    """
    Create a new context space for collaboration.
    
    Args:
        name: Name of the context space
        description: Optional description
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.create_context_space(
            context_name=name,
            description=description
        ))
        print(f"✅ Created context space: {result}")
        return result
    except Exception as e:
        print(f"❌ Error creating context space: {e}")
        return None

def list_contexts():
    """List all available context spaces."""
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        spaces = loop.run_until_complete(claude_comm.list_context_spaces())
        
        if not spaces:
            print("ℹ️ No context spaces found")
            return []
        
        print(f"📋 Found {len(spaces)} context spaces:")
        for i, space in enumerate(spaces):
            name = space.get("name", "unnamed")
            created = space.get("created_at", "")[:16]
            creator = space.get("created_by", "unknown")
            msg_count = space.get("message_count", 0)
            print(f"{i+1}. {name} (created by {creator} on {created}, {msg_count} messages)")
            
        return spaces
    except Exception as e:
        print(f"❌ Error listing context spaces: {e}")
        return []

def send_to_context(context_id: str, content: str, message_type: str = "update", priority: int = 2):
    """
    Send a message to a context space.
    
    Args:
        context_id: ID of the context space
        content: Message content
        message_type: Type of message
        priority: Importance level (1-5)
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(claude_comm.send_context_message(
            context_id=context_id,
            content=content,
            message_type=message_type,
            priority=priority
        ))
        print(f"✅ Message sent to context space: {result}")
        return result
    except Exception as e:
        print(f"❌ Error sending message to context space: {e}")
        return None

def get_context_messages(context_id: str, message_type: str = None, 
                        unread_only: bool = False, min_priority: int = 1, limit: int = 10):
    """
    Get messages from a context space.
    
    Args:
        context_id: ID of the context space
        message_type: Filter by message type
        unread_only: Only return unread messages
        min_priority: Minimum priority level
        limit: Maximum number of messages to return
    """
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        loop = asyncio.get_event_loop()
        messages = loop.run_until_complete(claude_comm.get_context_messages(
            context_id=context_id,
            message_type=message_type,
            min_priority=min_priority,
            unread_only=unread_only,
            limit=limit
        ))
        
        if not messages:
            print(f"ℹ️ No messages found in context space {context_id}")
            return []
        
        print(f"📨 Found {len(messages)} messages in context space:")
        for i, msg in enumerate(messages):
            sender = msg.get("sender", "unknown")
            timestamp = msg.get("timestamp", "")[:16]
            msg_type = msg.get("type", "")
            priority = "★" * msg.get("priority", 1)
            content = msg.get("content", "")
            print(f"{i+1}. [{priority}] {timestamp} FROM {sender} ({msg_type}): {content[:80]}")
            
            # Mark as read
            if unread_only and msg.get("id"):
                loop.run_until_complete(claude_comm.mark_as_read(msg["id"]))
            
        return messages
    except Exception as e:
        print(f"❌ Error getting context messages: {e}")
        return []

# Status and information

def communication_status():
    """Get status information about the Claude Communication system."""
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        # Get client ID
        my_id = claude_comm.client_id
        print(f"🆔 Client ID: {my_id}")
        
        # Check for unread messages
        loop = asyncio.get_event_loop()
        unread = loop.run_until_complete(claude_comm.get_messages(unread_only=True, limit=1))
        if unread:
            print(f"📨 You have unread messages. Use get_messages() to view them.")
        else:
            print("📭 No unread messages.")
            
        # List available context spaces
        spaces = loop.run_until_complete(claude_comm.list_context_spaces())
        if spaces:
            print(f"🗂️ {len(spaces)} context spaces available. Use list_contexts() to view them.")
        else:
            print("🗂️ No context spaces available. Use create_context() to create one.")
            
        return {
            "client_id": my_id,
            "has_unread": bool(unread),
            "context_spaces_count": len(spaces)
        }
    except Exception as e:
        print(f"❌ Error getting communication status: {e}")
        return None

def whoami():
    """Get information about your Claude identity in the communication system."""
    if claude_comm is None:
        print("⚠️ Claude Communication system not initialized")
        return None
    
    try:
        my_id = claude_comm.client_id
        print(f"🆔 You are Claude instance: {my_id}")
        
        # Check for any messages I've sent or received
        loop = asyncio.get_event_loop()
        sent = loop.run_until_complete(claude_comm.get_messages(sender=my_id, limit=1))
        received = loop.run_until_complete(claude_comm.get_messages(recipient=my_id, limit=1))
        
        if sent:
            print(f"📤 You've sent messages in this system.")
        if received:
            print(f"📥 You've received messages in this system.")
        
        return {
            "client_id": my_id,
            "has_sent": bool(sent),
            "has_received": bool(received)
        }
    except Exception as e:
        print(f"❌ Error getting identity information: {e}")
        return None

# Ultra-short aliases
sm = send_message    # Send message
gm = get_messages    # Get messages
ho = handoff         # Send handoff
mr = mark_as_read    # Mark as read
mp = mark_as_replied # Mark as replied (processed)
rt = respond_to      # Respond to message

cc = create_context  # Create context space
lc = list_contexts   # List context spaces
sc = send_to_context # Send to context
gc = get_context_messages # Get context messages

cs = communication_status # Communication status
wi = whoami         # Who am I

# Export the functions
__all__ = [
    "send_message", "get_messages", "mark_as_read", "mark_as_replied", 
    "handoff", "respond_to", "create_context", "list_contexts", 
    "send_to_context", "get_context_messages", "communication_status", "whoami",
    
    # Ultra-short aliases
    "sm", "gm", "ho", "mr", "mp", "rt", "cc", "lc", "sc", "gc", "cs", "wi"
]