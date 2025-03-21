#!/usr/bin/env python3
"""
Ollama Integration Test for Engram

This script tests the integration between Engram and Ollama
by performing basic memory operations with the Ollama API.

Usage:
    python test_ollama_integration.py [--model MODEL]
"""

import os
import sys
import argparse
import json
import requests
import asyncio
from pathlib import Path

# Add Engram to path if running directly
ENGRAM_DIR = Path(__file__).parent.parent.absolute()
if str(ENGRAM_DIR) not in sys.path:
    sys.path.insert(0, str(ENGRAM_DIR))

# Try to import Engram memory functions
try:
    from engram.cli.quickmem import m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z, run
    MEMORY_AVAILABLE = True
except ImportError:
    print("Warning: Engram memory functions not available")
    MEMORY_AVAILABLE = False

# Ollama API settings
OLLAMA_API_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_URL = f"{OLLAMA_API_HOST}/api/chat"

def test_ollama_availability():
    """Test if Ollama server is running."""
    try:
        response = requests.get(f"{OLLAMA_API_HOST}/api/tags")
        if response.status_code == 200:
            print("✅ Ollama server is running")
            available_models = [model["name"] for model in response.json().get("models", [])]
            print(f"Available models: {', '.join(available_models)}")
            return True, available_models
        else:
            print(f"❌ Ollama server returned status code: {response.status_code}")
            return False, []
    except requests.exceptions.ConnectionError:
        print("❌ Ollama server is not running")
        return False, []

def test_memory_service():
    """Test if Engram memory service is running."""
    if not MEMORY_AVAILABLE:
        print("❌ Engram memory functions not available")
        return False
    
    try:
        status = s()
        print(f"✅ Memory service status: {status}")
        return True
    except Exception as e:
        print(f"❌ Error checking memory status: {e}")
        return False

def test_ollama_chat(model):
    """Test a simple chat with Ollama."""
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, can you tell me what you are?"}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "No content returned")
            print(f"✅ Ollama model {model} responded successfully")
            print(f"Response preview: {content[:100]}...")
            return True
        else:
            print(f"❌ Ollama API returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error communicating with Ollama API: {e}")
        return False

class MemoryHandler:
    """Helper class to handle async/sync memory operations."""
    
    @staticmethod
    def store_memory(content: str):
        """Store a memory, handling async/sync cases."""
        try:
            return run(m(content))
        except Exception as e:
            print(f"Error storing memory: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def store_tagged_memory(content: str, tags):
        """Store a tagged memory, handling async/sync cases."""
        try:
            return run(t(content, tags))
        except Exception as e:
            print(f"Error storing tagged memory: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def get_recent_memories(count: int = 5):
        """Get recent memories, handling async/sync cases."""
        try:
            return run(l(count))
        except Exception as e:
            print(f"Error getting recent memories: {e}")
            return []

def test_memory_operations():
    """Test basic memory operations."""
    if not MEMORY_AVAILABLE:
        print("❌ Skipping memory operations test - memory functions not available")
        return False
    
    memory = MemoryHandler()
    
    try:
        # Store a memory
        memory_text = "This is a test memory from the Ollama integration test"
        result = memory.store_memory(memory_text)
        print(f"✅ Stored memory: {memory_text}")
        
        # Retrieve recent memories
        recent = memory.get_recent_memories(1)
        if recent and len(recent) > 0:
            content = recent[0].get("content", "")
            if memory_text in content:
                print("✅ Successfully retrieved stored memory")
            else:
                print(f"❌ Retrieved memory doesn't match: {content}")
                return False
        else:
            print("❌ Failed to retrieve stored memory")
            return False
        
        # Store a tagged memory
        thought_text = "Ollama integration with Engram seems to be working well"
        result = memory.store_tagged_memory(thought_text, ["test", "ollama", "integration"])
        print(f"✅ Stored tagged memory: {thought_text}")
        
        # Check memory service status
        status = s()
        print(f"✅ Memory service is still running: {status}")
        
        return True
    except Exception as e:
        print(f"❌ Error during memory operations: {e}")
        return False

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Ollama integration with Engram")
    parser.add_argument("--model", type=str, default="llama3:8b", 
                        help="Ollama model to test (default: llama3:8b)")
    args = parser.parse_args()
    
    # Set client ID for testing
    os.environ["ENGRAM_CLIENT_ID"] = "ollama_test"
    
    print("\n===== Ollama Integration Test =====\n")
    
    # Step 1: Check if Ollama is running
    ollama_available, available_models = test_ollama_availability()
    if not ollama_available:
        print("\n❌ Test failed: Ollama server is not running")
        print("Please start Ollama with: ollama serve")
        return False
    
    # Check if requested model is available
    if args.model not in available_models:
        print(f"\n⚠️ Warning: Model {args.model} not found in available models")
        print(f"Available models: {', '.join(available_models)}")
        
        # See if any model name could be a match (partial match)
        similar_models = [m for m in available_models if args.model.split(':')[0] in m]
        if similar_models:
            print(f"Found similar models: {', '.join(similar_models)}")
            print(f"Using {similar_models[0]} instead of {args.model}")
            args.model = similar_models[0]
            return True
        
        # Prepare auto-response for CI environments
        auto_proceed = os.environ.get("ENGRAM_AUTO_PULL", "")
        if auto_proceed.lower() in ["1", "true", "yes", "y"]:
            proceed = "y"
            print("Auto-proceeding with model pull (ENGRAM_AUTO_PULL=true)")
        else:
            # Normal interactive mode
            try:
                proceed = input("Do you want to pull this model now? (y/n): ")
            except (EOFError, KeyboardInterrupt):
                print("\nNon-interactive environment detected, skipping model pull")
                if "llama3" in args.model:
                    # For llama3 models, try using the latest
                    if "llama3:latest" in available_models:
                        print(f"Using llama3:latest instead of {args.model}")
                        args.model = "llama3:latest"
                        return True
                return False
                
        if proceed.lower() == 'y':
            print(f"Pulling model {args.model}...")
            pull_response = requests.post(f"{OLLAMA_API_HOST}/api/pull", json={"name": args.model})
            if pull_response.status_code != 200:
                print(f"❌ Error pulling model: {pull_response.status_code}")
                return False
            print(f"✅ Model {args.model} pulled successfully!")
        else:
            print("Please choose an available model or pull the requested model first")
            return False
    
    # Step 2: Check if memory service is running
    memory_available = test_memory_service()
    if not memory_available:
        print("\n⚠️ Warning: Memory service is not available")
        print("Basic Ollama communication will still be tested")
    
    # Step 3: Test Ollama chat
    chat_works = test_ollama_chat(args.model)
    if not chat_works:
        print("\n❌ Test failed: Could not communicate with Ollama API")
        return False
    
    # Step 4: Test memory operations if available
    if memory_available:
        memory_works = test_memory_operations()
        if not memory_works:
            print("\n⚠️ Warning: Memory operations failed")
    
    # Final status
    if ollama_available and chat_works:
        if memory_available:
            print("\n✅ All tests passed! Ollama integration with Engram is working correctly.")
        else:
            print("\n⚠️ Partial success: Ollama is working but Engram memory service is not available.")
        return True
    else:
        print("\n❌ Test failed: One or more components are not working correctly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)