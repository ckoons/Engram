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
import re
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
    parser.add_argument("--memory-functions", action="store_true", 
                        help="Enable memory function detection in model responses")
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
            
    @staticmethod
    def get_context_memories(context: str, max_memories: int = 5):
        """Get memories relevant to a specific context."""
        try:
            return run(c(context, max_memories))
        except Exception as e:
            print(f"Error retrieving context memories: {e}")
            return []
    
    @staticmethod
    def get_semantic_memories(query: str, max_memories: int = 5):
        """Get semantically similar memories using vector search."""
        try:
            return run(v(query, max_memories))
        except Exception as e:
            print(f"Error retrieving semantic memories: {e}")
            return []
            
    @staticmethod
    def detect_memory_operations(model_output: str):
        """Detect and execute memory operations in model output.
        
        Returns:
            tuple: (cleaned_output, operation_results)
        """
        operation_results = []
        cleaned_output = model_output
        
        # Define patterns for memory operations
        memory_patterns = [
            (r"REMEMBER:\s*(.+?)(?=\n|$)", "store", MemoryHandler.store_memory),
            (r"SEARCH:\s*(.+?)(?=\n|$)", "search", MemoryHandler.search_memories),
            (r"RETRIEVE:\s*(\d+)(?=\n|$)", "retrieve", lambda n: MemoryHandler.get_recent_memories(int(n))),
            (r"CONTEXT:\s*(.+?)(?=\n|$)", "context", MemoryHandler.get_context_memories),
            (r"SEMANTIC:\s*(.+?)(?=\n|$)", "semantic", MemoryHandler.get_semantic_memories),
        ]
        
        # Check for patterns and execute corresponding functions
        for pattern, op_type, func in memory_patterns:
            matches = re.findall(pattern, model_output)
            for match in matches:
                try:
                    result = func(match)
                    operation_results.append({
                        "type": op_type,
                        "input": match,
                        "result": result
                    })
                    # Remove the operation from the output
                    cleaned_output = re.sub(pattern, "", cleaned_output, count=1)
                except Exception as e:
                    print(f"Error executing memory operation: {e}")
        
        return cleaned_output.strip(), operation_results
    
    @staticmethod
    def enhance_prompt_with_memory(user_input: str):
        """Enhance user prompt with relevant memories."""
        if not MEMORY_AVAILABLE:
            return user_input
            
        # Check if input is likely to benefit from memory augmentation
        memory_triggers = [
            "remember", "recall", "previous", "last time", "you told me", 
            "earlier", "before", "you mentioned", "what do you know about"
        ]
        
        should_augment = any(trigger in user_input.lower() for trigger in memory_triggers)
        
        if should_augment:
            # Extract potential search terms
            search_term = user_input
            if "about" in user_input.lower():
                search_term = user_input.lower().split("about")[-1].strip()
            elif "know" in user_input.lower():
                search_term = user_input.lower().split("know")[-1].strip()
                
            # Try semantic search first if available
            try:
                memories = MemoryHandler.get_semantic_memories(search_term)
            except:
                memories = []
            
            # Fall back to keyword search if needed
            if not memories:
                memories = MemoryHandler.search_memories(search_term)
            
            # Format memories for context
            if memories:
                memory_context = "Here are some relevant memories that might help with your response:\n"
                for memory in memories[:3]:  # Limit to 3 most relevant memories
                    content = memory.get("content", "")
                    if content:
                        memory_context += f"- {content}\n"
                
                # Create enhanced prompt
                enhanced_prompt = f"{memory_context}\n\nUser: {user_input}"
                return enhanced_prompt
        
        return user_input

def main():
    """Main function for the Ollama bridge."""
    args = parse_args()
    
    # Set client ID for Engram
    os.environ["ENGRAM_CLIENT_ID"] = args.client_id
    
    # Create memory handler
    memory = MemoryHandler()
    
    # Set up memory functions system prompt if requested
    if args.memory_functions and not args.system:
        args.system = """You have access to a memory system that can store and retrieve information.
To use this system, include special commands in your responses:

- To store information: REMEMBER: {information to remember}
- To search for information: SEARCH: {search term}
- To retrieve recent memories: RETRIEVE: {number of memories}
- To get context-relevant memories: CONTEXT: {context description}
- To find semantically similar memories: SEMANTIC: {query}

Your memory commands will be processed automatically. Be sure to format your memory commands exactly as shown.
Always place memory commands on their own line to ensure they are processed correctly."""
    
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
        
        # Add user message to chat history, optionally enhancing with memory
    if MEMORY_AVAILABLE and args.memory_functions:
        # If using memory functions, enhance with memory
        enhanced_input = memory.enhance_prompt_with_memory(user_input)
        if enhanced_input != user_input:
            print("\n[Memory system: Enhancing prompt with relevant memories]")
            chat_history.append({"role": "user", "content": enhanced_input})
        else:
            chat_history.append({"role": "user", "content": user_input})
    else:
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
        # Check for memory operations in response if memory functions are enabled
        if MEMORY_AVAILABLE and args.memory_functions:
            cleaned_message, memory_ops = memory.detect_memory_operations(assistant_message)
            if memory_ops:
                print("\n[Memory system: Detected memory operations]")
                for op in memory_ops:
                    op_type = op.get("type", "")
                    op_input = op.get("input", "")
                    if op_type == "store":
                        print(f"[Memory system: Remembered '{op_input}']")
                    elif op_type in ["search", "retrieve", "context", "semantic"]:
                        print(f"[Memory system: {op_type.capitalize()} results for '{op_input}']")
                        results = op.get("result", [])
                        for i, result in enumerate(results[:3]):
                            content = result.get("content", "")
                            if content:
                                print(f"  {i+1}. {content[:80]}...")
                # Use the cleaned message for display and history
                assistant_message = cleaned_message
                
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