#!/usr/bin/env python3
"""
Simple HTTP wrapper for Claude Memory Bridge

This provides a RESTful API that Claude can call without requiring tool approval.
"""

import os
import json
import sys
import logging
from pathlib import Path
import asyncio
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
sys.path.insert(0, project_root)

# Import memory services
from cmb.core.memory import MemoryService
from cmb.core.structured_memory import StructuredMemory
from cmb.core.nexus import NexusInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.http_wrapper")

# Initialize FastAPI app
app = FastAPI(
    title="Claude Memory Bridge HTTP Wrapper",
    description="Simple HTTP API for Claude to access the memory bridge without tool approval",
    version="0.1.0"
)

# Global service instances
memory_service = None
structured_memory = None
nexus = None
client_id = None

@app.on_event("startup")
async def startup_event():
    """Initialize memory services on startup."""
    global memory_service, structured_memory, nexus, client_id
    
    # Get client ID from environment
    client_id = os.environ.get("CMB_CLIENT_ID", "claude")
    data_dir = os.environ.get("CMB_DATA_DIR", None)
    
    # Initialize memory service
    try:
        # Initialize legacy memory service
        memory_service = MemoryService(client_id=client_id, data_dir=data_dir)
        logger.info(f"Legacy memory service initialized with client ID: {client_id}")
        
        # Initialize structured memory service
        structured_memory = StructuredMemory(client_id=client_id, data_dir=data_dir)
        logger.info(f"Structured memory service initialized with client ID: {client_id}")
        
        # Initialize Nexus interface with both memory systems
        nexus = NexusInterface(memory_service=memory_service, structured_memory=structured_memory)
        logger.info(f"Nexus interface initialized with client ID: {client_id}")
    except Exception as e:
        logger.error(f"Failed to initialize memory services: {e}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Claude Memory Bridge HTTP Wrapper"}

@app.get("/health")
async def health_check():
    """Check if the memory bridge is running."""
    # Check if both memory services and Nexus are running
    if memory_service is None or structured_memory is None or nexus is None:
        return {"status": "error", "message": "One or more memory services not initialized"}
    
    # Return status
    return {
        "status": "ok",
        "client_id": client_id,
        "mem0_available": getattr(memory_service, "mem0_available", False),
        "structured_memory_available": structured_memory is not None,
        "nexus_available": nexus is not None,
        "structured_categories": list(structured_memory.category_importance.keys()) if structured_memory else []
    }

@app.get("/store")
async def store_memory(
    key: str,
    value: str,
    namespace: str = "conversations"
):
    """Store a memory in the specified namespace."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        # Store the memory
        success = await memory_service.add(
            content=value,
            namespace=namespace,
            metadata={"key": key}
        )
        
        return {
            "success": success,
            "key": key,
            "namespace": namespace,
        }
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        return {"status": "error", "message": f"Failed to store memory: {str(e)}"}

@app.get("/thinking")
async def store_thinking(thought: str):
    """Store a thought in the thinking namespace."""
    return await store_memory(key="thought", value=thought, namespace="thinking")

@app.get("/longterm")
async def store_longterm(info: str):
    """Store important information in the longterm namespace."""
    return await store_memory(key="important", value=info, namespace="longterm")

@app.get("/query")
async def query_memory(
    query: str,
    namespace: str = "conversations",
    limit: int = 5
):
    """Query memory for relevant information."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        # Search for memories
        results = await memory_service.search(
            query=query,
            namespace=namespace,
            limit=limit
        )
        
        return results
    except Exception as e:
        logger.error(f"Error querying memory: {e}")
        return {"status": "error", "message": f"Failed to query memory: {str(e)}"}

@app.get("/context")
async def get_context(
    query: str,
    include_thinking: bool = True,
    limit: int = 3
):
    """Get formatted context from multiple namespaces."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        # Determine which namespaces to include
        namespaces = ["conversations", "longterm"]
        if include_thinking:
            namespaces.append("thinking")
        
        # Get formatted context
        context = await memory_service.get_relevant_context(
            query=query,
            namespaces=namespaces,
            limit=limit
        )
        
        return {"context": context}
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return {"status": "error", "message": f"Failed to get context: {str(e)}"}

@app.get("/clear/{namespace}")
async def clear_namespace(namespace: str):
    """Clear all memories in a namespace."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        success = await memory_service.clear_namespace(namespace)
        return {"success": success, "namespace": namespace}
    except Exception as e:
        logger.error(f"Error clearing namespace: {e}")
        return {"status": "error", "message": f"Failed to clear namespace: {str(e)}"}

@app.get("/write")
async def write_session_memory(content: str, metadata: str = None):
    """Write a memory to the session namespace for persistence."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        # Parse metadata if provided
        meta_dict = json.loads(metadata) if metadata else None
        
        success = await memory_service.write_session_memory(content, meta_dict)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error writing session memory: {e}")
        return {"status": "error", "message": f"Failed to write session memory: {str(e)}"}

@app.get("/load")
async def load_session_memory(limit: int = 1):
    """Load previous session memory."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        # Search for the most recent session memories
        results = await memory_service.search(
            query="",
            namespace="session",
            limit=limit
        )
        
        if results.get("count", 0) > 0:
            return {
                "success": True,
                "content": [r.get("content", "") for r in results.get("results", [])],
                "metadata": [r.get("metadata", {}) for r in results.get("results", [])]
            }
        else:
            return {"success": False, "message": "No session memory found"}
    except Exception as e:
        logger.error(f"Error loading session memory: {e}")
        return {"status": "error", "message": f"Failed to load session memory: {str(e)}"}

@app.get("/compartment/create")
async def create_compartment(name: str, description: str = None, parent: str = None):
    """Create a new memory compartment."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        compartment_id = await memory_service.create_compartment(name, description, parent)
        if compartment_id:
            return {"success": True, "compartment_id": compartment_id}
        else:
            return {"success": False, "message": "Failed to create compartment"}
    except Exception as e:
        logger.error(f"Error creating compartment: {e}")
        return {"status": "error", "message": f"Failed to create compartment: {str(e)}"}

@app.get("/compartment/store")
async def store_in_compartment(compartment: str, content: str, key: str = "memory"):
    """Store content in a specific compartment."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        # Find compartment ID if a name was provided
        compartment_id = None
        
        # First check if it's already an ID
        if compartment in memory_service.compartments:
            compartment_id = compartment
        else:
            # Look for compartment by name
            for c_id, c_data in memory_service.compartments.items():
                if c_data.get("name", "").lower() == compartment.lower():
                    compartment_id = c_id
                    break
        
        if not compartment_id:
            return {"success": False, "message": f"Compartment '{compartment}' not found"}
        
        # Store in compartment namespace
        namespace = f"compartment-{compartment_id}"
        success = await memory_service.add(
            content=content,
            namespace=namespace,
            metadata={"key": key}
        )
        
        # Also activate the compartment
        await memory_service.activate_compartment(compartment_id)
        
        return {"success": success, "compartment_id": compartment_id}
    except Exception as e:
        logger.error(f"Error storing in compartment: {e}")
        return {"status": "error", "message": f"Failed to store in compartment: {str(e)}"}

@app.get("/compartment/activate")
async def activate_compartment(compartment: str):
    """Activate a compartment to include in automatic context retrieval."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        success = await memory_service.activate_compartment(compartment)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error activating compartment: {e}")
        return {"status": "error", "message": f"Failed to activate compartment: {str(e)}"}

@app.get("/compartment/deactivate")
async def deactivate_compartment(compartment: str):
    """Deactivate a compartment to exclude from automatic context retrieval."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        success = await memory_service.deactivate_compartment(compartment)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deactivating compartment: {e}")
        return {"status": "error", "message": f"Failed to deactivate compartment: {str(e)}"}

@app.get("/compartment/list")
async def list_compartments(include_expired: bool = False):
    """List all compartments."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        compartments = await memory_service.list_compartments(include_expired)
        return {"compartments": compartments, "count": len(compartments)}
    except Exception as e:
        logger.error(f"Error listing compartments: {e}")
        return {"status": "error", "message": f"Failed to list compartments: {str(e)}"}

@app.get("/compartment/expire")
async def set_compartment_expiration(compartment_id: str, days: int = None):
    """Set expiration for a compartment in days."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        success = await memory_service.set_compartment_expiration(compartment_id, days)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error setting compartment expiration: {e}")
        return {"status": "error", "message": f"Failed to set compartment expiration: {str(e)}"}

@app.get("/keep")
async def keep_memory(memory_id: str, days: int = 30):
    """Keep a memory for a specified number of days."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        success = await memory_service.keep_memory(memory_id, days)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error keeping memory: {e}")
        return {"status": "error", "message": f"Failed to keep memory: {str(e)}"}

@app.get("/private")
async def store_private(content: str):
    """Store a private memory."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        memory_id, success = await memory_service.add_private(content)
        if success:
            return {"success": True, "memory_id": memory_id}
        else:
            return {"success": False, "message": "Failed to store private memory"}
    except Exception as e:
        logger.error(f"Error storing private memory: {e}")
        return {"status": "error", "message": f"Failed to store private memory: {str(e)}"}

@app.get("/private/get")
async def get_private(memory_id: str, use_emergency: bool = False):
    """Get a specific private memory."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        memory = await memory_service.get_private(memory_id, use_emergency)
        if memory:
            return {"success": True, "memory": memory}
        else:
            return {"success": False, "message": "Failed to retrieve private memory"}
    except Exception as e:
        logger.error(f"Error retrieving private memory: {e}")
        return {"status": "error", "message": f"Failed to retrieve private memory: {str(e)}"}

@app.get("/private/list")
async def list_private():
    """List all private memories."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        memories = await memory_service.list_private()
        return {"success": True, "memories": memories}
    except Exception as e:
        logger.error(f"Error listing private memories: {e}")
        return {"status": "error", "message": f"Failed to list private memories: {str(e)}"}

@app.get("/private/delete")
async def delete_private(memory_id: str):
    """Delete a private memory."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    try:
        success = await memory_service.delete_private(memory_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deleting private memory: {e}")
        return {"status": "error", "message": f"Failed to delete private memory: {str(e)}"}

# Structured Memory Endpoints

@app.get("/structured/add")
async def add_structured_memory(
    content: str,
    category: str = "session",
    importance: Optional[int] = None,
    tags: Optional[str] = None,
    metadata: Optional[str] = None
):
    """Add a memory to the structured memory system."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        # Parse metadata and tags if provided
        meta_dict = json.loads(metadata) if metadata else None
        tags_list = json.loads(tags) if tags else None
        
        # Add memory
        memory_id = await structured_memory.add_memory(
            content=content,
            category=category,
            importance=importance,
            metadata=meta_dict,
            tags=tags_list
        )
        
        if memory_id:
            return {"success": True, "memory_id": memory_id}
        else:
            return {"success": False, "message": "Failed to add memory"}
    except Exception as e:
        logger.error(f"Error adding structured memory: {e}")
        return {"status": "error", "message": f"Failed to add structured memory: {str(e)}"}

@app.get("/structured/auto")
async def add_auto_categorized_memory(
    content: str,
    manual_category: Optional[str] = None,
    manual_importance: Optional[int] = None,
    manual_tags: Optional[str] = None,
    metadata: Optional[str] = None
):
    """Add a memory with automatic categorization."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        # Parse metadata and tags if provided
        meta_dict = json.loads(metadata) if metadata else None
        tags_list = json.loads(manual_tags) if manual_tags else None
        
        # Parse importance if provided
        importance = int(manual_importance) if manual_importance is not None else None
        
        # Add auto-categorized memory
        memory_id = await structured_memory.add_auto_categorized_memory(
            content=content,
            manual_category=manual_category,
            manual_importance=importance,
            manual_tags=tags_list,
            metadata=meta_dict
        )
        
        if memory_id:
            return {"success": True, "memory_id": memory_id}
        else:
            return {"success": False, "message": "Failed to add memory"}
    except Exception as e:
        logger.error(f"Error adding auto-categorized memory: {e}")
        return {"status": "error", "message": f"Failed to add auto-categorized memory: {str(e)}"}

@app.get("/structured/get")
async def get_structured_memory(memory_id: str):
    """Get a specific memory by ID."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        memory = await structured_memory.get_memory(memory_id)
        if memory:
            return {"success": True, "memory": memory}
        else:
            return {"success": False, "message": "Memory not found"}
    except Exception as e:
        logger.error(f"Error getting structured memory: {e}")
        return {"status": "error", "message": f"Failed to get structured memory: {str(e)}"}

@app.get("/structured/search")
async def search_structured_memory(
    query: Optional[str] = None,
    categories: Optional[str] = None,
    tags: Optional[str] = None,
    min_importance: int = 1,
    limit: int = 10,
    sort_by: str = "importance"
):
    """Search for memories."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        # Parse categories and tags
        categories_list = json.loads(categories) if categories else None
        tags_list = json.loads(tags) if tags else None
        
        # Search memories
        memories = await structured_memory.search_memories(
            query=query,
            categories=categories_list,
            tags=tags_list,
            min_importance=min_importance,
            limit=limit,
            sort_by=sort_by
        )
        
        return {"success": True, "results": memories, "count": len(memories)}
    except Exception as e:
        logger.error(f"Error searching structured memories: {e}")
        return {"status": "error", "message": f"Failed to search structured memories: {str(e)}"}

@app.get("/structured/digest")
async def get_memory_digest(
    max_memories: int = 10,
    include_private: bool = False,
    categories: Optional[str] = None
):
    """Get a memory digest."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        # Parse categories
        categories_list = json.loads(categories) if categories else None
        
        # Get digest
        digest = await structured_memory.get_memory_digest(
            categories=categories_list,
            max_memories=max_memories,
            include_private=include_private
        )
        
        return {"success": True, "digest": digest}
    except Exception as e:
        logger.error(f"Error getting memory digest: {e}")
        return {"status": "error", "message": f"Failed to get memory digest: {str(e)}"}

@app.get("/structured/delete")
async def delete_structured_memory(memory_id: str):
    """Delete a memory."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        success = await structured_memory.delete_memory(memory_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deleting structured memory: {e}")
        return {"status": "error", "message": f"Failed to delete structured memory: {str(e)}"}

@app.get("/structured/importance")
async def set_memory_importance(memory_id: str, importance: int):
    """Update the importance of a memory."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        success = await structured_memory.set_memory_importance(memory_id, importance)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error updating memory importance: {e}")
        return {"status": "error", "message": f"Failed to update memory importance: {str(e)}"}

@app.get("/structured/context")
async def get_context_memories(text: str, max_memories: int = 5):
    """Get memories relevant to context."""
    if structured_memory is None:
        return {"status": "error", "message": "Structured memory service not initialized"}
    
    try:
        memories = await structured_memory.get_context_memories(text, max_memories)
        return {"success": True, "memories": memories, "count": len(memories)}
    except Exception as e:
        logger.error(f"Error getting context memories: {e}")
        return {"status": "error", "message": f"Failed to get context memories: {str(e)}"}

# Nexus Interface Endpoints

@app.get("/nexus/start")
async def start_nexus_session(session_name: Optional[str] = None):
    """Start a new Nexus session."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        result = await nexus.start_session(session_name)
        return {"success": True, "session_id": nexus.session_id, "message": result}
    except Exception as e:
        logger.error(f"Error starting Nexus session: {e}")
        return {"status": "error", "message": f"Failed to start Nexus session: {str(e)}"}

@app.get("/nexus/end")
async def end_nexus_session(summary: Optional[str] = None):
    """End the current Nexus session."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        result = await nexus.end_session(summary)
        return {"success": True, "message": result}
    except Exception as e:
        logger.error(f"Error ending Nexus session: {e}")
        return {"status": "error", "message": f"Failed to end Nexus session: {str(e)}"}

@app.get("/nexus/process")
async def process_message(
    message: str,
    is_user: bool = True,
    metadata: Optional[str] = None
):
    """Process a conversation message."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        # Parse metadata if provided
        meta_dict = json.loads(metadata) if metadata else None
        
        # Process message
        result = await nexus.process_message(message, is_user, meta_dict)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"status": "error", "message": f"Failed to process message: {str(e)}"}

@app.get("/nexus/store")
async def store_nexus_memory(
    content: str,
    category: Optional[str] = None,
    importance: Optional[int] = None,
    tags: Optional[str] = None,
    metadata: Optional[str] = None
):
    """Store a memory using the Nexus interface."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        # Parse metadata and tags if provided
        meta_dict = json.loads(metadata) if metadata else None
        tags_list = json.loads(tags) if tags else None
        
        # Parse importance if provided
        imp = int(importance) if importance is not None else None
        
        # Store memory
        result = await nexus.store_memory(
            content=content,
            category=category,
            importance=imp,
            tags=tags_list,
            metadata=meta_dict
        )
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error storing Nexus memory: {e}")
        return {"status": "error", "message": f"Failed to store Nexus memory: {str(e)}"}

@app.get("/nexus/forget")
async def forget_nexus_memory(content: str):
    """Mark information to be forgotten."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        success = await nexus.forget_memory(content)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error forgetting memory: {e}")
        return {"status": "error", "message": f"Failed to forget memory: {str(e)}"}

@app.get("/nexus/search")
async def search_nexus_memories(
    query: Optional[str] = None,
    categories: Optional[str] = None,
    min_importance: int = 1,
    limit: int = 5
):
    """Search for memories across memory systems."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        # Parse categories if provided
        categories_list = json.loads(categories) if categories else None
        
        # Search memories
        result = await nexus.search_memories(
            query=query,
            categories=categories_list,
            min_importance=min_importance,
            limit=limit
        )
        
        return {"success": True, "results": result}
    except Exception as e:
        logger.error(f"Error searching Nexus memories: {e}")
        return {"status": "error", "message": f"Failed to search Nexus memories: {str(e)}"}

@app.get("/nexus/summary")
async def get_nexus_conversation_summary(max_length: int = 5):
    """Get a summary of the current conversation."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        summary = await nexus.get_conversation_summary(max_length)
        return {"success": True, "summary": summary}
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        return {"status": "error", "message": f"Failed to get conversation summary: {str(e)}"}

@app.get("/nexus/settings")
async def get_nexus_settings():
    """Get current Nexus settings."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        settings = await nexus.get_settings()
        return {"success": True, "settings": settings}
    except Exception as e:
        logger.error(f"Error getting Nexus settings: {e}")
        return {"status": "error", "message": f"Failed to get Nexus settings: {str(e)}"}

@app.get("/nexus/update-settings")
async def update_nexus_settings(settings: str):
    """Update Nexus settings."""
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        # Parse settings
        settings_dict = json.loads(settings)
        
        # Update settings
        updated_settings = await nexus.update_settings(settings_dict)
        return {"success": True, "settings": updated_settings}
    except Exception as e:
        logger.error(f"Error updating Nexus settings: {e}")
        return {"status": "error", "message": f"Failed to update Nexus settings: {str(e)}"}

def main():
    """Run the HTTP wrapper server."""
    parser = argparse.ArgumentParser(description="Claude Memory Bridge HTTP Wrapper")
    parser.add_argument("--client-id", type=str, default="claude",
                      help="Client ID for memory service")
    parser.add_argument("--port", type=int, default=8001,
                      help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                      help="Host to bind the server to")
    parser.add_argument("--data-dir", type=str, default=None,
                      help="Directory to store memory data")
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["CMB_CLIENT_ID"] = args.client_id
    if args.data_dir:
        os.environ["CMB_DATA_DIR"] = args.data_dir
    
    # Start the server
    logger.info(f"Starting HTTP wrapper server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    import argparse
    main()