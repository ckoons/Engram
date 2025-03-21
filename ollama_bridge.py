#!/usr/bin/env python3
"""
Ollama Bridge for Engram Memory
This script creates a bridge between Ollama and Engram, allowing Ollama models
to use Engram's memory system.
"""

import os
import sys
import argparse
import json
import asyncio
from typing import List, Dict, Any, Optional
import requests

# Import Engram memory functions
try:
    from engram.cli.quickmem import (
        m, t, r, w, l, c, k, s, a, p, v, d, n, q, y, z,
        run  # Import the run function for executing coroutines
    )
    MEMORY_AVAILABLE = True
except ImportError:
    print("Warning: Engram memory functions not available")
    MEMORY_AVAILABLE = False

# Ollama API settings
OLLAMA_API_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_URL = f"{OLLAMA_API_HOST}/api/chat"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ollama Bridge for Engram Memory")
    parser.add_argument("model", type=str, help="Ollama model to use (e.g., llama3:8b)")
    parser.add_argument("--system", type=str, help="System prompt", default="")
    parser.add_argument("--temperature", type=float, help="Temperature (0.0-1.0)", default=0.7)
    parser.add_argument("--top-p", type=float, help="Top-p sampling", default=0.9)
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens to generate", default=2048)
    parser.add_argument("--client-id", type=str, help="Engram client ID", default="ollama")
    return parser.parse_args()

def call_ollama_api(model: str, messages: List[Dict[str, str]], 
                   system: Optional[str] = None,
                   temperature: float = 0.7, 
                   top_p: float = 0.9,
                   max_tokens: int = 2048) -> Dict[str, Any]:
    """Call the Ollama API with the given parameters."""
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens
        }
    }
    
    if system:
        payload["system"] = system
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama API: {e}")
        return {"error": str(e)}

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
    def get_recent_memories(count: int = 5):
        """Get recent memories, handling async/sync cases."""
        try:
            return run(l(count))
        except Exception as e:
            print(f"Error getting recent memories: {e}")
            return []
    
    @staticmethod
    def search_memories(query: str):
        """Search memories, handling async/sync cases."""
        try:
            return run(k(query))
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

def main():
    """Main function for the Ollama bridge."""
    args = parse_args()
    
    # Set client ID for Engram
    os.environ["ENGRAM_CLIENT_ID"] = args.client_id
    
    # Create memory handler
    memory = MemoryHandler()
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{OLLAMA_API_HOST}/api/tags")
        if response.status_code != 200:
            print(f"Error connecting to Ollama: {response.status_code}")
            sys.exit(1)
        
        # Check if model is available
        available_models = [model["name"] for model in response.json().get("models", [])]
        if args.model not in available_models:
            print(f"Warning: Model '{args.model}' not found in available models.")
            print(f"Available models: {', '.join(available_models)}")
            proceed = input("Do you want to pull this model now? (y/n): ")
            if proceed.lower() == 'y':
                print(f"Pulling model {args.model}...")
                pull_response = requests.post(f"{OLLAMA_API_HOST}/api/pull", json={"name": args.model})
                if pull_response.status_code != 200:
                    print(f"Error pulling model: {pull_response.status_code}")
                    sys.exit(1)
                print(f"Model {args.model} pulled successfully!")
            else:
                print("Please choose an available model or pull the requested model first.")
                sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Ollama is not running. Please start Ollama first.")
        sys.exit(1)
    
    # Check if memory service is running
    if MEMORY_AVAILABLE:
        try:
            status = s()
            print(f"Memory service status: {status}")
        except Exception as e:
            print(f"Error checking memory status: {e}")
            print("Warning: Memory service may not be running correctly")

    # Print welcome message
    print(f"\nOllama Bridge with Engram Memory")
    print(f"Model: {args.model}")
    print(f"Client ID: {args.client_id}")
    print(f"Type 'exit' or '/quit' to exit, '/reset' to reset chat history\n")
    
    # Initialize chat history
    chat_history = []
    
    if MEMORY_AVAILABLE:
        # Load most recent memories
        try:
            print("Recent memories:")
            recent_memories = memory.get_recent_memories(5)
            if recent_memories:
                for mem in recent_memories:
                    content = mem.get("content", "")
                    if content:
                        print(f"- {content[:80]}...")
                
                use_recent = input("Include recent memories in conversation? (y/n): ")
                if use_recent.lower() == 'y':
                    # Add memories to system prompt
                    memory_text = "Here are some recent memories that might be relevant:\n"
                    for mem in recent_memories:
                        content = mem.get("content", "")
                        if content:
                            memory_text += f"- {content}\n"
                    
                    if args.system:
                        args.system = args.system + "\n\n" + memory_text
                    else:
                        args.system = memory_text
            else:
                print("No recent memories found.")
        except Exception as e:
            print(f"Error loading recent memories: {e}")
    
    # Main chat loop
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Handle special commands
        if user_input.lower() in ['exit', '/quit']:
            break
        elif user_input.lower() == '/reset':
            chat_history = []
            print("Chat history reset.")
            continue
        elif user_input.lower().startswith('/remember '):
            # Save to memory
            memory_text = user_input[10:]
            if MEMORY_AVAILABLE:
                result = memory.store_memory(memory_text)
                print(f"Saved to memory: {memory_text}")
            else:
                print("Memory functions not available.")
            continue
        elif user_input.lower() == '/memories':
            # List recent memories
            if MEMORY_AVAILABLE:
                recent_memories = memory.get_recent_memories(5)
                print("Recent memories:")
                for mem in recent_memories:
                    content = mem.get("content", "")
                    if content:
                        print(f"- {content}")
            else:
                print("Memory functions not available.")
            continue
        elif user_input.lower().startswith('/search '):
            # Search memories
            query = user_input[8:]
            if MEMORY_AVAILABLE:
                results = memory.search_memories(query)
                print(f"Memory search results for '{query}':")
                for result in results:
                    content = result.get("content", "")
                    if content:
                        print(f"- {content}")
            else:
                print("Memory functions not available.")
            continue
        
        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_input})
        
        # Call Ollama API
        response = call_ollama_api(
            model=args.model,
            messages=chat_history,
            system=args.system,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens
        )
        
        if "error" in response:
            print(f"Error: {response['error']}")
            continue
        
        # Get assistant response
        assistant_message = response.get("message", {}).get("content", "")
        if assistant_message:
            print(f"\n{args.model}: {assistant_message}")
            
            # Add assistant message to chat history
            chat_history.append({"role": "assistant", "content": assistant_message})
            
            # Automatically save significant interactions to memory
            if MEMORY_AVAILABLE and len(user_input) > 20 and len(assistant_message) > 50:
                memory_text = f"User asked: '{user_input}' and {args.model} responded: '{assistant_message[:100]}...'"
                memory.store_memory(memory_text)
        else:
            print("Error: No response from model")

if __name__ == "__main__":
    main()