"""Entry point for python -m engram"""
import os
import sys

# Add Tekton root to path if not already present
tekton_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if tekton_root not in sys.path:
    sys.path.insert(0, tekton_root)

from shared.utils.socket_server import run_component_server
from shared.utils.env_config import get_component_config

if __name__ == "__main__":
    # Get port from configuration
    config = get_component_config()
    default_port = config.engram.port if hasattr(config, 'engram') else int(os.environ.get("ENGRAM_PORT"))
    
    run_component_server(
        component_name="engram",
        app_module="engram.api.server",
        default_port=default_port,
        reload=False
    )