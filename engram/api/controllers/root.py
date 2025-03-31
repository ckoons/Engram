"""
Root Controllers - Root endpoints and health checks

This module provides the root and health check endpoints.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from engram.core.memory import MemoryService, HAS_MEM0
from engram.api.models import HealthResponse
from engram.api.dependencies import get_client_id, get_memory_service, get_memory_manager

# Configure logging
logger = logging.getLogger("engram.api.controllers.root")

# Create router
router = APIRouter(tags=["Root"])


@router.get("/")
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


@router.get("/health")
async def health_check(client_id: str = Depends(get_client_id)):
    """Check if all memory services are running."""
    memory_manager = await get_memory_manager()
    
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