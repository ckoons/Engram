"""
Engram API Server

A unified FastAPI server that provides memory services for both
standalone mode and Hermes integration.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add Tekton root to path if not already present
tekton_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if tekton_root not in sys.path:
    sys.path.insert(0, tekton_root)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.api.server")

# Import shared utils with correct path
try:
    from shared.utils.health_check import create_health_response
    from shared.utils.hermes_registration import HermesRegistration, heartbeat_loop
except ImportError as e:
    logger.warning(f"Could not import shared utils: {e}")
    create_health_response = None
    HermesRegistration = None

# Check if we're in debug mode
DEBUG = os.environ.get('ENGRAM_DEBUG', '').lower() in ('1', 'true', 'yes')
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled")

# Check if we're in fallback mode
USE_FALLBACK = os.environ.get('ENGRAM_USE_FALLBACK', '').lower() in ('1', 'true', 'yes')
if USE_FALLBACK:
    logger.info("Fallback mode enabled - using file-based storage")

# Check if we're in Hermes mode
USE_HERMES = os.environ.get('ENGRAM_MODE', '').lower() == 'hermes'
if USE_HERMES:
    logger.info("Hermes integration mode enabled")

# Import Engram core modules
try:
    from engram.core.memory_manager import MemoryManager
    from engram.core.memory.base import MemoryService
except ImportError as e:
    logger.error(f"Failed to import Engram core modules: {e}")
    logger.error("Make sure Engram is properly installed or in your PYTHONPATH")
    sys.exit(1)

# Initialize memory manager
default_client_id = os.environ.get("ENGRAM_CLIENT_ID", "default")
data_dir = os.environ.get("ENGRAM_DATA_DIR", None)

try:
    memory_manager = MemoryManager(data_dir=data_dir)
    logger.info(f"Memory manager initialized with data directory: {data_dir or '~/.engram'}")
    logger.info(f"Default client ID: {default_client_id}")
except Exception as e:
    logger.error(f"Failed to initialize memory manager: {e}")
    memory_manager = None
    sys.exit(1)

# Initialize Hermes integration if enabled
if USE_HERMES:
    try:
        from engram.integrations.hermes.memory_adapter import HermesMemoryAdapter
        
        # Initialize Hermes adapter
        hermes_adapter = HermesMemoryAdapter(memory_manager)
        logger.info("Hermes memory adapter initialized")
        
        # Start Hermes integration in background task
        async def start_hermes_integration():
            try:
                await hermes_adapter.initialize()
                logger.info("Hermes integration initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Hermes integration: {e}")
        
        # We'll start this after the API server is running
    except ImportError as e:
        logger.error(f"Failed to initialize Hermes integration: {e}")
        logger.warning("Continuing without Hermes integration")
        USE_HERMES = False

# Global state for Hermes registration
is_registered_with_hermes = False
hermes_registration = None
heartbeat_task = None

# Initialize FastAPI app
app = FastAPI(
    title="Engram Memory API",
    description="API for Engram memory services",
    version="0.8.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get memory service for a client
async def get_memory_service(
    request: Request,
    x_client_id: str = Header(None)
) -> MemoryService:
    client_id = x_client_id or default_client_id
    
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    
    try:
        return await memory_manager.get_memory_service(client_id)
    except Exception as e:
        logger.error(f"Error getting memory service: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting memory service: {str(e)}")

# Define routes
@app.get("/")
async def root():
    """Root endpoint returning basic service information."""
    return {
        "service": "Engram Memory API",
        "version": "0.8.0",
        "mode": "hermes" if USE_HERMES else "standalone",
        "fallback": USE_FALLBACK
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        # Check if we can get the default memory service
        memory_service = await memory_manager.get_memory_service(default_client_id)
        
        # Try to get storage info
        storage_info = await memory_service.get_storage_info()
        
        health_status = "healthy"
        details = {
            "client_id": default_client_id,
            "storage_type": storage_info.get("storage_type", "unknown"),
            "vector_available": not USE_FALLBACK,
            "hermes_integration": USE_HERMES
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status = "unhealthy"
        details = {
            "error": str(e),
            "vector_available": not USE_FALLBACK,
            "hermes_integration": USE_HERMES
        }
    
    # Use standardized health response if available
    if create_health_response:
        return create_health_response(
            component_name="engram",
            port=8000,
            version="0.8.0",
            status=health_status,
            registered=is_registered_with_hermes,
            details=details
        )
    else:
        # Fallback to manual format
        return {
            "status": health_status,
            "version": "0.8.0",
            "timestamp": datetime.now().isoformat(),
            "component": "engram",
            "port": 8000,
            "registered_with_hermes": is_registered_with_hermes,
            "details": details
        }

@app.post("/memory")
async def add_memory(
    request: Request,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Add a memory."""
    try:
        data = await request.json()
        content = data.get("content")
        namespace = data.get("namespace", "conversations")
        metadata = data.get("metadata")
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required parameter: content"}
            )
        
        memory_id = await memory_service.add(
            content=content,
            namespace=namespace,
            metadata=metadata
        )
        
        return {
            "id": memory_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error adding memory: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error adding memory: {str(e)}"}
        )

@app.get("/memory/{memory_id}")
async def get_memory(
    memory_id: str,
    namespace: str = "conversations",
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get a memory by ID."""
    try:
        memory = await memory_service.get(memory_id, namespace)
        
        if not memory:
            return JSONResponse(
                status_code=404,
                content={"error": f"Memory {memory_id} not found in namespace {namespace}"}
            )
        
        return memory
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting memory: {str(e)}"}
        )

@app.post("/search")
async def search_memory(
    request: Request,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Search for memories."""
    try:
        data = await request.json()
        query = data.get("query")
        namespace = data.get("namespace", "conversations")
        limit = data.get("limit", 5)
        
        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required parameter: query"}
            )
        
        # Handle empty or None namespace
        if not namespace:
            namespace = "conversations"
        
        results = await memory_service.search(
            query=query,
            namespace=namespace,
            limit=limit
        )
        
        # Ensure results is always a dict with expected structure
        if not isinstance(results, dict):
            results = {"results": [], "count": 0}
        
        return results
    except Exception as e:
        logger.error(f"Error searching memory: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Error searching memory: {str(e)}"}
        )

@app.post("/context")
async def get_context(
    request: Request,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get relevant context from multiple namespaces."""
    try:
        data = await request.json()
        query = data.get("query")
        namespaces = data.get("namespaces")
        limit = data.get("limit", 3)
        
        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required parameter: query"}
            )
        
        context = await memory_service.get_relevant_context(
            query=query,
            namespaces=namespaces,
            limit=limit
        )
        
        return {"context": context}
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting context: {str(e)}"}
        )

@app.get("/namespaces")
async def list_namespaces(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """List available namespaces."""
    try:
        namespaces = await memory_service.get_namespaces()
        return namespaces
    except Exception as e:
        logger.error(f"Error listing namespaces: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error listing namespaces: {str(e)}"}
        )

@app.post("/compartments")
async def create_compartment(
    request: Request,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Create a new memory compartment."""
    try:
        data = await request.json()
        name = data.get("name")
        description = data.get("description")
        parent = data.get("parent")
        
        if not name:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required parameter: name"}
            )
        
        compartment_id = await memory_service.create_compartment(
            name=name,
            description=description,
            parent=parent
        )
        
        return {
            "id": compartment_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error creating compartment: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error creating compartment: {str(e)}"}
        )

@app.get("/compartments")
async def list_compartments(
    include_inactive: bool = False,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """List memory compartments."""
    try:
        compartments = await memory_service.list_compartments(include_inactive)
        return compartments
    except Exception as e:
        logger.error(f"Error listing compartments: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error listing compartments: {str(e)}"}
        )

@app.post("/compartments/{compartment_id}/activate")
async def activate_compartment(
    compartment_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Activate a memory compartment."""
    try:
        success = await memory_service.activate_compartment(compartment_id)
        
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": f"Compartment {compartment_id} not found"}
            )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error activating compartment {compartment_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error activating compartment: {str(e)}"}
        )

@app.post("/compartments/{compartment_id}/deactivate")
async def deactivate_compartment(
    compartment_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Deactivate a memory compartment."""
    try:
        success = await memory_service.deactivate_compartment(compartment_id)
        
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": f"Compartment {compartment_id} not found"}
            )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deactivating compartment {compartment_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error deactivating compartment: {str(e)}"}
        )

# Startup event to initialize Hermes integration if enabled
@app.on_event("startup")
async def startup_event():
    global is_registered_with_hermes, hermes_registration, heartbeat_task
    logger.info("Starting up Engram API server")
    
    if USE_HERMES:
        try:
            # Start Hermes integration
            await start_hermes_integration()
        except Exception as e:
            logger.error(f"Failed to start Hermes integration: {e}")
            logger.warning("Continuing without Hermes integration")
    
    # Register with Hermes if available
    if HermesRegistration:
        hermes_registration = HermesRegistration()
        is_registered_with_hermes = await hermes_registration.register_component(
            component_name="engram",
            port=8000,
            version="0.8.0",
            capabilities=[
                "memory_storage",
                "vector_search",
                "semantic_similarity",
                "memory_retrieval",
                "conversation_memory"
            ],
            metadata={
                "vector_support": not USE_FALLBACK,
                "storage_type": "vector" if not USE_FALLBACK else "simple",
                "hermes_integration": USE_HERMES
            }
        )
        
        # Start heartbeat task if registered
        if is_registered_with_hermes:
            heartbeat_task = asyncio.create_task(
                heartbeat_loop(hermes_registration, "engram", interval=30)
            )
            logger.info("Started Hermes heartbeat task")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global heartbeat_task
    
    # Cancel heartbeat task
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    
    # Deregister from Hermes
    if hermes_registration and is_registered_with_hermes:
        await hermes_registration.deregister("engram")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Engram API Server")
    parser.add_argument("--client-id", type=str, default=None,
                      help="Default client ID (default: 'default')")
    parser.add_argument("--port", type=int, default=None,
                      help="Port to run the server on (default: 8000)")
    parser.add_argument("--host", type=str, default=None,
                      help="Host to bind the server to (default: '127.0.0.1')")
    parser.add_argument("--data-dir", type=str, default=None,
                      help="Directory to store memory data (default: '~/.engram')")
    parser.add_argument("--fallback", action="store_true",
                      help="Use fallback file-based implementation without vector database")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug mode")
    return parser.parse_args()

def main():
    """Main entry point for the server when run directly."""
    args = parse_arguments()
    
    # Override environment variables with command line arguments if provided
    if args.client_id:
        os.environ["ENGRAM_CLIENT_ID"] = args.client_id
    
    if args.data_dir:
        os.environ["ENGRAM_DATA_DIR"] = args.data_dir
    
    if args.fallback:
        os.environ["ENGRAM_USE_FALLBACK"] = "1"
    
    if args.debug:
        os.environ["ENGRAM_DEBUG"] = "1"
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get host and port from environment or arguments using standardized port config
    from tekton.utils.port_config import get_engram_port
    host = args.host or os.environ.get("ENGRAM_HOST", "127.0.0.1")
    port = args.port or get_engram_port()
    
    # Start the server
    logger.info(f"Starting Engram API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()