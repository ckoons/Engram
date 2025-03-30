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
    
# Import Ollama system prompts
try:
    # Try local import first
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    
    from ollama_system_prompts import (
        get_memory_system_prompt,
        get_communication_system_prompt, 
        get_combined_system_prompt,
        get_model_capabilities
    )
    SYSTEM_PROMPTS_AVAILABLE = True
except ImportError:
    print("Warning: Ollama system prompts not available")
    SYSTEM_PROMPTS_AVAILABLE = False

# Ollama API settings
OLLAMA_API_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_URL = f"{OLLAMA_API_HOST}/api/chat"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ollama Bridge for Engram Memory")
    parser.add_argument("model", type=str, help="Ollama model to use (e.g., llama3:8b)")
    parser.add_argument("--system", type=str, help="Custom system prompt (overrides defaults)", default="")
    parser.add_argument("--temperature", type=float, help="Temperature (0.0-1.0)", default=0.7)
    parser.add_argument("--top-p", type=float, help="Top-p sampling", default=0.9)
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens to generate", default=2048)
    parser.add_argument("--client-id", type=str, help="Engram client ID", default="ollama")
    parser.add_argument("--memory-functions", action="store_true", 
                        help="Enable memory function detection in model responses")
    parser.add_argument("--prompt-type", type=str, choices=["memory", "communication", "combined"], 
                        default="combined", help="Type of system prompt to use")
    parser.add_argument("--available-models", type=str, nargs="+", 
                        help="List of available AI models for communication", 
                        default=["Claude"])
    parser.add_argument("--hermes-integration", action="store_true",
                        help="Enable Hermes integration for centralized database services")
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
    
    def __init__(self, client_id="ollama", use_hermes=False):
        """Initialize with client ID."""
        self.client_id = client_id
        self.sender_persona = "Echo"  # Default persona
        self.use_hermes = use_hermes
        
        # Dialog mode settings
        self.dialog_mode = False
        self.dialog_target = None
        self.dialog_type = None
        self.last_check_time = 0
        
        # Try to get persona based on model name if available
        if "SYSTEM_PROMPTS_AVAILABLE" in globals() and SYSTEM_PROMPTS_AVAILABLE:
            try:
                model_name = self.client_id.split('-')[0]  # Extract model base name
                self.sender_persona = get_model_capabilities(model_name)["persona"]
            except Exception as e:
                print(f"Error getting persona for {client_id}: {e}")
        
        # Initialize Hermes integration if requested
        if use_hermes:
            # Check if Hermes integration is available
            try:
                from hermes.utils.database_helper import DatabaseClient
                os.environ["ENGRAM_USE_HERMES"] = "1"
                print("\033[92mEnabled Hermes integration for memory services\033[0m")
            except ImportError:
                print("\033[93mHermes integration requested but not available\033[0m")
                print("\033[93mFalling back to standard memory service\033[0m")
                self.use_hermes = False
    
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
    
    def _handle_send_message(self, recipient: str, message: str):
        """Handle sending a message to another AI."""
        try:
            # Import AI communication functions
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            try:
                from ai_communication import send_message, run as ai_run
            except ImportError:
                # Fallback implementation
                from datetime import datetime
                
                async def send_message(sender, recipient, message, thread_id=None):
                    """Send a message from one AI to another."""
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Determine the appropriate tag based on sender/recipient
                    if sender.lower() == "claude" and recipient.lower() == "echo":
                        tag = "CLAUDE_TO_ECHO"
                    elif sender.lower() == "echo" and recipient.lower() == "claude":
                        tag = "ECHO_TO_CLAUDE"
                    else:
                        tag = f"{sender.upper()}_TO_{recipient.upper()}"
                    
                    # Add thread_id if provided
                    thread_part = f" [Thread: {thread_id}]" if thread_id else ""
                    
                    # Include tag information in the message itself to make search easier
                    memory_text = f"{tag}: [{timestamp}]{thread_part} {tag}:{sender}:{recipient} {message}"
                    
                    await m(memory_text)
                    return {"status": "sent", "timestamp": timestamp, "thread_id": thread_id}
            
            # Standardize recipient name
            if recipient.lower() in ["claude", "claude-3", "anthropic", "claude3"]:
                recipient = "claude"
            
            # Send the message using AI communication
            result = run(send_message(self.sender_persona, recipient, message))
            return result
        except Exception as e:
            print(f"Error sending message to {recipient}: {e}")
            return {"error": str(e)}
    
    def _handle_check_messages(self, sender: str):
        """Handle checking for messages from a specific sender."""
        try:
            # Import AI communication functions
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            try:
                from ai_communication import get_messages, run as ai_run
            except ImportError:
                # Simple fallback using direct memory search
                async def get_messages(tag, limit=5, thread_id=None):
                    """Simple fallback to get messages with a tag."""
                    return await k(tag)
            
            # Standardize sender name
            if sender.lower() in ["claude", "claude-3", "anthropic", "claude3"]:
                sender = "claude"
                tag = "CLAUDE_TO_ECHO"
            else:
                tag = f"{sender.upper()}_TO_{self.sender_persona.upper()}"
            
            # Get messages from the sender
            messages = run(get_messages(tag, limit=5))
            
            # Store message summary as a memory for the model to see
            if messages:
                summary = f"Received {len(messages)} messages from {sender}:\n"
                for i, msg in enumerate(messages[:3]):
                    content = msg.get("content", "")
                    if content:
                        # Try to extract just the message part
                        try:
                            parts = content.split("] ")
                            if len(parts) > 1:
                                # Get everything after the tag and timestamp
                                msg_text = parts[-1]
                                # Remove the TAG:SENDER:RECIPIENT prefix if present
                                if ":" in msg_text and len(msg_text.split(" ", 1)) > 1:
                                    msg_text = msg_text.split(" ", 1)[1]
                            else:
                                msg_text = content
                        except:
                            msg_text = content
                        
                        summary += f"{i+1}. {msg_text[:100]}...\n"
                
                # Store this summary for the model to see in its next response
                self.store_memory(summary)
            else:
                self.store_memory(f"No recent messages found from {sender}.")
            
            return {"count": len(messages) if messages else 0}
        except Exception as e:
            print(f"Error checking messages from {sender}: {e}")
            return {"error": str(e)}
    
    def _handle_reply_message(self, recipient: str, message: str):
        """Handle replying to a message from another AI."""
        # This is similar to sending a message but might include context of previous messages
        try:
            # First check for recent messages to establish context
            check_result = self._handle_check_messages(recipient)
            
            # Then send the reply
            send_result = self._handle_send_message(recipient, message)
            
            # Combine results
            return {
                "checked": check_result,
                "sent": send_result
            }
        except Exception as e:
            print(f"Error replying to {recipient}: {e}")
            return {"error": str(e)}
    
    def _handle_broadcast_message(self, message: str):
        """Handle broadcasting a message to all available AIs."""
        try:
            # Default recipients
            recipients = ["claude"]
            
            # Try to get available models from system
            try:
                # This assumes we're running in a context where available_models might be defined
                if "MODEL_CAPABILITIES" in globals():
                    recipients = list(MODEL_CAPABILITIES.keys())
                    recipients = [r for r in recipients if r != "default" and r != self.client_id]
            except:
                pass
            
            # Send message to each recipient
            results = {}
            for recipient in recipients:
                result = self._handle_send_message(recipient, message)
                results[recipient] = result
            
            return {
                "recipients": recipients,
                "results": results
            }
        except Exception as e:
            print(f"Error broadcasting message: {e}")
            return {"error": str(e)}
            
    def _handle_dialog_mode(self, recipient: str):
        """
        Handle entering dialog mode with a specific AI or with all AIs (*).
        This function will inform the user that dialog mode has been activated,
        but the actual implementation is handled in the main function.
        
        Args:
            recipient: The client ID to dialog with, or '*' for all
        
        Returns:
            Dict with dialog mode status
        """
        try:
            dialog_target = recipient
            
            # Check if using wildcard
            if dialog_target == "*":
                dialog_message = "Entering dialog mode with ALL available AI models"
                dialog_type = "all"
            else:
                dialog_message = f"Entering dialog mode with {dialog_target}"
                dialog_type = "specific"
            
            # Store the dialog target for the main loop to use
            self.dialog_mode = True
            self.dialog_target = dialog_target
            self.dialog_type = dialog_type
            
            # Return message to display to user
            return {
                "status": "active",
                "dialog_with": dialog_target,
                "type": dialog_type,
                "message": dialog_message
            }
            
        except Exception as e:
            print(f"Error entering dialog mode: {e}")
            return {"error": str(e)}
            
    def detect_memory_operations(self, model_output: str):
        """Detect and execute memory operations in model output.
        
        Returns:
            tuple: (cleaned_output, operation_results)
        """
        operation_results = []
        cleaned_output = model_output
        
        # Define patterns for memory operations
        memory_patterns = [
            (r"(?:REMEMBER:|(?:\*\*)?REMEMBER(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "store", MemoryHandler.store_memory),
            (r"(?:SEARCH:|(?:\*\*)?SEARCH(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "search", MemoryHandler.search_memories),
            (r"(?:RETRIEVE:|(?:\*\*)?RETRIEVE(?:\*\*)?:?)\s*(\d+)(?=\n|$)", "retrieve", lambda n: MemoryHandler.get_recent_memories(int(n))),
            (r"(?:CONTEXT:|(?:\*\*)?CONTEXT(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "context", MemoryHandler.get_context_memories),
            (r"(?:SEMANTIC:|(?:\*\*)?SEMANTIC(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "semantic", MemoryHandler.get_semantic_memories),
            (r"(?:FORGET:|(?:\*\*)?FORGET(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "forget", lambda info: MemoryHandler.store_memory(f"FORGET/IGNORE: {info}")),
            (r"(?:LIST:|(?:\*\*)?LIST(?:\*\*)?:?)\s*(\d+)(?=\n|$)", "list", lambda n: MemoryHandler.get_recent_memories(int(n))),
            (r"(?:SUMMARIZE:|(?:\*\*)?SUMMARIZE(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "summarize", MemoryHandler.search_memories),
        ]
        
        # Define patterns for communication operations with methods from self instance
        comm_patterns = [
            (r"(?:SEND TO\s+(\w+):|(?:\*\*)?SEND TO\s+(\w+)(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "send", self._handle_send_message),
            (r"(?:CHECK MESSAGES FROM\s+(\w+)|(?:\*\*)?CHECK MESSAGES FROM\s+(\w+)(?:\*\*)?)", "check", self._handle_check_messages),
            (r"(?:REPLY TO\s+(\w+):|(?:\*\*)?REPLY TO\s+(\w+)(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "reply", self._handle_reply_message),
            (r"(?:BROADCAST:|(?:\*\*)?BROADCAST(?:\*\*)?:?)\s*(.+?)(?=\n|$)", "broadcast", self._handle_broadcast_message),
            (r"(?:DIALOG\s+(\w+|\*)|(?:\*\*)?DIALOG\s+(\w+|\*)(?:\*\*)?)", "dialog", self._handle_dialog_mode),
        ]
        
        # Combine memory and communication patterns
        all_patterns = memory_patterns + comm_patterns
        
        # Check for patterns and execute corresponding functions
        for pattern, op_type, func in all_patterns:
            try:
                if op_type in ["send", "reply", "broadcast"]:
                    # Special handling for communication patterns with multiple capture groups
                    if op_type == "send":
                        # Pattern: SEND TO recipient: message
                        matches = re.finditer(pattern, model_output)
                        for match in matches:
                            groups = match.groups()
                            recipient = groups[0] or groups[1]  # Either first or second group will have the recipient
                            message = groups[2] if len(groups) > 2 else ""
                            try:
                                result = func(recipient, message)
                                operation_results.append({
                                    "type": op_type,
                                    "input": f"to {recipient}: {message}",
                                    "result": result
                                })
                                # Remove the operation from the output
                                cleaned_output = cleaned_output.replace(match.group(0), "", 1)
                            except Exception as e:
                                print(f"Error executing communication operation: {e}")
                    
                    elif op_type == "reply":
                        # Pattern: REPLY TO recipient: message
                        matches = re.finditer(pattern, model_output)
                        for match in matches:
                            groups = match.groups()
                            recipient = groups[0] or groups[1]
                            message = groups[2] if len(groups) > 2 else ""
                            try:
                                result = func(recipient, message)
                                operation_results.append({
                                    "type": op_type,
                                    "input": f"to {recipient}: {message}",
                                    "result": result
                                })
                                # Remove the operation from the output
                                cleaned_output = cleaned_output.replace(match.group(0), "", 1)
                            except Exception as e:
                                print(f"Error executing communication operation: {e}")
                    
                    elif op_type == "broadcast":
                        # Pattern: BROADCAST: message
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
                                print(f"Error executing communication operation: {e}")
                
                elif op_type == "check":
                    # Pattern: CHECK MESSAGES FROM recipient
                    matches = re.finditer(pattern, model_output)
                    for match in matches:
                        groups = match.groups()
                        recipient = groups[0] or groups[1]
                        try:
                            result = func(recipient)
                            operation_results.append({
                                "type": op_type,
                                "input": f"from {recipient}",
                                "result": result
                            })
                            # Remove the operation from the output
                            cleaned_output = cleaned_output.replace(match.group(0), "", 1)
                        except Exception as e:
                            print(f"Error executing communication operation: {e}")
                
                else:
                    # Standard pattern handling for memory operations
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
            except Exception as e:
                print(f"Error processing pattern {pattern}: {e}")
        
        # Clean up extra newlines caused by removal
        cleaned_output = re.sub(r'\n{3,}', '\n\n', cleaned_output)
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
    
    # Create memory handler with client ID and Hermes integration if enabled
    memory = MemoryHandler(client_id=args.client_id, use_hermes=args.hermes_integration)
    
    # Make it globally available for error recovery
    global memory_handler
    memory_handler = memory
    
    # Set up system prompt
    if not args.system:  # Only if user didn't provide a custom system prompt
        if SYSTEM_PROMPTS_AVAILABLE:
            # Use our standardized system prompts
            if args.prompt_type == "memory":
                args.system = get_memory_system_prompt(args.model)
            elif args.prompt_type == "communication":
                args.system = get_communication_system_prompt(args.model, args.available_models)
            else:  # default to combined
                args.system = get_combined_system_prompt(args.model, args.available_models)
            
            print(f"Using standardized {args.prompt_type} system prompt for {args.model}")
        else:
            # Fallback to basic memory system prompt if our module isn't available
            args.system = """You have access to a memory system that can store and retrieve information.
To use this system, include special commands in your responses:

- To store information: REMEMBER: {information to remember}
- To search for information: SEARCH: {search term}
- To retrieve recent memories: RETRIEVE: {number of memories}
- To get context-relevant memories: CONTEXT: {context description}
- To find semantically similar memories: SEMANTIC: {query}

Your memory commands will be processed automatically. The command format is flexible:
- Standard format: REMEMBER: information
- Markdown format: **REMEMBER**: information
- With or without colons: REMEMBER information

Always place memory commands on their own line to ensure they are processed correctly.
When you use these commands, they will be processed and removed from your visible response."""
    
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
                
                try:
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
                except EOFError:
                    print("\nDetected EOF during input. Continuing without recent memories...")
            else:
                print("No recent memories found.")
        except Exception as e:
            print(f"Error loading recent memories: {e}")
    
    # Main chat loop
    while True:
        try:
            # Check for messages in dialog mode
            if memory.dialog_mode and memory.dialog_target:
                current_time = time.time()
                # Only check messages every 2 seconds to avoid spamming
                if current_time - memory.last_check_time >= 2:
                    memory.last_check_time = current_time
                    
                    # Check for new messages based on dialog mode type
                    if memory.dialog_type == "all":
                        print("\n[Dialog] Checking for messages from all models...")
                        # Try to list all connections and check each one
                        try:
                            from engram.cli.comm_quickmem import lc, gm, run
                            connections = run(lc())
                            new_messages_found = False
                            
                            for conn in connections:
                                conn_id = conn.get("id", "")
                                if conn_id and conn_id != memory.client_id:
                                    messages = run(gm(conn_id, 3, False))
                                    if messages and not isinstance(messages, dict):
                                        new_messages_found = True
                                        for msg in messages:
                                            print(f"\n[Dialog] From {conn_id}: {msg.get('message', '')}")
                                            
                                            # Auto-reply if the message contains a question
                                            content = msg.get('message', '')
                                            if '?' in content:
                                                # Process the message through Ollama
                                                chat_history.append({"role": "user", "content": f"Message from {conn_id}: {content}"})
                                                # Call Ollama API
                                                response = call_ollama_api(
                                                    model=args.model,
                                                    messages=chat_history,
                                                    system=args.system,
                                                    temperature=args.temperature,
                                                    top_p=args.top_p,
                                                    max_tokens=args.max_tokens
                                                )
                                                
                                                if "message" in response:
                                                    ai_reply = response["message"]["content"]
                                                    print(f"\n[Dialog] Auto-replying to {conn_id}...")
                                                    memory._handle_reply_message(conn_id, ai_reply)
                                                    chat_history.append({"role": "assistant", "content": ai_reply})
                            
                            if not new_messages_found:
                                # Don't spam "no messages" - only show occasionally
                                if int(current_time) % 10 == 0:  # Show every ~10 seconds
                                    print("\n[Dialog] No new messages")
                        except Exception as e:
                            print(f"\n[Dialog] Error checking messages: {e}")
                    else:
                        # Check from specific target
                        target = memory.dialog_target
                        if target:
                            try:
                                from engram.cli.comm_quickmem import gm, run
                                messages = run(gm(target, 3, False))
                                if messages and not isinstance(messages, dict):
                                    for msg in messages:
                                        print(f"\n[Dialog] From {target}: {msg.get('message', '')}")
                                        
                                        # Auto-reply if the message contains a question
                                        content = msg.get('message', '')
                                        if '?' in content:
                                            # Process the message through Ollama
                                            chat_history.append({"role": "user", "content": f"Message from {target}: {content}"})
                                            # Call Ollama API
                                            response = call_ollama_api(
                                                model=args.model,
                                                messages=chat_history,
                                                system=args.system,
                                                temperature=args.temperature,
                                                top_p=args.top_p,
                                                max_tokens=args.max_tokens
                                            )
                                            
                                            if "message" in response:
                                                ai_reply = response["message"]["content"]
                                                print(f"\n[Dialog] Auto-replying to {target}...")
                                                memory._handle_reply_message(target, ai_reply)
                                                chat_history.append({"role": "assistant", "content": ai_reply})
                                else:
                                    # Don't spam "no messages" - only show occasionally
                                    if int(current_time) % 10 == 0:  # Show every ~10 seconds
                                        print(f"\n[Dialog] No new messages from {target}")
                            except Exception as e:
                                print(f"\n[Dialog] Error checking messages from {target}: {e}")
            
            # Get user input with timeout to support dialog mode
            user_input = None
            if memory.dialog_mode:
                import select
                import sys
                
                # Check if there's input available with a 1-second timeout
                ready, _, _ = select.select([sys.stdin], [], [], 1)
                if ready:
                    user_input = input("\nYou: ")
                
                # Continue the loop if no input and we're in dialog mode
                if not user_input:
                    continue
            else:
                user_input = input("\nYou: ")
            
            # Handle special commands
            if user_input and user_input.lower() in ['exit', '/quit']:
                memory.dialog_mode = False  # Ensure dialog mode is turned off
                break
            elif user_input and user_input.lower() == '/reset':
                chat_history = []
                print("Chat history reset.")
                continue
            elif user_input and user_input.lower() == '/dialog_off':
                memory.dialog_mode = False
                memory.dialog_target = None
                memory.dialog_type = None
                print("\n[Dialog mode deactivated]")
                continue
            elif user_input and user_input.lower().startswith('/remember '):
                # Save to memory
                memory_text = user_input[10:]
                if MEMORY_AVAILABLE:
                    result = memory.store_memory(memory_text)
                    print(f"Saved to memory: {memory_text}")
                else:
                    print("Memory functions not available.")
                continue
            elif user_input and user_input.lower() == '/memories':
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
            elif user_input and user_input.lower().startswith('/search '):
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
            elif not user_input:
                # This happens when in dialog mode and no input is available
                continue
                
        except EOFError:
            print("\nDetected EOF. Exiting...")
            break
        
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
            # Check for memory and communication operations in response if enabled
            if MEMORY_AVAILABLE and args.memory_functions:
                try:
                    # Pass the assistant message to memory handler for processing
                    cleaned_message, ops = memory.detect_memory_operations(assistant_message)
                except Exception as e:
                    print(f"Error processing memory operations: {e}")
                    # Use a global fallback handler if the original one fails
                    try:
                        if 'memory_handler' in globals():
                            print("Using fallback memory handler")
                            cleaned_message, ops = memory_handler.detect_memory_operations(assistant_message)
                        else:
                            print("No fallback handler available")
                            cleaned_message, ops = assistant_message, []
                    except Exception as e2:
                        print(f"Fallback handler also failed: {e2}")
                        cleaned_message, ops = assistant_message, []
                        
                if ops:
                    # Separate memory and communication operations
                    memory_ops = [op for op in ops if op.get("type", "") in 
                                 ["store", "search", "retrieve", "context", "semantic", 
                                  "forget", "list", "summarize"]]
                    
                    comm_ops = [op for op in ops if op.get("type", "") in 
                               ["send", "check", "reply", "broadcast"]]
                    
                    # Report memory operations
                    if memory_ops:
                        print("\n[Memory system: Detected memory operations]")
                        for op in memory_ops:
                            op_type = op.get("type", "")
                            op_input = op.get("input", "")
                            if op_type == "store":
                                print(f"[Memory system: Remembered '{op_input}']")
                            elif op_type == "forget":
                                print(f"[Memory system: Marked to forget '{op_input}']")
                            elif op_type in ["search", "retrieve", "context", "semantic", "list", "summarize"]:
                                print(f"[Memory system: {op_type.capitalize()} results for '{op_input}']")
                                results = op.get("result", [])
                                for i, result in enumerate(results[:3]):
                                    content = result.get("content", "")
                                    if content:
                                        print(f"  {i+1}. {content[:80]}...")
                    
                    # Report communication operations
                    if comm_ops:
                        print("\n[Communication system: Detected communication operations]")
                        for op in comm_ops:
                            op_type = op.get("type", "")
                            op_input = op.get("input", "")
                            
                            if op_type == "send":
                                print(f"[Communication system: Sent message {op_input}]")
                            elif op_type == "check":
                                count = op.get("result", {}).get("count", 0)
                                print(f"[Communication system: Checked messages {op_input} (found {count})]")
                            elif op_type == "reply":
                                print(f"[Communication system: Replied {op_input}]")
                            elif op_type == "broadcast":
                                recipients = op.get("result", {}).get("recipients", [])
                                count = len(recipients)
                                print(f"[Communication system: Broadcasted message to {count} recipients]")
                    
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