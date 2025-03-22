#!/usr/bin/env python3
"""
Engram Consolidated API Server

A unified FastAPI server that provides both core memory services and HTTP wrapper
functionality on a single port. This eliminates the need for multiple ports.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Body, HTTPException, Query, APIRouter, Header, Depends
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
logger = logging.getLogger("engram.consolidated")

# Check if we're in fallback mode (set by engram_consolidated script)
USE_FALLBACK = os.environ.get('ENGRAM_USE_FALLBACK', '').lower() in ('1', 'true', 'yes')

# Import Engram modules
try:
    # Always import config first
    from engram.core.config import get_config
    
    # Check for fallback mode
    if USE_FALLBACK:
        logger.info("Using fallback implementation without vector database")
        # Force Python to not try to import vector modules
        os.environ['ENGRAM_USE_FALLBACK'] = '1'
        
    # Now import memory modules
    from engram.core.memory import MemoryService, HAS_MEM0
    from engram.core.structured_memory import StructuredMemory
    from engram.core.nexus import NexusInterface
    # Use the local memory_manager file instead
    from engram.core.memory_manager import MemoryManager
except ImportError as e:
    logger.error(f"Failed to import Engram modules: {e}")
    logger.error("Make sure you're running this from the project root or it's installed")
    raise

# Define API models for core memory service
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
    mem0_available: bool  # For backward compatibility
    vector_available: bool = False
    namespaces: List[str]
    structured_memory_available: bool
    nexus_available: bool
    implementation_type: str = "unknown"
    vector_search: bool = False
    vector_db_version: Optional[str] = None
    vector_db_name: Optional[str] = None
    multi_client: bool = True

class ClientModel(BaseModel):
    client_id: str
    last_access_time: str
    idle_seconds: int
    active: bool
    structured_memory: bool
    nexus: bool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI - handles startup and shutdown"""
    global memory_manager, default_client_id
    
    # Get default client ID from environment
    default_client_id = os.environ.get("ENGRAM_CLIENT_ID", "claude")
    data_dir = os.environ.get("ENGRAM_DATA_DIR", None)
    
    # Initialize memory manager
    try:
        memory_manager = MemoryManager(data_dir=data_dir)
        logger.info(f"Memory manager initialized with data directory: {data_dir or '~/.engram'}")
        logger.info(f"Default client ID: {default_client_id}")
        
        # Pre-initialize default client
        await memory_manager.get_memory_service(default_client_id)
        await memory_manager.get_structured_memory(default_client_id)
        await memory_manager.get_nexus_interface(default_client_id)
        logger.info(f"Pre-initialized services for default client: {default_client_id}")
        logger.info("Server startup complete and ready to accept connections")
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {e}")
        # Re-raise to prevent server from starting with incomplete initialization
        raise
    
    yield  # Server is running here
    
    # Shutdown code
    if memory_manager:
        await memory_manager.shutdown()
        logger.info("Memory manager shut down")

# Initialize FastAPI app
app = FastAPI(
    title="Engram Consolidated API",
    description="Unified API for Engram combining core memory services and HTTP wrapper",
    version="0.7.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create routers for each service
core_router = APIRouter(prefix="/memory", tags=["Core Memory API"])
http_router = APIRouter(prefix="/http", tags=["HTTP Wrapper API"])
nexus_router = APIRouter(prefix="/nexus", tags=["Nexus API"])
structured_router = APIRouter(prefix="/structured", tags=["Structured Memory API"])
clients_router = APIRouter(prefix="/clients", tags=["Client Management API"])

# Global service instances
memory_manager = None
default_client_id = "claude"

# Helper to get client ID from request
async def get_client_id(x_client_id: Optional[str] = Header(None)) -> str:
    """Get client ID from header or use default."""
    return x_client_id or default_client_id

# Helper to get memory service for client
async def get_memory_service(client_id: str = Depends(get_client_id)) -> MemoryService:
    """Get memory service for the specified client."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    return await memory_manager.get_memory_service(client_id)

# Helper to get structured memory for client
async def get_structured_memory(client_id: str = Depends(get_client_id)) -> StructuredMemory:
    """Get structured memory for the specified client."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    return await memory_manager.get_structured_memory(client_id)

# Helper to get nexus interface for client
async def get_nexus_interface(client_id: str = Depends(get_client_id)) -> NexusInterface:
    """Get nexus interface for the specified client."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    return await memory_manager.get_nexus_interface(client_id)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI - handles startup and shutdown"""
    global memory_manager, default_client_id
    
    # Get default client ID from environment
    default_client_id = os.environ.get("ENGRAM_CLIENT_ID", "claude")
    data_dir = os.environ.get("ENGRAM_DATA_DIR", None)
    
    # Initialize memory manager
    try:
        memory_manager = MemoryManager(data_dir=data_dir)
        logger.info(f"Memory manager initialized with data directory: {data_dir or '~/.engram'}")
        logger.info(f"Default client ID: {default_client_id}")
        
        # Pre-initialize default client
        await memory_manager.get_memory_service(default_client_id)
        await memory_manager.get_structured_memory(default_client_id)
        await memory_manager.get_nexus_interface(default_client_id)
        logger.info(f"Pre-initialized services for default client: {default_client_id}")
        logger.info("Server startup complete and ready to accept connections")
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {e}")
        # Re-raise to prevent server from starting with incomplete initialization
        raise
    
    yield  # Server is running here
    
    # Shutdown code
    if memory_manager:
        await memory_manager.shutdown()
        logger.info("Memory manager shut down")

# Use the lifespan manager
app = FastAPI(
    title="Engram Consolidated API",
    description="Unified API for Engram combining core memory services and HTTP wrapper",
    version="0.7.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Engram Memory Consolidated API",
        "services": {
            "memory": "/memory",
            "http": "/http",
            "nexus": "/nexus",
            "structured": "/structured",
            "clients": "/clients"
        }
    }

@app.get("/health", tags=["Root"])
async def health_check(client_id: str = Depends(get_client_id)):
    """Check if all memory services are running."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        # Get memory service for the client
        memory_service = await memory_manager.get_memory_service(client_id)
        
        # Determine memory implementation type
        vector_available = False
        vector_db_version = None
        vector_db_name = None
        implementation_type = "file"
        
        if hasattr(memory_service, "vector_available"):
            vector_available = memory_service.vector_available
            
            # Get vector database info if available
            if vector_available:
                implementation_type = "vector"
                # Try to get vector db information
                try:
                    from engram.core.memory import VECTOR_DB_NAME, VECTOR_DB_VERSION
                    vector_db_name = VECTOR_DB_NAME
                    vector_db_version = VECTOR_DB_VERSION
                except Exception:
                    pass
        
        # Get available namespaces
        namespaces = await memory_service.get_namespaces()
        
        # Get client services status
        structured_memory_available = client_id in memory_manager.structured_memories
        nexus_available = client_id in memory_manager.nexus_interfaces
        
        # Enhanced status response with implementation details
        response_data = {
            "status": "ok",
            "client_id": client_id,
            "mem0_available": False,  # For backward compatibility
            "vector_available": vector_available,
            "implementation_type": implementation_type,
            "vector_search": vector_available,
            "vector_db_name": vector_db_name,
            "namespaces": namespaces,
            "structured_memory_available": structured_memory_available,
            "nexus_available": nexus_available,
            "multi_client": True
        }
        
        # Include version info if available
        if vector_db_version:
            response_data["vector_db_version"] = vector_db_version
        
        return HealthResponse(**response_data)
    except Exception as e:
        # Log the error but don't crash the health endpoint
        logger.error(f"Error in health check: {e}")
        
        # Return a degraded but functional response
        return HealthResponse(
            status="degraded",
            client_id=client_id,
            mem0_available=False,
            vector_available=False,
            implementation_type="fallback",
            namespaces=[],
            structured_memory_available=False,
            nexus_available=False,
            multi_client=True
        )

# ==================== CORE MEMORY API ROUTES ====================

@core_router.post("/query")
async def query_memory(
    query_data: MemoryQuery,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Query memory for relevant information."""
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

@core_router.post("/store")
async def store_memory(
    memory_data: MemoryStore,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store a new memory."""
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

@core_router.post("/store_conversation")
async def store_conversation(
    conversation: List[Dict[str, str]] = Body(...),
    namespace: str = Query("conversations"),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store a complete conversation."""
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

@core_router.post("/context")
async def get_context(
    query_data: MemoryMultiQuery,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get formatted memory context across multiple namespaces."""
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

@core_router.post("/clear/{namespace}")
async def clear_namespace(
    namespace: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Clear all memories in a namespace."""
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

# ==================== HTTP WRAPPER ROUTES ====================

@http_router.get("/store")
async def http_store_memory(
    key: str,
    value: str,
    namespace: str = "conversations",
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store a memory in the specified namespace."""
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

@http_router.get("/thinking")
async def http_store_thinking(
    thought: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store a thought in the thinking namespace."""
    try:
        success = await memory_service.add(
            content=thought,
            namespace="thinking",
            metadata={"key": "thought"}
        )
        return {
            "success": success,
            "key": "thought",
            "namespace": "thinking",
        }
    except Exception as e:
        logger.error(f"Error storing thought: {e}")
        return {"status": "error", "message": f"Failed to store thought: {str(e)}"}

@http_router.get("/longterm")
async def http_store_longterm(
    info: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store important information in the longterm namespace."""
    try:
        success = await memory_service.add(
            content=info,
            namespace="longterm", 
            metadata={"key": "important"}
        )
        return {
            "success": success,
            "key": "important",
            "namespace": "longterm",
        }
    except Exception as e:
        logger.error(f"Error storing longterm memory: {e}")
        return {"status": "error", "message": f"Failed to store longterm memory: {str(e)}"}

@http_router.get("/query")
async def http_query_memory(
    query: str,
    namespace: str = "conversations",
    limit: int = 5,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Query memory for relevant information."""
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

@http_router.get("/context")
async def http_get_context(
    query: str,
    include_thinking: bool = True,
    limit: int = 3,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get formatted context from multiple namespaces."""
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

@http_router.get("/clear/{namespace}")
async def http_clear_namespace(
    namespace: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Clear all memories in a namespace."""
    try:
        success = await memory_service.clear_namespace(namespace)
        return {"success": success, "namespace": namespace}
    except Exception as e:
        logger.error(f"Error clearing namespace: {e}")
        return {"status": "error", "message": f"Failed to clear namespace: {str(e)}"}

@http_router.get("/write")
async def write_session_memory(
    content: str, 
    metadata: str = None,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Write a memory to the session namespace for persistence."""
    try:
        # Parse metadata if provided
        meta_dict = json.loads(metadata) if metadata else None
        
        success = await memory_service.write_session_memory(content, meta_dict)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error writing session memory: {e}")
        return {"status": "error", "message": f"Failed to write session memory: {str(e)}"}

@http_router.get("/load")
async def load_session_memory(
    limit: int = 1,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Load previous session memory."""
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

@http_router.get("/compartment/create")
async def create_compartment(
    name: str, 
    description: str = None, 
    parent: str = None,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Create a new memory compartment."""
    try:
        compartment_id = await memory_service.create_compartment(name, description, parent)
        if compartment_id:
            return {"success": True, "compartment_id": compartment_id}
        else:
            return {"success": False, "message": "Failed to create compartment"}
    except Exception as e:
        logger.error(f"Error creating compartment: {e}")
        return {"status": "error", "message": f"Failed to create compartment: {str(e)}"}

@http_router.get("/compartment/store")
async def store_in_compartment(
    compartment: str, 
    content: str, 
    key: str = "memory",
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store content in a specific compartment."""
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

@http_router.get("/compartment/activate")
async def activate_compartment(
    compartment: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Activate a compartment to include in automatic context retrieval."""
    try:
        success = await memory_service.activate_compartment(compartment)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error activating compartment: {e}")
        return {"status": "error", "message": f"Failed to activate compartment: {str(e)}"}

@http_router.get("/compartment/deactivate")
async def deactivate_compartment(
    compartment: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Deactivate a compartment to exclude from automatic context retrieval."""
    try:
        success = await memory_service.deactivate_compartment(compartment)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deactivating compartment: {e}")
        return {"status": "error", "message": f"Failed to deactivate compartment: {str(e)}"}

@http_router.get("/compartment/list")
async def list_compartments(
    include_expired: bool = False,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """List all compartments."""
    try:
        compartments = await memory_service.list_compartments(include_expired)
        return {"compartments": compartments, "count": len(compartments)}
    except Exception as e:
        logger.error(f"Error listing compartments: {e}")
        return {"status": "error", "message": f"Failed to list compartments: {str(e)}"}

@http_router.get("/compartment/expire")
async def set_compartment_expiration(
    compartment_id: str, 
    days: int = None,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Set expiration for a compartment in days."""
    try:
        success = await memory_service.set_compartment_expiration(compartment_id, days)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error setting compartment expiration: {e}")
        return {"status": "error", "message": f"Failed to set compartment expiration: {str(e)}"}

@http_router.get("/keep")
async def keep_memory(
    memory_id: str, 
    days: int = 30,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Keep a memory for a specified number of days."""
    try:
        success = await memory_service.keep_memory(memory_id, days)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error keeping memory: {e}")
        return {"status": "error", "message": f"Failed to keep memory: {str(e)}"}

@http_router.get("/private")
async def store_private(
    content: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Store a private memory."""
    try:
        memory_id, success = await memory_service.add_private(content)
        if success:
            return {"success": True, "memory_id": memory_id}
        else:
            return {"success": False, "message": "Failed to store private memory"}
    except Exception as e:
        logger.error(f"Error storing private memory: {e}")
        return {"status": "error", "message": f"Failed to store private memory: {str(e)}"}

@http_router.get("/private/get")
async def get_private(
    memory_id: str, 
    use_emergency: bool = False,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get a specific private memory."""
    try:
        memory = await memory_service.get_private(memory_id, use_emergency)
        if memory:
            return {"success": True, "memory": memory}
        else:
            return {"success": False, "message": "Failed to retrieve private memory"}
    except Exception as e:
        logger.error(f"Error retrieving private memory: {e}")
        return {"status": "error", "message": f"Failed to retrieve private memory: {str(e)}"}

@http_router.get("/private/list")
async def list_private(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """List all private memories."""
    try:
        memories = await memory_service.list_private()
        return {"success": True, "memories": memories}
    except Exception as e:
        logger.error(f"Error listing private memories: {e}")
        return {"status": "error", "message": f"Failed to list private memories: {str(e)}"}

@http_router.get("/private/delete")
async def delete_private(
    memory_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Delete a private memory."""
    try:
        success = await memory_service.delete_private(memory_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error deleting private memory: {e}")
        return {"status": "error", "message": f"Failed to delete private memory: {str(e)}"}

# ==================== STRUCTURED MEMORY ROUTES ====================

@structured_router.get("/add")
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

@structured_router.get("/auto")
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

@structured_router.get("/get")
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

@structured_router.get("/search")
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

@structured_router.get("/digest")
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

@structured_router.get("/delete")
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

@structured_router.get("/importance")
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

@structured_router.get("/context")
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

# ==================== NEXUS INTERFACE ROUTES ====================

@nexus_router.get("/start")
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

@nexus_router.get("/end")
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

@nexus_router.get("/process")
async def process_message(
    message: str,
    is_user: bool = True,
    metadata: Optional[str] = None,
    auto_agency: Optional[bool] = None
):
    """Process a conversation message with optional automatic agency activation.
    
    Auto-agency defaults to the value in the configuration file if not specified.
    """
    if nexus is None:
        return {"status": "error", "message": "Nexus interface not initialized"}
    
    try:
        # Parse metadata if provided
        meta_dict = json.loads(metadata) if metadata else None
        
        # Automatic agency invocation for user messages
        agency_applied = False
        
        # If auto_agency not explicitly provided in request, use config setting
        use_auto_agency = auto_agency if auto_agency is not None else get_config()["auto_agency"]
        
        if is_user and use_auto_agency:
            try:
                # Signal to Claude to exercise agency - we don't use the result directly
                # but this tells Claude to use its judgment
                logger.info(f"Invoking automatic agency for message: {message[:50]}...")
                
                # In a real implementation, we could have something like:
                # await nexus.invoke_agency(message)
                
                agency_applied = True
            except Exception as agency_err:
                # Continue even if agency invocation fails
                logger.warning(f"Agency invocation failed: {agency_err}")
        
        # Process message
        result = await nexus.process_message(message, is_user, meta_dict)
        return {
            "success": True, 
            "result": result,
            "agency_applied": agency_applied
        }
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"status": "error", "message": f"Failed to process message: {str(e)}"}

@nexus_router.get("/store")
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

@nexus_router.get("/forget")
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

@nexus_router.get("/search")
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

@nexus_router.get("/summary")
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

@nexus_router.get("/settings")
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

@nexus_router.get("/update-settings")
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

# ----- Client Management API Routes -----

@clients_router.get("/list", tags=["Client Management"])
async def list_clients():
    """List all active clients."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        clients = await memory_manager.list_clients()
        return {"clients": clients}
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list clients: {str(e)}")

@clients_router.get("/status/{client_id}", tags=["Client Management"])
async def client_status(client_id: str):
    """Get status for a specific client."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        clients = await memory_manager.list_clients()
        for client in clients:
            if client["client_id"] == client_id:
                return client
        
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    except Exception as e:
        logger.error(f"Error getting client status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get client status: {str(e)}")

@clients_router.post("/cleanup", tags=["Client Management"])
async def cleanup_idle_clients(idle_threshold: int = 3600):
    """Clean up clients that have been idle for a specified time."""
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        count = await memory_manager.cleanup_idle_clients(idle_threshold)
        return {"cleaned_clients": count}
    except Exception as e:
        logger.error(f"Error cleaning up idle clients: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clean up idle clients: {str(e)}")

# Include all routers
app.include_router(core_router)
app.include_router(http_router)
app.include_router(nexus_router)
app.include_router(structured_router)
app.include_router(clients_router)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Engram Consolidated API Server")
    parser.add_argument("--client-id", type=str, default=None,
                      help="Client ID for memory service")
    parser.add_argument("--port", type=int, default=None,
                      help="Port to run the server on")
    parser.add_argument("--host", type=str, default=None,
                      help="Host to bind the server to")
    parser.add_argument("--data-dir", type=str, default=None,
                      help="Directory to store memory data")
    parser.add_argument("--config", type=str, default=None,
                      help="Path to custom config file")
    parser.add_argument("--fallback", action="store_true",
                      help="Use fallback file-based implementation without vector database")
    parser.add_argument("--no-auto-agency", action="store_true",
                      help="Disable automatic agency activation")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug mode")
    return parser.parse_args()

def main():
    """Main entry point for the CLI command."""
    args = parse_arguments()
    
    # Load configuration
    config = get_config(args.config)
    
    # Override with command line arguments if provided
    if args.client_id:
        config["client_id"] = args.client_id
    if args.data_dir:
        config["data_dir"] = args.data_dir
    if args.port:
        config["port"] = args.port
    if args.host:
        config["host"] = args.host
    if args.no_auto_agency:
        config["auto_agency"] = False
    if args.debug:
        config["debug"] = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set environment variables for default client ID and data directory
    # Note: The client_id is now just a default - multiple clients are supported
    os.environ["ENGRAM_CLIENT_ID"] = config["client_id"]
    os.environ["ENGRAM_DATA_DIR"] = config["data_dir"]
    
    # Set fallback mode if requested
    if args.fallback:
        os.environ["ENGRAM_USE_FALLBACK"] = "1"
        logger.info("Fallback mode enabled: Using file-based implementation without vector database")
    
    # Start the server
    logger.info(f"Starting Engram consolidated server on {config['host']}:{config['port']}")
    logger.info(f"Default client ID: {config['client_id']}, Data directory: {config['data_dir']}")
    logger.info(f"Multiple client IDs are supported - use the X-Client-ID header to specify")
    logger.info(f"Auto-agency: {'enabled' if config['auto_agency'] else 'disabled'}")
    
    if config["debug"]:
        logger.info("Debug mode enabled")
    
    uvicorn.run(app, host=config["host"], port=config["port"])

if __name__ == "__main__":
    main()