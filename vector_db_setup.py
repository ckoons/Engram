#!/usr/bin/env python3
"""
Vector Database Setup for Engram

This script installs and configures the necessary dependencies for the Engram
vector database integration. It verifies the installation, creates necessary
directories, and tests the vector database functionality.

Usage:
    python vector_db_setup.py [--install] [--test]

Options:
    --install    Install required vector database dependencies
    --test       Run vector database test after setup
"""

import os
import sys
import subprocess
import argparse
import logging
import json
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.vector_setup")

# Required packages
REQUIRED_PACKAGES = [
    "qdrant-client>=1.7.0",
    "sentence-transformers>=2.2.2",
]

def check_packages():
    """Check if required packages are installed and importable."""
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        package_name = package.split('>=')[0].split('==')[0]
        try:
            __import__(package_name.replace('-', '_'))
            logger.info(f"✅ Package {package_name} is installed")
        except ImportError:
            logger.warning(f"❌ Package {package_name} is not installed or not importable")
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """Install the specified packages using pip."""
    if not packages:
        logger.info("No packages to install")
        return True
    
    logger.info(f"Installing packages: {', '.join(packages)}")
    
    # For venv aware installation
    pip_cmd = [sys.executable, "-m", "pip", "install"] + packages
    
    try:
        result = subprocess.run(pip_cmd, check=True, capture_output=True, text=True)
        logger.info(f"Installation output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def verify_vector_db():
    """Verify that the vector database components are working properly."""
    try:
        import qdrant_client
        from sentence_transformers import SentenceTransformer
        
        logger.info(f"Qdrant client version: {qdrant_client.__version__}")
        
        # Test creating a simple client
        with tempfile.TemporaryDirectory() as temp_dir:
            client = qdrant_client.QdrantClient(path=temp_dir)
            
            # Create a simple collection
            vector_size = 384  # Default for "all-MiniLM-L6-v2"
            client.create_collection(
                collection_name="test_collection",
                vectors_config=qdrant_client.models.VectorParams(
                    size=vector_size,
                    distance=qdrant_client.models.Distance.COSINE
                )
            )
            
            # Check if the collection was created
            collections = client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if "test_collection" in collection_names:
                logger.info("✅ Successfully created test collection")
            else:
                logger.error("❌ Failed to create test collection")
                return False
        
        # Test loading a model - this will download it if not present
        logger.info("Testing sentence transformer model loading...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test creating an embedding
        test_embedding = model.encode("This is a test sentence")
        if len(test_embedding) > 0:
            logger.info(f"✅ Successfully created embedding of size {len(test_embedding)}")
            return True
        else:
            logger.error("❌ Failed to create embedding")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying vector database: {e}")
        return False

def test_engram_with_vector():
    """Test Engram with vector database integration."""
    try:
        # Import Engram modules
        from engram.core.memory import MemoryService, HAS_VECTOR_DB
        from engram.core.structured_memory import StructuredMemory
        
        if not HAS_VECTOR_DB:
            logger.error("❌ Vector database not recognized by Engram")
            return False
        
        logger.info("✅ Vector database recognized by Engram")
        
        # Initialize memory service with test client ID
        client_id = f"vector_test_{os.getpid()}"
        memory = MemoryService(client_id=client_id)
        
        if not memory.vector_available:
            logger.error("❌ Vector database not available in memory service")
            return False
        
        logger.info("✅ Vector database available in memory service")
        
        # Test adding and searching memories
        import asyncio
        
        async def test_memory():
            # Add a few test memories
            memories = [
                "Artificial intelligence is revolutionizing the world",
                "Machine learning models can identify patterns in data",
                "Neural networks are inspired by the human brain",
                "Deep learning uses multiple layers of neural networks"
            ]
            
            for i, content in enumerate(memories):
                await memory.add(content, namespace="test_vector")
                logger.info(f"Added memory {i+1}")
            
            # Search using semantic query
            search_query = "computational intelligence and algorithms"
            results = await memory.search(search_query, namespace="test_vector", limit=5)
            
            if results["count"] > 0:
                logger.info(f"✅ Successfully retrieved {results['count']} memories with semantic search")
                for i, result in enumerate(results["results"]):
                    relevance = result.get("relevance", 0)
                    content = result.get("content", "")
                    logger.info(f"  {i+1}. [Score: {relevance:.4f}] {content[:50]}...")
                return True
            else:
                logger.error("❌ No results found with semantic search")
                return False
        
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(test_memory())
        
    except Exception as e:
        logger.error(f"Error testing Engram with vector database: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Vector Database Setup for Engram")
    parser.add_argument("--install", action="store_true", help="Install required vector database dependencies")
    parser.add_argument("--test", action="store_true", help="Run vector database test after setup")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("ENGRAM VECTOR DATABASE SETUP")
    print("="*60 + "\n")
    
    # Check for required packages
    missing_packages = check_packages()
    
    # Install packages if requested
    if args.install and missing_packages:
        if not install_packages(missing_packages):
            logger.error("Failed to install required packages")
            sys.exit(1)
        
        # Re-check after installation
        missing_packages = check_packages()
        if missing_packages:
            logger.error(f"Still missing packages after installation: {missing_packages}")
            sys.exit(1)
    elif missing_packages:
        logger.warning("Some required packages are missing. Run with --install to install them.")
    
    # Verify vector database functionality
    if not missing_packages:
        logger.info("\nVerifying vector database functionality...")
        if verify_vector_db():
            logger.info("✅ Vector database verification successful")
        else:
            logger.error("❌ Vector database verification failed")
            sys.exit(1)
    
    # Test Engram with vector database
    if args.test and not missing_packages:
        logger.info("\nTesting Engram with vector database...")
        if test_engram_with_vector():
            logger.info("✅ Engram vector database test successful")
        else:
            logger.error("❌ Engram vector database test failed")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("SETUP COMPLETE")
    print("="*60)
    
    if not args.install and not args.test:
        print("\nUsage:")
        print("  - Run with --install to install required packages")
        print("  - Run with --test to test vector database functionality")
        print("  - Run with both --install --test to install and test")

if __name__ == "__main__":
    main()