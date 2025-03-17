# Agenteer Integration with Engram Async Protocol

## Overview

This document outlines the planned integration between the Agenteer agent framework and the Engram asynchronous messaging system. The integration will enable Agenteer agents to communicate with each other and with other AI systems using Engram's robust messaging capabilities.

## Integration Goals

1. Allow Agenteer agents to send and receive asynchronous messages
2. Enable persistent communication between agent sessions
3. Support cross-agent workflow orchestration
4. Provide structured message passing between specialized agents
5. Create a flexible communication interface for multi-agent systems

## Architecture Design

### Core Components

#### 1. Engram Message Adapter for Agenteer

A dedicated adapter module that connects Agenteer's agent framework to Engram's async messaging protocol.

```python
# Proposed module: agenteer/adapters/engram_messaging.py

from typing import Dict, Any, List, Optional
import asyncio
import os

# Import from Engram
from cmb.cli.comm_quickmem import (
    send_async, receive_async, broadcast_async, reply_async, 
    async_status, cleanup_async,
    # Short aliases
    sa, ra, ba, rp, acs, cla
)

class EngramMessaging:
    """
    Adapter for Engram's asynchronous messaging protocol.
    
    This class provides Agenteer agents with the ability to send and
    receive asynchronous messages using Engram's robust messaging 
    system with message persistence, threading, and delivery guarantees.
    """
    
    def __init__(self, agent_id: str, data_dir: Optional[str] = None):
        """
        Initialize the Engram messaging adapter.
        
        Args:
            agent_id: ID of the Agenteer agent (used as client_id)
            data_dir: Optional path to store message data
        """
        self.agent_id = agent_id
        self.data_dir = data_dir
        
        # Set environment variable for Engram
        os.environ["CMB_CLIENT_ID"] = agent_id
        if data_dir:
            os.environ["CMB_DATA_DIR"] = data_dir
    
    async def send_message(self, content: Any, to: str, priority: int = 2, **kwargs) -> str:
        """
        Send an asynchronous message to another agent.
        
        Args:
            content: Message content (can be any JSON-serializable data)
            to: Recipient agent ID
            priority: Message priority (1-5)
            **kwargs: Additional parameters for send_async
            
        Returns:
            Message ID if successful, empty string otherwise
        """
        try:
            return await send_async(
                content=content,
                to=to,
                priority=priority,
                **kwargs
            )
        except Exception as e:
            print(f"Error sending message: {e}")
            return ""
    
    async def broadcast(self, content: Any, priority: int = 2, **kwargs) -> str:
        """
        Broadcast a message to all agents.
        
        Args:
            content: Message content
            priority: Message priority (1-5)
            **kwargs: Additional parameters for broadcast_async
            
        Returns:
            Message ID if successful, empty string otherwise
        """
        try:
            return await broadcast_async(
                content=content,
                priority=priority,
                **kwargs
            )
        except Exception as e:
            print(f"Error broadcasting message: {e}")
            return ""
    
    async def get_messages(self, include_broadcast: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """
        Get messages addressed to this agent.
        
        Args:
            include_broadcast: Whether to include broadcast messages
            **kwargs: Additional filtering parameters
            
        Returns:
            List of message dictionaries
        """
        try:
            return await receive_async(
                include_broadcast=include_broadcast,
                **kwargs
            )
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    async def reply_to(self, message_id: str, content: Any, **kwargs) -> str:
        """
        Reply to a specific message.
        
        Args:
            message_id: ID of the message to reply to
            content: Reply content
            **kwargs: Additional parameters
            
        Returns:
            Message ID of the reply if successful, empty string otherwise
        """
        try:
            return await reply_async(
                parent_id=message_id,
                content=content,
                **kwargs
            )
        except Exception as e:
            print(f"Error replying to message: {e}")
            return ""
    
    async def mark_processed(self, message_id: str) -> bool:
        """
        Mark a message as fully processed.
        
        Args:
            message_id: ID of the message to mark
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await mark_processed_async(message_id)
        except Exception as e:
            print(f"Error marking message as processed: {e}")
            return False
    
    async def check_status(self) -> Dict[str, Any]:
        """
        Get status information about the messaging system.
        
        Returns:
            Status dictionary or None if error
        """
        try:
            return await async_status()
        except Exception as e:
            print(f"Error checking status: {e}")
            return None
    
    async def cleanup(self) -> int:
        """
        Clean up expired messages.
        
        Returns:
            Number of messages cleaned up
        """
        try:
            return await cleanup_async()
        except Exception as e:
            print(f"Error cleaning up messages: {e}")
            return 0
```

#### 2. Agent Messaging Extension

An extension to the base Agenteer Agent class that provides messaging capabilities.

```python
# Proposed extension: agenteer/extensions/messaging.py

from typing import Dict, Any, List, Optional, Union
import asyncio
import json
from agenteer.adapters.engram_messaging import EngramMessaging

class MessagingExtension:
    """
    Extension providing asynchronous messaging capabilities to Agenteer agents.
    """
    
    def __init__(self, agent):
        """
        Initialize the messaging extension.
        
        Args:
            agent: The Agenteer agent this extension is attached to
        """
        self.agent = agent
        self.messaging = EngramMessaging(agent.id)
        self._initialize_event_handlers()
    
    def _initialize_event_handlers(self):
        """Set up event handlers for message-related events."""
        self.agent.on("before_run", self._check_incoming_messages)
        self.agent.on("after_run", self._process_outgoing_messages)
    
    async def _check_incoming_messages(self):
        """Check for incoming messages before agent execution."""
        messages = await self.messaging.get_messages(limit=10)
        if messages:
            # Add messages to agent context
            self.agent.context["incoming_messages"] = messages
            
            # Process high-priority messages immediately
            high_priority = [m for m in messages if m.get("priority", 2) >= 4]
            if high_priority:
                self.agent.context["high_priority_messages"] = high_priority
    
    async def _process_outgoing_messages(self):
        """Process any outgoing messages after agent execution."""
        if "outgoing_messages" in self.agent.context:
            outgoing = self.agent.context["outgoing_messages"]
            for msg in outgoing:
                recipient = msg.get("to", "all")
                content = msg.get("content")
                priority = msg.get("priority", 2)
                
                if recipient == "all":
                    await self.messaging.broadcast(content, priority)
                else:
                    await self.messaging.send_message(content, recipient, priority)
            
            # Clear processed messages
            self.agent.context["outgoing_messages"] = []
    
    # Public API methods
    
    async def send(self, to: str, content: Any, priority: int = 2, **kwargs) -> str:
        """
        Send a message to another agent.
        
        Args:
            to: Recipient agent ID
            content: Message content
            priority: Message priority (1-5)
            **kwargs: Additional parameters
            
        Returns:
            Message ID
        """
        return await self.messaging.send_message(content, to, priority, **kwargs)
    
    async def broadcast(self, content: Any, priority: int = 2, **kwargs) -> str:
        """
        Broadcast a message to all agents.
        
        Args:
            content: Message content
            priority: Message priority (1-5)
            **kwargs: Additional parameters
            
        Returns:
            Message ID
        """
        return await self.messaging.broadcast(content, priority, **kwargs)
    
    async def get_messages(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get messages for this agent.
        
        Args:
            **kwargs: Filtering parameters
            
        Returns:
            List of message dictionaries
        """
        return await self.messaging.get_messages(**kwargs)
    
    async def reply(self, message_id: str, content: Any, **kwargs) -> str:
        """
        Reply to a message.
        
        Args:
            message_id: ID of the message to reply to
            content: Reply content
            **kwargs: Additional parameters
            
        Returns:
            Message ID of the reply
        """
        return await self.messaging.reply_to(message_id, content, **kwargs)
    
    def queue_message(self, to: str, content: Any, priority: int = 2, **kwargs):
        """
        Queue a message to be sent after the agent run completes.
        
        Args:
            to: Recipient agent ID
            content: Message content
            priority: Message priority (1-5)
            **kwargs: Additional parameters
        """
        if "outgoing_messages" not in self.agent.context:
            self.agent.context["outgoing_messages"] = []
            
        self.agent.context["outgoing_messages"].append({
            "to": to,
            "content": content,
            "priority": priority,
            **kwargs
        })
```

#### 3. Specialized Message Types

Custom message formats for specific types of agent-to-agent communication.

```python
# Proposed module: agenteer/messaging/message_types.py

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

class AgentMessageType(Enum):
    """Types of messages that can be exchanged between agents."""
    # Task-related messages
    TASK_REQUEST = "task_request"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Knowledge-related messages
    KNOWLEDGE_QUERY = "knowledge_query"
    KNOWLEDGE_RESPONSE = "knowledge_response"
    
    # Coordination messages
    AVAILABILITY_CHECK = "availability_check"
    AVAILABILITY_RESPONSE = "availability_response"
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    
    # Decision messages
    DECISION_REQUEST = "decision_request"
    DECISION_RESPONSE = "decision_response"
    VOTE_REQUEST = "vote_request"
    VOTE_RESPONSE = "vote_response"
    
    # Status messages
    STATUS_UPDATE = "status_update"
    HEART_BEAT = "heart_beat"
    ERROR_REPORT = "error_report"
    WARNING = "warning"

# Message factories

def create_task_request(task_id: str, description: str, requirements: Dict[str, Any], 
                       deadline: Optional[str] = None, priority: int = 3) -> Dict[str, Any]:
    """
    Create a task request message.
    
    Args:
        task_id: Unique identifier for the task
        description: Human-readable task description
        requirements: Dictionary of task requirements and parameters
        deadline: Optional deadline in ISO format
        priority: Task priority (1-5)
        
    Returns:
        Task request message dictionary
    """
    return {
        "message_type": AgentMessageType.TASK_REQUEST.value,
        "content": {
            "task_id": task_id,
            "description": description,
            "requirements": requirements,
            "deadline": deadline,
            "timestamp": datetime.now().isoformat(),
        },
        "priority": priority,
        "metadata": {
            "message_category": "task",
            "expected_response": AgentMessageType.AVAILABILITY_RESPONSE.value
        }
    }

def create_task_progress(task_id: str, progress: float, status_message: str,
                        remaining_time: Optional[str] = None, 
                        artifacts: Optional[List[Dict[str, Any]]] = None,
                        priority: int = 2) -> Dict[str, Any]:
    """
    Create a task progress message.
    
    Args:
        task_id: ID of the task
        progress: Progress percentage (0.0 to 1.0)
        status_message: Current status description
        remaining_time: Estimated time remaining
        artifacts: Optional list of intermediate artifacts
        priority: Message priority (1-5)
        
    Returns:
        Task progress message dictionary
    """
    return {
        "message_type": AgentMessageType.TASK_PROGRESS.value,
        "content": {
            "task_id": task_id,
            "progress": progress,
            "status_message": status_message,
            "remaining_time": remaining_time,
            "artifacts": artifacts or [],
            "timestamp": datetime.now().isoformat(),
        },
        "priority": priority,
        "metadata": {
            "message_category": "task",
            "update_type": "progress"
        }
    }

def create_task_completed(task_id: str, results: Dict[str, Any],
                        execution_time: Optional[float] = None,
                        priority: int = 3) -> Dict[str, Any]:
    """
    Create a task completion message.
    
    Args:
        task_id: ID of the completed task
        results: Dictionary of task results
        execution_time: Total execution time in seconds
        priority: Message priority (1-5)
        
    Returns:
        Task completed message dictionary
    """
    return {
        "message_type": AgentMessageType.TASK_COMPLETED.value,
        "content": {
            "task_id": task_id,
            "results": results,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
        },
        "priority": priority,
        "metadata": {
            "message_category": "task",
            "update_type": "completion",
            "requires_acknowledgment": True
        }
    }
```

## Usage Examples

### 1. Simple Agent-to-Agent Communication

```python
# Example: Direct messaging between agents

from agenteer import Agent
from agenteer.extensions.messaging import MessagingExtension

# Create agent with messaging extension
agent = Agent(
    name="DataProcessorAgent",
    description="Processes data and sends results to other agents",
    extensions=[MessagingExtension]
)

# In agent's run method
async def run(self, input_data):
    # Process data
    results = self.process_data(input_data)
    
    # Send results to another agent
    message_id = await self.extensions.messaging.send(
        to="VisualizationAgent",
        content={
            "processed_data": results,
            "dataset_name": input_data.get("name", "unknown"),
            "timestamp": datetime.now().isoformat()
        },
        priority=3
    )
    
    return {
        "status": "success",
        "message": f"Data processed and sent to visualization agent",
        "message_id": message_id
    }
```

### 2. Task Delegation and Workflow

```python
# Example: Task delegation with progress tracking

from agenteer import Agent
from agenteer.extensions.messaging import MessagingExtension
from agenteer.messaging.message_types import (
    create_task_request, 
    create_task_progress,
    create_task_completed,
    AgentMessageType
)

# Coordinator agent
class CoordinatorAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_extension(MessagingExtension)
        self.task_status = {}
    
    async def delegate_task(self, task_id, description, requirements, worker_id):
        # Create task request
        message = create_task_request(
            task_id=task_id,
            description=description,
            requirements=requirements,
            priority=3
        )
        
        # Send to worker agent
        message_id = await self.extensions.messaging.send(
            to=worker_id,
            content=message["content"],
            msg_type=message["message_type"],
            priority=message["priority"],
            metadata=message["metadata"]
        )
        
        # Track task
        self.task_status[task_id] = {
            "status": "delegated",
            "worker": worker_id,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return message_id
    
    async def check_task_updates(self):
        # Get messages since last check
        messages = await self.extensions.messaging.get_messages(
            include_processed=False
        )
        
        for msg in messages:
            content = msg.get("content", {})
            msg_type = msg.get("message_type")
            
            # Check for task progress updates
            if msg_type == AgentMessageType.TASK_PROGRESS.value:
                task_id = content.get("task_id")
                if task_id in self.task_status:
                    self.task_status[task_id].update({
                        "status": "in_progress",
                        "progress": content.get("progress", 0),
                        "last_update": content.get("timestamp")
                    })
            
            # Check for task completions
            elif msg_type == AgentMessageType.TASK_COMPLETED.value:
                task_id = content.get("task_id")
                if task_id in self.task_status:
                    self.task_status[task_id].update({
                        "status": "completed",
                        "results": content.get("results"),
                        "execution_time": content.get("execution_time"),
                        "completion_time": content.get("timestamp")
                    })
                    
                    # Mark message as processed
                    await self.extensions.messaging.mark_processed(msg["message_id"])
```

## Integration Steps

### Phase 1: Basic Messaging Integration

1. Create the EngramMessaging adapter class
2. Add MessagingExtension to Agenteer
3. Update the Agent base class to support extensions
4. Implement message serialization/deserialization
5. Add basic example agents using messaging

### Phase 2: Enhanced Messaging Capabilities

1. Implement specialized message types
2. Add task delegation and workflow patterns
3. Create message filtering and prioritization
4. Implement conversation threading for complex interactions
5. Add message persistence across agent restarts

### Phase 3: Advanced Agent Coordination

1. Implement agent discovery and capability advertising
2. Create coordination protocols for multi-agent tasks
3. Add supervisory patterns for agent oversight
4. Implement autonomous error recovery
5. Create visualization tools for message flows

## Testing and Validation

1. **Unit Tests**
   - Test message creation and parsing
   - Test adapter initialization
   - Test extension integration with agents

2. **Integration Tests**
   - Test message delivery between agents
   - Test conversation threading
   - Test task delegation and progress tracking

3. **System Tests**
   - Test multi-agent workflows
   - Test persistence across restarts
   - Test scalability with many agents

4. **Stress Tests**
   - Test high message volume handling
   - Test recovery from simulated failures
   - Test performance under load

## Security Considerations

1. **Authentication**
   - Implement agent identity verification
   - Add message signing for authenticity

2. **Authorization**
   - Create permission model for agent interactions
   - Implement access control for sensitive tasks

3. **Privacy**
   - Add message encryption options
   - Implement secure credential handling

4. **Auditing**
   - Create comprehensive logging
   - Add message tracing for troubleshooting

## Conclusion

The integration of Engram's asynchronous messaging protocol with Agenteer will create a powerful platform for building sophisticated agent-based systems with robust communication capabilities. This integration enables persistent messaging, complex workflows, and coordinated multi-agent activities that operate reliably across sessions and environments.