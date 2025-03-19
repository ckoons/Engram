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
    "numpy<2.0.0",  # Force numpy 1.x for compatibility with sentence-transformers
    "chromadb>=0.6.0",  # Primary vector database (preferred)
    "qdrant-client>=1.7.0",  # Alternative vector database (legacy)
    "sentence-transformers>=2.2.2",  # For generating embeddings
]

def check_packages():
    """Check if required packages are installed and importable."""
    missing_packages = []
    
    # Special check for NumPy version
    try:
        import numpy
        numpy_version = numpy.__version__
        major_version = int(numpy_version.split('.')[0])
        if major_version >= 2:
            logger.warning(f"❌ NumPy version {numpy_version} detected. Version 1.x is required for compatibility.")
            missing_packages.append("numpy<2.0.0")
        else:
            logger.info(f"✅ NumPy version {numpy_version} is compatible")
    except ImportError:
        logger.warning("❌ NumPy is not installed")
        missing_packages.append("numpy<2.0.0")
    
    for package in REQUIRED_PACKAGES:
        if package.startswith("numpy"):
            continue  # Already checked NumPy above
            
        package_name = package.split('>=')[0].split('==')[0].split('<')[0]
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
    # First try ChromaDB (preferred)
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        # Check version if available
        try:
            version = chromadb.__version__
        except AttributeError:
            version = "unknown"
            
        logger.info(f"ChromaDB installed (version: {version})")
        
        # Create temporary client
        with tempfile.TemporaryDirectory() as temp_dir:
            client = chromadb.PersistentClient(path=temp_dir)
            
            # Create a test collection
            collection = client.create_collection(
                name="test_collection",
                embedding_function=None  # We'll provide embeddings explicitly
            )
            
            logger.info("✅ Successfully created ChromaDB test collection")
            
            # Test sentence transformer model loading
            logger.info("Testing sentence transformer model loading...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Test creating an embedding
            test_embedding = model.encode("This is a test sentence")
            embedding_size = len(test_embedding)
            
            if embedding_size > 0:
                logger.info(f"✅ Successfully created embedding of size {embedding_size}")
                
                # Test adding to collection
                collection.add(
                    ids=["test1"],
                    embeddings=[test_embedding.tolist()],
                    documents=["This is a test sentence"],
                    metadatas=[{"source": "test"}]
                )
                logger.info("✅ Successfully added document to ChromaDB")
                
                # Test querying
                results = collection.query(
                    query_embeddings=[test_embedding.tolist()],
                    n_results=1
                )
                
                if len(results["ids"][0]) > 0:
                    logger.info("✅ Successfully queried ChromaDB")
                    return True
                else:
                    logger.error("❌ Failed to query ChromaDB")
                    return False
            else:
                logger.error("❌ Failed to create embedding")
                return False
    
    except Exception as e:
        logger.warning(f"ChromaDB verification failed: {e}")
        logger.warning("Falling back to Qdrant verification")
        
        # Fall back to Qdrant if ChromaDB isn't available
        try:
            import qdrant_client
            from sentence_transformers import SentenceTransformer
            
            # Some packages don't expose __version__ directly
            try:
                version = qdrant_client.__version__
            except AttributeError:
                version = "unknown"
                
            logger.info(f"Qdrant client installed (version: {version})")
            
            # Test creating a simple client
            with tempfile.TemporaryDirectory() as temp_dir:
                # For qdrant-client 0.11.9, the parameter is 'location', not 'path'
                try:
                    client = qdrant_client.QdrantClient(path=temp_dir)
                except TypeError:
                    # Try with location parameter for older clients
                    client = qdrant_client.QdrantClient(location=temp_dir)
                
                # Create a simple collection
                vector_size = 384  # Default for "all-MiniLM-L6-v2"
                
                # Try the simplest approach with dimension parameter (works with newer clients)
                try:
                    client.create_collection(
                        collection_name="test_collection",
                        dimension=vector_size
                    )
                except Exception as e:
                    logger.warning(f"First collection creation attempt failed: {e}")
                    # Try direct dictionary-based config as fallback
                    try:
                        client.create_collection(
                            collection_name="test_collection",
                            vectors_config={
                                "size": vector_size,
                                "distance": "Cosine"
                            }
                        )
                    except Exception as e2:
                        logger.warning(f"Second collection creation attempt failed: {e2}")
                        # Try the approach with explicit models
                        try:
                            from qdrant_client import QdrantClient
                            from qdrant_client.http import models
                            
                            # Try to create a model without strict validation
                            logger.info("Trying alternative collection creation method...")
                            
                            # Use the raw API parameters directly
                            client.create_collection(
                                collection_name="test_collection",
                                vectors_config={"size": vector_size, "distance": "Cosine"},
                                hnsw_config=None,
                                optimizers_config=None,
                                wal_config=None,
                                on_disk_payload=False,
                                write_consistency_factor=None
                            )
                        except Exception as e3:
                            logger.error(f"All collection creation attempts failed. Last error: {e3}")
                            logger.error("This likely indicates a compatibility issue with qdrant-client and Pydantic.")
                            
                            # We'll still return True for this test, as the issue is specific to Pydantic validation
                            # not with the core vector database functionality
                            logger.warning("Proceeding with tests despite collection creation issues")
                
                # Check if the collection was created
                collections = client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if "test_collection" in collection_names:
                    logger.info("✅ Successfully created test collection with Qdrant")
                else:
                    logger.error("❌ Failed to create test collection with Qdrant")
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
        from engram.core.memory import MemoryService, HAS_VECTOR_DB, VECTOR_DB_NAME
        from engram.core.structured_memory import StructuredMemory
        
        if not HAS_VECTOR_DB:
            logger.error("❌ Vector database not recognized by Engram")
            return False
        
        logger.info(f"✅ Vector database recognized by Engram: {VECTOR_DB_NAME}")
        
        # Initialize memory service with test client ID
        client_id = f"vector_test_{os.getpid()}"
        memory = MemoryService(client_id=client_id)
        
        if not memory.vector_available:
            logger.error("❌ Vector database not available in memory service")
            return False
        
        logger.info(f"✅ Vector database ({VECTOR_DB_NAME}) available in memory service")
        
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
    parser.add_argument("--fix-numpy", action="store_true", help="Fix NumPy compatibility issues")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("ENGRAM VECTOR DATABASE SETUP")
    print("="*60 + "\n")
    
    # Check for NumPy 2.x compatibility issues
    try:
        import numpy
        numpy_version = numpy.__version__
        major_version = int(numpy_version.split('.')[0])
        if major_version >= 2:
            print(f"\n⚠️  NumPy {numpy_version} detected. This version may cause compatibility issues.")
            print("   The vector database integration requires NumPy 1.x for full compatibility.")
            print("   Run this script with --install to downgrade NumPy to a compatible version.\n")
            
            if args.fix_numpy or args.install:
                print("   Proceeding with NumPy downgrade as requested...")
            else:
                print("   To fix this issue automatically, run:")
                print("   python vector_db_setup.py --fix-numpy\n")
    except ImportError:
        pass  # NumPy not installed, will be handled by the regular package check
    
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
        try:
            if test_engram_with_vector():
                logger.info("✅ Engram vector database test successful")
            else:
                logger.error("❌ Engram vector database test failed")
                
                # Add guidance for users on how to work around the issue
                logger.info("\n" + "="*60)
                logger.info("WORKAROUND GUIDANCE")
                logger.info("="*60)
                logger.info("The vector database test failed, likely due to validation issues with the")
                logger.info("Qdrant client and Pydantic libraries. To work around this issue:")
                logger.info("")
                logger.info("1. Use the fallback mode in Engram by setting this environment variable:")
                logger.info("   export ENGRAM_USE_FALLBACK=1")
                logger.info("")
                logger.info("2. This will make Engram use the file-based memory implementation")
                logger.info("   which will work correctly without the vector database.")
                logger.info("")
                logger.info("3. When running Python scripts or commands, you can also set it inline:")
                logger.info("   ENGRAM_USE_FALLBACK=1 python your_script.py")
                logger.info("")
                logger.info("4. To enable vector database in the future, either:")
                logger.info("   - Unset the environment variable: unset ENGRAM_USE_FALLBACK")
                logger.info("   - Or set it to false: export ENGRAM_USE_FALLBACK=0")
                logger.info("="*60)
        except Exception as e:
            logger.error(f"❌ Engram vector database test failed with error: {e}")
            logger.error("Consider using fallback mode with ENGRAM_USE_FALLBACK=1")
    
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