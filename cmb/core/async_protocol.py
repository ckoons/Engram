#!/usr/bin/env python3
"""
Asynchronous Message Protocol for AI Communication

This module defines a standardized protocol for asynchronous message delivery
between AI instances, supporting:
- Message persistence until delivery
- Lifecycle-aware messaging (startup, progress, completion, shutdown)
- Version negotiation for backward compatibility
- Priority and TTL (Time To Live) for messages
- Acknowledgment and delivery guarantees
"""

import os
import json
import time
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.async_protocol")

# Protocol version
PROTOCOL_VERSION = "1.0.0"

class MessageType(Enum):
    """Types of messages that can be exchanged between AI instances."""
    # Lifecycle messages
    STARTUP = "startup"        # AI is starting and announcing its presence
    SHUTDOWN = "shutdown"      # AI is shutting down gracefully
    HEARTBEAT = "heartbeat"    # Regular indication that AI is still alive
    
    # Task messages
    TASK_REQUEST = "task_request"    # Request for a task to be performed
    TASK_PROGRESS = "task_progress"  # Progress update on task execution
    TASK_RESULT = "task_result"      # Final result of a task
    TASK_CANCEL = "task_cancel"      # Request to cancel a task
    
    # Communication messages
    QUERY = "query"            # Information request
    RESPONSE = "response"      # Response to a query
    BROADCAST = "broadcast"    # Message for all AIs
    DIRECT = "direct"          # Direct message for specific AI
    
    # System messages
    ERROR = "error"            # Error notification
    WARNING = "warning"        # Warning message
    INFO = "info"              # Informational message
    
    # Special messages
    CAPABILITY = "capability"  # Announce capabilities for negotiation
    HANDOFF = "handoff"        # Transfer responsibility of a conversation
    CONTEXT = "context"        # Shared context information


class MessagePriority(Enum):
    """Priority levels for message delivery."""
    LOW = 1       # Background, non-time-sensitive
    NORMAL = 2    # Standard priority
    HIGH = 3      # Important, preferential handling
    URGENT = 4    # Time-sensitive, deliver ASAP
    CRITICAL = 5  # Highest priority, must be delivered immediately


class MessageStatus(Enum):
    """Status of a message in the delivery lifecycle."""
    CREATED = "created"        # Message has been created
    QUEUED = "queued"          # Message is queued for delivery
    DELIVERED = "delivered"    # Message has been delivered
    READ = "read"              # Message has been read by recipient
    ACKNOWLEDGED = "acked"     # Message has been acknowledged
    PROCESSED = "processed"    # Message has been fully processed
    EXPIRED = "expired"        # Message has expired (TTL reached)
    FAILED = "failed"          # Message delivery failed
    CANCELLED = "cancelled"    # Message was cancelled


class AsyncMessage:
    """
    Represents an asynchronous message in the AI communication protocol.
    
    This class encapsulates a message sent between AI instances with metadata
    for tracking delivery, status, and relationship to other messages.
    """
    
    def __init__(
        self,
        content: Any,
        sender_id: str,
        recipient_id: str = "all",
        message_type: Union[MessageType, str] = MessageType.DIRECT,
        priority: Union[MessagePriority, int] = MessagePriority.NORMAL,
        message_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new asynchronous message.
        
        Args:
            content: The message content (can be string, dict, or serializable object)
            sender_id: ID of the sending AI instance
            recipient_id: ID of the recipient AI instance (or "all" for broadcast)
            message_type: Type of message (use MessageType enum)
            priority: Priority level (use MessagePriority enum)
            message_id: Optional custom message ID (UUID generated if not provided)
            parent_id: Optional ID of the parent message (for threaded conversations)
            thread_id: Optional ID of the conversation thread
            ttl_seconds: Time-to-live in seconds (None for no expiration)
            metadata: Optional additional metadata for the message
        """
        # Core message properties
        self.message_id = message_id or f"{uuid.uuid4()}"
        self.content = content
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        
        # Message type (convert string to enum if needed)
        if isinstance(message_type, str):
            try:
                self.message_type = MessageType[message_type.upper()]
            except KeyError:
                logger.warning(f"Unknown message type: {message_type}, using DIRECT")
                self.message_type = MessageType.DIRECT
        else:
            self.message_type = message_type
        
        # Priority (convert int to enum if needed)
        if isinstance(priority, int):
            try:
                self.priority = MessagePriority(min(max(priority, 1), 5))
            except ValueError:
                logger.warning(f"Invalid priority: {priority}, using NORMAL")
                self.priority = MessagePriority.NORMAL
        else:
            self.priority = priority
        
        # Message relationships
        self.parent_id = parent_id
        self.thread_id = thread_id or self.message_id  # Default to message_id if no thread specified
        
        # Lifecycle properties
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.status = MessageStatus.CREATED
        self.status_history = [
            {"status": MessageStatus.CREATED.value, "timestamp": self.created_at}
        ]
        
        # Protocol information
        self.protocol_version = PROTOCOL_VERSION
        
        # Time-to-live
        self.ttl_seconds = ttl_seconds
        if ttl_seconds is not None:
            self.expires_at = (datetime.fromisoformat(self.created_at) + 
                               timedelta(seconds=ttl_seconds)).isoformat()
        else:
            self.expires_at = None
        
        # Additional metadata
        self.metadata = metadata or {}
    
    def update_status(self, status: Union[MessageStatus, str]) -> None:
        """
        Update the message status and record in history.
        
        Args:
            status: New status (MessageStatus enum or string)
        """
        # Convert string to enum if needed
        if isinstance(status, str):
            try:
                status = MessageStatus[status.upper()]
            except KeyError:
                logger.warning(f"Unknown status: {status}, using current status")
                return
        
        # Update status
        self.status = status
        self.updated_at = datetime.now().isoformat()
        
        # Add to history
        self.status_history.append({
            "status": status.value,
            "timestamp": self.updated_at
        })
    
    def is_expired(self) -> bool:
        """
        Check if the message has expired based on TTL.
        
        Returns:
            bool: True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        
        return datetime.now() > datetime.fromisoformat(self.expires_at)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary representation.
        
        Returns:
            Dict representation of the message
        """
        return {
            "message_id": self.message_id,
            "content": self.content,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "parent_id": self.parent_id,
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "status_history": self.status_history,
            "protocol_version": self.protocol_version,
            "ttl_seconds": self.ttl_seconds,
            "expires_at": self.expires_at,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert message to JSON string.
        
        Returns:
            JSON string representation of the message
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AsyncMessage':
        """
        Create a message from dictionary representation.
        
        Args:
            data: Dictionary representation of a message
            
        Returns:
            AsyncMessage object
        """
        # Create a message with required fields
        msg = cls(
            content=data["content"],
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id", "all"),
            message_type=data.get("message_type", MessageType.DIRECT.value),
            priority=data.get("priority", MessagePriority.NORMAL.value),
            message_id=data.get("message_id"),
            parent_id=data.get("parent_id"),
            thread_id=data.get("thread_id"),
            ttl_seconds=data.get("ttl_seconds"),
            metadata=data.get("metadata", {})
        )
        
        # Set additional fields if present
        if "created_at" in data:
            msg.created_at = data["created_at"]
        if "updated_at" in data:
            msg.updated_at = data["updated_at"]
        if "status" in data:
            msg.status = MessageStatus(data["status"])
        if "status_history" in data:
            msg.status_history = data["status_history"]
        if "protocol_version" in data:
            msg.protocol_version = data["protocol_version"]
        if "expires_at" in data:
            msg.expires_at = data["expires_at"]
        
        return msg
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AsyncMessage':
        """
        Create a message from JSON string.
        
        Args:
            json_str: JSON string representation of a message
            
        Returns:
            AsyncMessage object
        """
        return cls.from_dict(json.loads(json_str))


class MessageQueue:
    """
    Queue for handling asynchronous messages.
    
    This class provides functionality for enqueueing, retrieving,
    and managing messages between AI instances.
    """
    
    def __init__(self, data_dir: Optional[str] = None, client_id: Optional[str] = None):
        """
        Initialize the message queue.
        
        Args:
            data_dir: Directory to store messages (default: ~/.cmb/async_messages)
            client_id: ID of this client (used for filtering messages)
        """
        # Set up data directory
        if data_dir is None:
            data_dir = os.path.expanduser("~/.cmb/async_messages")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Store client ID
        self.client_id = client_id
        
        # Create directories for different message states
        self.pending_dir = self.data_dir / "pending"
        self.delivered_dir = self.data_dir / "delivered"
        self.processed_dir = self.data_dir / "processed"
        self.expired_dir = self.data_dir / "expired"
        
        # Create directories
        self.pending_dir.mkdir(exist_ok=True)
        self.delivered_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        self.expired_dir.mkdir(exist_ok=True)
        
        # Load pending messages
        self.pending_messages = {}
        self._load_pending_messages()
        
        logger.info(f"Message queue initialized with {len(self.pending_messages)} pending messages")
    
    def _load_pending_messages(self) -> None:
        """Load pending messages from the pending directory."""
        for file_path in self.pending_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    message_data = json.load(f)
                    message = AsyncMessage.from_dict(message_data)
                    self.pending_messages[message.message_id] = message
            except Exception as e:
                logger.error(f"Error loading message from {file_path}: {e}")
    
    def _save_message(self, message: AsyncMessage, directory: Path) -> Path:
        """
        Save a message to a specific directory.
        
        Args:
            message: Message to save
            directory: Directory to save in
            
        Returns:
            Path to the saved file
        """
        # Generate filename based on priority and creation time for natural sorting
        priority_prefix = f"p{message.priority.value}"
        timestamp = datetime.fromisoformat(message.created_at).strftime("%Y%m%d%H%M%S")
        filename = f"{priority_prefix}_{timestamp}_{message.message_id}.json"
        
        # Save to file
        file_path = directory / filename
        with open(file_path, "w") as f:
            json.dump(message.to_dict(), f, indent=2)
        
        return file_path
    
    def enqueue(self, message: AsyncMessage) -> str:
        """
        Add a message to the queue.
        
        Args:
            message: Message to enqueue
            
        Returns:
            ID of the enqueued message
        """
        # Update status to QUEUED
        message.update_status(MessageStatus.QUEUED)
        
        # Save to pending directory
        self._save_message(message, self.pending_dir)
        
        # Add to pending messages
        self.pending_messages[message.message_id] = message
        
        logger.info(f"Message {message.message_id} enqueued for {message.recipient_id}")
        return message.message_id
    
    def get_messages(
        self,
        recipient_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        message_type: Optional[Union[MessageType, str]] = None,
        min_priority: int = 1,
        include_processed: bool = False,
        limit: int = 100
    ) -> List[AsyncMessage]:
        """
        Get messages from the queue.
        
        Args:
            recipient_id: Filter by recipient ID
            sender_id: Filter by sender ID
            message_type: Filter by message type
            min_priority: Minimum priority level
            include_processed: Whether to include processed messages
            limit: Maximum number of messages to return
            
        Returns:
            List of matching messages
        """
        # Convert message_type to enum if it's a string
        if isinstance(message_type, str):
            try:
                message_type = MessageType[message_type.upper()]
            except (KeyError, TypeError):
                message_type = None
        
        # Get pending messages
        messages = list(self.pending_messages.values())
        
        # If include_processed, also get processed messages
        if include_processed:
            processed_messages = []
            for file_path in self.processed_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        message_data = json.load(f)
                        message = AsyncMessage.from_dict(message_data)
                        processed_messages.append(message)
                except Exception as e:
                    logger.error(f"Error loading processed message from {file_path}: {e}")
            
            messages.extend(processed_messages)
        
        # Apply filters
        filtered_messages = []
        for message in messages:
            # Skip expired messages
            if message.is_expired():
                self._mark_as_expired(message)
                continue
                
            # Apply recipient filter
            if recipient_id and message.recipient_id != recipient_id and message.recipient_id != "all":
                continue
                
            # Apply sender filter
            if sender_id and message.sender_id != sender_id:
                continue
                
            # Apply message type filter
            if message_type and message.message_type != message_type:
                continue
                
            # Apply priority filter
            if message.priority.value < min_priority:
                continue
                
            filtered_messages.append(message)
        
        # Sort by priority (highest first) and then creation time
        filtered_messages.sort(
            key=lambda m: (-m.priority.value, m.created_at)
        )
        
        # Apply limit
        return filtered_messages[:limit]
    
    def mark_as_delivered(self, message_id: str) -> bool:
        """
        Mark a message as delivered.
        
        Args:
            message_id: ID of the message to mark
            
        Returns:
            True if successful, False otherwise
        """
        if message_id not in self.pending_messages:
            logger.warning(f"Cannot mark unknown message {message_id} as delivered")
            return False
        
        # Get message
        message = self.pending_messages[message_id]
        
        # Update status
        message.update_status(MessageStatus.DELIVERED)
        
        # Move to delivered directory
        self._save_message(message, self.delivered_dir)
        
        # Remove from pending
        del self.pending_messages[message_id]
        
        # Remove from pending directory
        for file_path in self.pending_dir.glob(f"*{message_id}.json"):
            file_path.unlink()
        
        logger.info(f"Message {message_id} marked as delivered")
        return True
    
    def mark_as_processed(self, message_id: str) -> bool:
        """
        Mark a message as fully processed.
        
        Args:
            message_id: ID of the message to mark
            
        Returns:
            True if successful, False otherwise
        """
        # Check if message is pending
        if message_id in self.pending_messages:
            message = self.pending_messages[message_id]
            del self.pending_messages[message_id]
            
            # Remove from pending directory
            for file_path in self.pending_dir.glob(f"*{message_id}.json"):
                file_path.unlink()
        else:
            # Try to find in delivered directory
            delivered_files = list(self.delivered_dir.glob(f"*{message_id}.json"))
            if not delivered_files:
                logger.warning(f"Cannot mark unknown message {message_id} as processed")
                return False
            
            # Load message
            with open(delivered_files[0], "r") as f:
                message_data = json.load(f)
                message = AsyncMessage.from_dict(message_data)
            
            # Remove from delivered directory
            for file_path in delivered_files:
                file_path.unlink()
        
        # Update status
        message.update_status(MessageStatus.PROCESSED)
        
        # Save to processed directory
        self._save_message(message, self.processed_dir)
        
        logger.info(f"Message {message_id} marked as processed")
        return True
    
    def _mark_as_expired(self, message: AsyncMessage) -> None:
        """
        Mark a message as expired and move to expired directory.
        
        Args:
            message: Message to mark as expired
        """
        # Update status
        message.update_status(MessageStatus.EXPIRED)
        
        # Save to expired directory
        self._save_message(message, self.expired_dir)
        
        # Remove from pending if present
        if message.message_id in self.pending_messages:
            del self.pending_messages[message.message_id]
            
            # Remove from pending directory
            for file_path in self.pending_dir.glob(f"*{message.message_id}.json"):
                file_path.unlink()
        
        logger.info(f"Message {message.message_id} marked as expired")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired messages from the queue.
        
        Returns:
            Number of expired messages removed
        """
        count = 0
        
        # Check pending messages
        expired_ids = []
        for message_id, message in self.pending_messages.items():
            if message.is_expired():
                expired_ids.append(message_id)
                self._mark_as_expired(message)
                count += 1
        
        # Remove expired messages from pending
        for message_id in expired_ids:
            if message_id in self.pending_messages:
                del self.pending_messages[message_id]
        
        logger.info(f"Cleaned up {count} expired messages")
        return count
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the message queue.
        
        Returns:
            Dict with queue statistics
        """
        # Count files in each directory
        pending_count = len(list(self.pending_dir.glob("*.json")))
        delivered_count = len(list(self.delivered_dir.glob("*.json")))
        processed_count = len(list(self.processed_dir.glob("*.json")))
        expired_count = len(list(self.expired_dir.glob("*.json")))
        
        # Count by priority in pending
        priority_counts = {p.value: 0 for p in MessagePriority}
        for message in self.pending_messages.values():
            priority_counts[message.priority.value] += 1
        
        # Calculate queue age (oldest pending message)
        oldest_timestamp = datetime.now()
        if self.pending_messages:
            oldest = min(
                (datetime.fromisoformat(m.created_at) for m in self.pending_messages.values()),
                default=oldest_timestamp
            )
            oldest_age_seconds = (datetime.now() - oldest).total_seconds()
        else:
            oldest_age_seconds = 0
        
        return {
            "pending_count": pending_count,
            "delivered_count": delivered_count,
            "processed_count": processed_count,
            "expired_count": expired_count,
            "total_count": pending_count + delivered_count + processed_count + expired_count,
            "priority_distribution": priority_counts,
            "oldest_message_age_seconds": oldest_age_seconds,
            "client_id": self.client_id,
            "timestamp": datetime.now().isoformat()
        }


class MessageRouter:
    """
    Routes messages between AI instances.
    
    This class provides functionality for routing messages between different
    AI instances, managing delivery and status updates.
    """
    
    def __init__(self, client_id: str, data_dir: Optional[str] = None):
        """
        Initialize the message router.
        
        Args:
            client_id: ID of this client
            data_dir: Directory to store messages
        """
        self.client_id = client_id
        self.queue = MessageQueue(data_dir=data_dir, client_id=client_id)
        logger.info(f"Message router initialized for client {client_id}")
    
    async def send_message(
        self,
        content: Any,
        recipient_id: str = "all",
        message_type: Union[MessageType, str] = MessageType.DIRECT,
        priority: Union[MessagePriority, int] = MessagePriority.NORMAL,
        parent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a message to another AI instance.
        
        Args:
            content: Message content
            recipient_id: ID of the recipient
            message_type: Type of message
            priority: Message priority
            parent_id: ID of parent message
            thread_id: ID of thread
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata
            
        Returns:
            ID of the sent message
        """
        # Create message
        message = AsyncMessage(
            content=content,
            sender_id=self.client_id,
            recipient_id=recipient_id,
            message_type=message_type,
            priority=priority,
            parent_id=parent_id,
            thread_id=thread_id,
            ttl_seconds=ttl_seconds,
            metadata=metadata
        )
        
        # Enqueue message
        message_id = self.queue.enqueue(message)
        
        logger.info(f"Message {message_id} sent to {recipient_id}")
        return message_id
    
    async def get_messages(
        self,
        include_broadcast: bool = True,
        message_type: Optional[Union[MessageType, str]] = None,
        sender_id: Optional[str] = None,
        min_priority: int = 1,
        include_processed: bool = False,
        mark_as_delivered: bool = True,
        limit: int = 100
    ) -> List[AsyncMessage]:
        """
        Get messages for this client.
        
        Args:
            include_broadcast: Whether to include broadcast messages
            message_type: Filter by message type
            sender_id: Filter by sender ID
            min_priority: Minimum priority level
            include_processed: Whether to include processed messages
            mark_as_delivered: Mark retrieved messages as delivered
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        # Get messages for this client
        messages = self.queue.get_messages(
            recipient_id=self.client_id if not include_broadcast else None,
            sender_id=sender_id,
            message_type=message_type,
            min_priority=min_priority,
            include_processed=include_processed,
            limit=limit
        )
        
        # Filter messages for this client or broadcast
        if include_broadcast:
            messages = [
                m for m in messages 
                if m.recipient_id == self.client_id or m.recipient_id == "all"
            ]
        
        # Mark as delivered if requested
        if mark_as_delivered:
            for message in messages:
                # Only mark as delivered if not already processed
                if message.status != MessageStatus.PROCESSED:
                    self.queue.mark_as_delivered(message.message_id)
        
        return messages
    
    async def process_message(self, message_id: str) -> bool:
        """
        Mark a message as processed.
        
        Args:
            message_id: ID of the message to mark
            
        Returns:
            True if successful, False otherwise
        """
        return self.queue.mark_as_processed(message_id)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the message queue.
        
        Returns:
            Dict with queue statistics
        """
        return self.queue.get_queue_stats()
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired messages from the queue.
        
        Returns:
            Number of expired messages removed
        """
        return self.queue.cleanup_expired()


class AsyncCommClient:
    """
    Client for asynchronous communication between AI instances.
    
    This class provides a simple interface for sending and receiving
    messages between AI instances using the async protocol.
    """
    
    def __init__(self, client_id: str, data_dir: Optional[str] = None):
        """
        Initialize the async communication client.
        
        Args:
            client_id: ID of this client
            data_dir: Directory to store messages
        """
        self.client_id = client_id
        self.router = MessageRouter(client_id=client_id, data_dir=data_dir)
        logger.info(f"Async communication client initialized for {client_id}")
    
    async def send(
        self,
        content: Any,
        to: str = "all",
        msg_type: str = "direct",
        priority: int = 2,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Send a message to another AI instance.
        
        Args:
            content: Message content
            to: Recipient ID
            msg_type: Message type
            priority: Priority level (1-5)
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata
            thread_id: Thread ID
            parent_id: Parent message ID
            
        Returns:
            Message ID
        """
        return await self.router.send_message(
            content=content,
            recipient_id=to,
            message_type=msg_type,
            priority=priority,
            ttl_seconds=ttl_seconds,
            metadata=metadata,
            thread_id=thread_id,
            parent_id=parent_id
        )
    
    async def receive(
        self,
        include_broadcast: bool = True,
        msg_type: Optional[str] = None,
        from_id: Optional[str] = None,
        min_priority: int = 1,
        include_processed: bool = False,
        mark_as_delivered: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Receive messages for this client.
        
        Args:
            include_broadcast: Whether to include broadcast messages
            msg_type: Filter by message type
            from_id: Filter by sender ID
            min_priority: Minimum priority level
            include_processed: Whether to include processed messages
            mark_as_delivered: Mark retrieved messages as delivered
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        messages = await self.router.get_messages(
            include_broadcast=include_broadcast,
            message_type=msg_type,
            sender_id=from_id,
            min_priority=min_priority,
            include_processed=include_processed,
            mark_as_delivered=mark_as_delivered,
            limit=limit
        )
        
        # Convert to dictionaries
        return [m.to_dict() for m in messages]
    
    async def mark_processed(self, message_id: str) -> bool:
        """
        Mark a message as processed.
        
        Args:
            message_id: ID of the message to mark
            
        Returns:
            True if successful, False otherwise
        """
        return await self.router.process_message(message_id)
    
    async def status(self) -> Dict[str, Any]:
        """
        Get status information about the client.
        
        Returns:
            Status information
        """
        stats = await self.router.get_queue_stats()
        pending_for_me = len(await self.receive(mark_as_delivered=False))
        
        return {
            "client_id": self.client_id,
            "queue_stats": stats,
            "pending_messages": pending_for_me,
            "protocol_version": PROTOCOL_VERSION,
            "timestamp": datetime.now().isoformat()
        }
    
    async def broadcast(
        self,
        content: Any,
        msg_type: str = "broadcast",
        priority: int = 2,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Broadcast a message to all AI instances.
        
        Args:
            content: Message content
            msg_type: Message type
            priority: Priority level (1-5)
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        return await self.send(
            content=content,
            to="all",
            msg_type=msg_type,
            priority=priority,
            ttl_seconds=ttl_seconds,
            metadata=metadata
        )
    
    async def reply(
        self,
        parent_id: str,
        content: Any,
        priority: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Reply to a message.
        
        Args:
            parent_id: ID of the message to reply to
            content: Reply content
            priority: Priority level (1-5)
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        # Try to get messages including the one we want to reply to
        parent_messages = await self.receive(
            include_processed=True, 
            mark_as_delivered=False,
            limit=100
        )
        
        # Find the parent message
        parent = None
        for msg in parent_messages:
            if msg.get("message_id") == parent_id:
                parent = msg
                break
        
        # If not found in received messages, try to find it in message directories
        if parent is None:
            # Enhanced search across all message storage locations
            search_locations = [
                (self.router.queue.pending_dir, "pending"),
                (self.router.queue.delivered_dir, "delivered"),
                (self.router.queue.processed_dir, "processed"),
                (self.router.queue.expired_dir, "expired")  # Even check expired messages
            ]
            
            # Search in all locations
            for directory, location_name in search_locations:
                matching_files = list(directory.glob(f"*{parent_id}.json"))
                if matching_files:
                    try:
                        with open(matching_files[0], "r") as f:
                            parent = json.load(f)
                            logger.info(f"Found parent message {parent_id} in {location_name} directory")
                            break
                    except Exception as e:
                        logger.error(f"Error loading parent message from {location_name} directory: {e}")
        
        # If still not found, we can't reply
        if parent is None:
            logger.warning(f"Parent message {parent_id} not found in any location")
            return ""
        
        # Use same priority as parent if not specified
        if priority is None:
            try:
                priority = parent["priority"]
            except (KeyError, TypeError):
                logger.warning(f"Could not get priority from parent, using default priority 2")
                priority = 2
        
        # Add metadata about the reply
        reply_metadata = metadata or {}
        reply_metadata.update({
            "is_reply": True,
            "parent_id": parent_id,
            "parent_sender": parent.get("sender_id", "unknown"),
            "reply_timestamp": datetime.now().isoformat()
        })
        
        # Get thread ID from parent or use parent ID as thread ID
        thread_id = parent.get("thread_id", parent_id)
        
        # Send reply
        try:
            return await self.send(
                content=content,
                to=parent["sender_id"],
                msg_type="response",
                priority=priority,
                metadata=reply_metadata,
                thread_id=thread_id,
                parent_id=parent_id
            )
        except Exception as e:
            logger.error(f"Error sending reply to message {parent_id}: {e}")
            return ""
    
    async def cleanup(self) -> int:
        """
        Clean up expired messages.
        
        Returns:
            Number of expired messages removed
        """
        return await self.router.cleanup_expired()


# Create quickmem-style functions
async def initialize_async_comm(client_id: Optional[str] = None, data_dir: Optional[str] = None) -> AsyncCommClient:
    """
    Initialize async communication for quick memory functions.
    
    Args:
        client_id: Client ID (defaults to CMB_CLIENT_ID env var)
        data_dir: Data directory
        
    Returns:
        AsyncCommClient instance
    """
    # Get client ID from environment variable if not provided
    if client_id is None:
        client_id = os.environ.get("CMB_CLIENT_ID", "claude")
    
    # Initialize client
    return AsyncCommClient(client_id=client_id, data_dir=data_dir)

async def add_async_comm_functions() -> Dict[str, Any]:
    """
    Get a dictionary of async communication functions.
    
    Returns:
        Dict mapping function names to functions
    """
    client = await initialize_async_comm()
    
    return {
        # Core functions
        "send_async": client.send,
        "receive_async": client.receive,
        "mark_processed": client.mark_processed,
        "async_status": client.status,
        "async_broadcast": client.broadcast,
        "async_reply": client.reply,
        "async_cleanup": client.cleanup,
        
        # Short aliases
        "sa": client.send,
        "ra": client.receive,
        "mp": client.mark_processed,
        "as": client.status,
        "ba": client.broadcast,
        "rp": client.reply,
        "ac": client.cleanup
    }