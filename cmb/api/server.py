#!/usr/bin/env python3
"""
Claude Memory Bridge API Server

A FastAPI server that provides an HTTP API for Claude to interact with the memory service.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import uvicorn
from fastapi import FastAPI, Body, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.api")

# Import CMB modules
try:
    from cmb.core.memory import MemoryService, HAS_MEM0
except ImportError as e:
    logger.error(f"Failed to import CMB modules: {e}")
    logger.error("Make sure you're running this from the project root or it's installed")
    raise

# Define API models
class MemoryQuery(BaseModel):
    query: str
    namespace: str = "conversations"
    limit: int = 5

class MemoryStore(BaseModel):
    key: str
    value: str
    namespace: str = "conversations"
    metadata: Optional[Dict[str, Any]] = None

class MemoryMultiQuery(BaseModel):
    query: str
    namespaces: List[str] = ["conversations", "thinking", "longterm"]
    limit: int = 3

class HealthResponse(BaseModel):
    status: str
    client_id: str
    mem0_available: bool
    namespaces: List[str]

# Initialize FastAPI app
app = FastAPI(
    title="Claude Memory Bridge",
    description="Bridge between Claude and persistent memory",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store memory service instance
memory_service = None
client_id = None

@app.on_event("startup")
async def startup_event():
    global memory_service, client_id
    
    # Get client ID from environment or default
    client_id = os.environ.get("CMB_CLIENT_ID", "claude")
    data_dir = os.environ.get("CMB_DATA_DIR", None)
    
    # Initialize memory service
    try:
        memory_service = MemoryService(client_id=client_id, data_dir=data_dir)
        logger.info(f"Memory service initialized with client ID: {client_id}")
    except Exception as e:
        logger.error(f"Failed to initialize memory service: {e}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the memory bridge is running and properly configured."""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    namespaces = await memory_service.get_namespaces()
    
    return HealthResponse(
        status="ok",
        client_id=client_id,
        mem0_available=memory_service.mem0_available if hasattr(memory_service, "mem0_available") else False,
        namespaces=namespaces
    )

@app.post("/query")
async def query_memory(query_data: MemoryQuery):
    """Query memory for relevant information."""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        results = await memory_service.search(
            query=query_data.query, 
            namespace=query_data.namespace, 
            limit=query_data.limit
        )
        
        # Add query timestamp
        return {
            **results,
            "query": query_data.query,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error querying memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query memory: {str(e)}")

@app.post("/store")
async def store_memory(memory_data: MemoryStore):
    """Store a new memory."""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        # Store the memory
        success = await memory_service.add(
            content=memory_data.value,
            namespace=memory_data.namespace,
            metadata=memory_data.metadata or {"key": memory_data.key}
        )
        
        return {
            "success": success,
            "key": memory_data.key,
            "namespace": memory_data.namespace,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")

@app.post("/store_conversation")
async def store_conversation(
    conversation: List[Dict[str, str]] = Body(...),
    namespace: str = Query("conversations")
):
    """Store a complete conversation."""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        # Generate a unique conversation ID
        conversation_id = f"conversation_{int(datetime.now().timestamp())}"
        
        # Store the conversation
        success = await memory_service.add(
            content=conversation,
            namespace=namespace,
            metadata={"conversation_id": conversation_id}
        )
        
        return {
            "success": success,
            "conversation_id": conversation_id,
            "message_count": len(conversation),
            "namespace": namespace,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store conversation: {str(e)}")

@app.post("/context")
async def get_context(query_data: MemoryMultiQuery):
    """Get formatted memory context across multiple namespaces."""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        # Get formatted context
        context = await memory_service.get_relevant_context(
            query=query_data.query,
            namespaces=query_data.namespaces,
            limit=query_data.limit
        )
        
        return {
            "context": context,
            "query": query_data.query,
            "namespaces": query_data.namespaces,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@app.post("/clear/{namespace}")
async def clear_namespace(namespace: str):
    """Clear all memories in a namespace."""
    if memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        success = await memory_service.clear_namespace(namespace)
        
        return {
            "success": success,
            "namespace": namespace,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing namespace: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear namespace: {str(e)}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Claude Memory Bridge API Server")
    parser.add_argument("--client-id", type=str, default="claude",
                      help="Client ID for memory service")
    parser.add_argument("--port", type=int, default=8000,
                      help="Port to run the server on")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                      help="Host to bind the server to")
    parser.add_argument("--data-dir", type=str, default=None,
                      help="Directory to store memory data")
    return parser.parse_args()

def main():
    """Main entry point for the CLI command."""
    args = parse_arguments()
    
    # Set environment variables
    os.environ["CMB_CLIENT_ID"] = args.client_id
    if args.data_dir:
        os.environ["CMB_DATA_DIR"] = args.data_dir
    
    # Start the server
    logger.info(f"Starting memory bridge server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()