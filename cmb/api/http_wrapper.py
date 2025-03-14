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

# Import memory service
from cmb.core.memory import MemoryService

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

# Global memory service instance
memory_service = None
client_id = None

@app.on_event("startup")
async def startup_event():
    """Initialize memory service on startup."""
    global memory_service, client_id
    
    # Get client ID from environment
    client_id = os.environ.get("CMB_CLIENT_ID", "claude")
    data_dir = os.environ.get("CMB_DATA_DIR", None)
    
    # Initialize memory service
    try:
        memory_service = MemoryService(client_id=client_id, data_dir=data_dir)
        logger.info(f"Memory service initialized with client ID: {client_id}")
    except Exception as e:
        logger.error(f"Failed to initialize memory service: {e}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Claude Memory Bridge HTTP Wrapper"}

@app.get("/health")
async def health_check():
    """Check if the memory bridge is running."""
    if memory_service is None:
        return {"status": "error", "message": "Memory service not initialized"}
    
    return {
        "status": "ok",
        "client_id": client_id,
        "mem0_available": getattr(memory_service, "mem0_available", False)
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