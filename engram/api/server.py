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
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add Tekton root to path if not already present
tekton_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if tekton_root not in sys.path:
    sys.path.insert(0, tekton_root)

# Import shared utils
from shared.utils.health_check import create_health_response
from shared.utils.hermes_registration import HermesRegistration, heartbeat_loop
from shared.utils.logging_setup import setup_component_logging
from shared.utils.env_config import get_component_config
from shared.utils.errors import StartupError
from shared.utils.startup import component_startup, StartupMetrics
from shared.utils.shutdown import GracefulShutdown
from shared.api import (
    create_standard_routers,
    mount_standard_routers,
    create_ready_endpoint,
    create_discovery_endpoint,
    get_openapi_configuration,
    EndpointInfo
)

# Use shared logger
logger = setup_component_logging("engram")

# Component configuration
COMPONENT_NAME = "Engram"
COMPONENT_VERSION = "0.1.0"
COMPONENT_DESCRIPTION = "Memory management system with vector search and semantic similarity"
start_time = None

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
hermes_adapter = None
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
mcp_bridge = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for Engram"""
    global is_registered_with_hermes, hermes_registration, heartbeat_task, start_time
    
    # Track startup time
    import time
    start_time = time.time()
    
    # Startup
    logger.info("Starting Engram Memory API")
    
    async def engram_startup():
        """Engram-specific startup logic"""
        try:
            # Get configuration
            config = get_component_config()
            port = config.engram.port if hasattr(config, 'engram') else int(os.environ.get("ENGRAM_PORT"))
            
            if USE_HERMES:
                try:
                    # Start Hermes integration
                    await start_hermes_integration()
                except Exception as e:
                    logger.error(f"Failed to start Hermes integration: {e}")
                    logger.warning("Continuing without Hermes integration")
            
            # Register with Hermes
            global is_registered_with_hermes, hermes_registration, heartbeat_task
            hermes_registration = HermesRegistration()
            
            logger.info(f"Attempting to register Engram with Hermes on port {port}")
            is_registered_with_hermes = await hermes_registration.register_component(
                component_name="engram",
                port=port,
                version=COMPONENT_VERSION,
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
            
            if is_registered_with_hermes:
                logger.info("Successfully registered with Hermes")
                # Start heartbeat task
                heartbeat_task = asyncio.create_task(
                    heartbeat_loop(hermes_registration, "engram", interval=30)
                )
                logger.info("Started Hermes heartbeat task")
            else:
                logger.warning("Failed to register with Hermes - continuing without registration")
            
            # Initialize FastMCP tools with Hermes bridge
            try:
                from engram.core.mcp.hermes_bridge import EngramMCPBridge
                global mcp_bridge
                mcp_bridge = EngramMCPBridge(memory_manager)
                await mcp_bridge.initialize()
                logger.info("Initialized Hermes MCP Bridge for FastMCP tools")
            except Exception as e:
                logger.warning(f"Failed to initialize MCP Bridge: {e}")
                
        except Exception as e:
            logger.error(f"Error during Engram startup: {e}", exc_info=True)
            raise StartupError(str(e), "engram", "STARTUP_FAILED")
    
    # Execute startup with metrics
    try:
        metrics = await component_startup("engram", engram_startup, timeout=30)
        logger.info(f"Engram started successfully in {metrics.total_time:.2f}s")
    except Exception as e:
        logger.error(f"Failed to start Engram: {e}")
        raise
    
    # Create shutdown handler
    shutdown = GracefulShutdown("engram")
    
    # Register cleanup tasks
    async def cleanup_hermes():
        """Cleanup Hermes registration"""
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if hermes_registration and is_registered_with_hermes:
            await hermes_registration.deregister("engram")
            logger.info("Deregistered from Hermes")
    
    async def cleanup_memory_manager():
        """Cleanup memory manager resources"""
        global memory_manager
        
        if USE_HERMES and hermes_adapter:
            try:
                await hermes_adapter.close()
            except Exception as e:
                logger.warning(f"Error closing Hermes adapter: {e}")
        
        # Shutdown memory manager if it exists
        if memory_manager:
            try:
                await memory_manager.shutdown()
                logger.info("Memory manager shut down successfully")
            except Exception as e:
                logger.warning(f"Error shutting down memory manager: {e}")
        
        logger.info("Memory manager cleanup completed")
    
    async def cleanup_heartbeat():
        """Cancel heartbeat task if running"""
        global heartbeat_task
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("Heartbeat task cancelled")
    
    async def cleanup_mcp_bridge():
        """Cleanup MCP bridge"""
        global mcp_bridge
        if mcp_bridge:
            try:
                await mcp_bridge.shutdown()
                logger.info("MCP bridge cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up MCP bridge: {e}")
    
    shutdown.register_cleanup(cleanup_heartbeat)
    shutdown.register_cleanup(cleanup_hermes)
    shutdown.register_cleanup(cleanup_memory_manager)
    shutdown.register_cleanup(cleanup_mcp_bridge)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Engram Memory API")
    await shutdown.shutdown_sequence(timeout=10)
    
    # Socket release delay for macOS
    await asyncio.sleep(0.5)

# Initialize FastAPI app with standard configuration
app = FastAPI(
    **get_openapi_configuration(
        component_name=COMPONENT_NAME,
        component_version=COMPONENT_VERSION,
        component_description=COMPONENT_DESCRIPTION
    ),
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

# Create standard routers
routers = create_standard_routers(COMPONENT_NAME)


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
@routers.root.get("/")
async def root():
    """Root endpoint returning basic service information."""
    return {
        "service": f"{COMPONENT_NAME} Memory API",
        "version": COMPONENT_VERSION,
        "description": COMPONENT_DESCRIPTION,
        "mode": "hermes" if USE_HERMES else "standalone",
        "fallback": USE_FALLBACK,
        "docs": "/api/v1/docs"
    }

@routers.root.get("/health")
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
    
    # Use standardized health response
    config = get_component_config()
    port = config.engram.port if hasattr(config, 'engram') else int(os.environ.get("ENGRAM_PORT"))
    return create_health_response(
        component_name="engram",
        port=port,
        version=COMPONENT_VERSION,
        status=health_status,
        registered=is_registered_with_hermes,
        details=details
    )

@routers.v1.post("/memory")
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

@routers.v1.get("/memory/{memory_id}")
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

@routers.v1.post("/search")
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

@routers.v1.post("/context")
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

@routers.v1.get("/namespaces")
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

@routers.v1.post("/compartments")
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

@routers.v1.get("/compartments")
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

@routers.v1.post("/compartments/{compartment_id}/activate")
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

@routers.v1.post("/compartments/{compartment_id}/deactivate")
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


# Add ready endpoint
routers.root.add_api_route(
    "/ready",
    create_ready_endpoint(
        component_name=COMPONENT_NAME,
        component_version=COMPONENT_VERSION,
        start_time=start_time or 0,
        readiness_check=lambda: memory_manager is not None
    ),
    methods=["GET"]
)

# Add discovery endpoint to v1 router
routers.v1.add_api_route(
    "/discovery",
    create_discovery_endpoint(
        component_name=COMPONENT_NAME,
        component_version=COMPONENT_VERSION,
        component_description=COMPONENT_DESCRIPTION,
        endpoints=[
            EndpointInfo(
                path="/api/v1/memory",
                method="POST",
                description="Add a memory"
            ),
            EndpointInfo(
                path="/api/v1/memory/{memory_id}",
                method="GET",
                description="Get a memory by ID"
            ),
            EndpointInfo(
                path="/api/v1/search",
                method="POST",
                description="Search memories"
            ),
            EndpointInfo(
                path="/api/v1/context",
                method="POST",
                description="Get recent context"
            ),
            EndpointInfo(
                path="/api/v1/namespaces",
                method="GET",
                description="List all namespaces"
            ),
            EndpointInfo(
                path="/api/v1/compartments",
                method="GET",
                description="List all compartments"
            )
        ],
        capabilities=[
            "memory_storage",
            "vector_search",
            "semantic_similarity",
            "memory_retrieval",
            "conversation_memory"
        ],
        dependencies={
            "hermes": "http://localhost:8001"
        },
        metadata={
            "vector_support": not USE_FALLBACK,
            "storage_type": "vector" if not USE_FALLBACK else "simple",
            "documentation": "/api/v1/docs"
        }
    ),
    methods=["GET"]
)

# Mount standard routers
mount_standard_routers(app, routers)

# Import and include MCP router if available
try:
    from engram.api.fastmcp_endpoints import mcp_router
    app.include_router(mcp_router)
    logger.info("FastMCP endpoints added to Engram API")
except ImportError as e:
    logger.warning(f"FastMCP endpoints not available: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Engram API Server")
    parser.add_argument("--client-id", type=str, default=None,
                      help="Default client ID (default: 'default')")
    parser.add_argument("--port", type=int, default=None,
                      help="Port to run the server on (default: from env config)")
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
    config = get_component_config()
    host = args.host or os.environ.get("ENGRAM_HOST", "127.0.0.1")
    port = args.port or (config.engram.port if hasattr(config, 'engram') else int(os.environ.get("ENGRAM_PORT")))
    
    # Start the server with socket reuse
    logger.info(f"Starting Engram API server on {host}:{port}")
    from shared.utils.socket_server import run_with_socket_reuse
    run_with_socket_reuse(
        "engram.api.server:app",
        host=host,
        port=port,
        timeout_graceful_shutdown=3,
        server_header=False,
        access_log=False
    )

if __name__ == "__main__":
    main()