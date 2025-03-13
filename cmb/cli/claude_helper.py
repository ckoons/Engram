#!/usr/bin/env python3
"""
Claude Memory Helper

A simple library for Claude to interact with the Memory Bridge.
Import this in Claude Code sessions to access persistent memory.

Usage:
  from claude_helper import query_memory, store_memory, store_thinking, store_longterm
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional, Union

# Default Memory Bridge URL
MEMORY_BRIDGE_URL = os.environ.get("CMB_URL", "http://127.0.0.1:8000")

def check_health() -> Dict[str, Any]:
    """
    Check if the memory bridge is running and properly configured.
    
    Returns:
        Dictionary with health status information
    """
    try:
        response = requests.get(f"{MEMORY_BRIDGE_URL}/health")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to connect to Memory Bridge. Make sure the server is running."
        }

def query_memory(query: str, namespace: str = "conversations", limit: int = 5) -> Dict[str, Any]:
    """
    Query memory for relevant information.
    
    Args:
        query: The search query
        namespace: Memory namespace to search in ("conversations", "thinking", "longterm", "projects")
        limit: Maximum number of memories to return
        
    Returns:
        Dictionary with memory results
    """
    try:
        response = requests.post(
            f"{MEMORY_BRIDGE_URL}/query",
            json={"query": query, "namespace": namespace, "limit": limit}
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Format results for nice display
        if result.get("count", 0) > 0:
            print(f"\nFound {result.get('count', 0)} memories in '{namespace}' namespace:")
            for i, memory in enumerate(result.get("results", [])):
                content = memory.get("content", "")
                # Truncate long content for display
                if len(content) > 300:
                    content = content[:297] + "..."
                print(f"{i+1}. {content}\n")
        else:
            print(f"\nNo memories found in '{namespace}' namespace for query: '{query}'")
        
        return result
    except Exception as e:
        print(f"\nError querying memory: {e}")
        return {
            "error": str(e),
            "message": "Failed to query memory",
            "count": 0,
            "results": []
        }

def store_memory(key: str, value: str, namespace: str = "conversations") -> Dict[str, Any]:
    """
    Store a memory in the specified namespace.
    
    Args:
        key: A unique identifier or category for the memory
        value: The information to store
        namespace: Namespace to store in ("conversations", "thinking", "longterm", "projects")
        
    Returns:
        Dictionary with success status
    """
    try:
        response = requests.post(
            f"{MEMORY_BRIDGE_URL}/store",
            json={"key": key, "value": value, "namespace": namespace}
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            print(f"\nSuccessfully stored memory in '{namespace}' namespace")
        else:
            print(f"\nFailed to store memory in '{namespace}' namespace")
        
        return result
    except Exception as e:
        print(f"\nError storing memory: {e}")
        return {
            "error": str(e),
            "message": "Failed to store memory",
            "success": False
        }

def store_thinking(thought: str) -> Dict[str, Any]:
    """
    Store Claude's internal thought process.
    
    Args:
        thought: The thought to remember
        
    Returns:
        Dictionary with success status
    """
    return store_memory("thought", thought, namespace="thinking")

def store_longterm(information: str) -> Dict[str, Any]:
    """
    Store important information in long-term memory.
    
    Args:
        information: The important information to remember permanently
        
    Returns:
        Dictionary with success status
    """
    return store_memory("important", information, namespace="longterm")

def store_project_info(project: str, information: str) -> Dict[str, Any]:
    """
    Store project-specific information.
    
    Args:
        project: The project name or identifier
        information: The project information to remember
        
    Returns:
        Dictionary with success status
    """
    return store_memory(f"project:{project}", information, namespace="projects")

def store_conversation(conversation: List[Dict[str, str]], namespace: str = "conversations") -> Dict[str, Any]:
    """
    Store a complete conversation.
    
    Args:
        conversation: List of message objects with 'role' and 'content'
        namespace: Namespace to store in (usually "conversations")
        
    Returns:
        Dictionary with success status
    """
    try:
        response = requests.post(
            f"{MEMORY_BRIDGE_URL}/store_conversation",
            json=conversation,
            params={"namespace": namespace}
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            print(f"\nSuccessfully stored conversation with {len(conversation)} messages")
        else:
            print(f"\nFailed to store conversation")
        
        return result
    except Exception as e:
        print(f"\nError storing conversation: {e}")
        return {
            "error": str(e),
            "message": "Failed to store conversation",
            "success": False
        }

def get_context(query: str, include_thinking: bool = True, limit: int = 3) -> str:
    """
    Get formatted memory context for the current conversation.
    
    Args:
        query: The current conversation topic/query
        include_thinking: Whether to include Claude's thoughts
        limit: Maximum memories per namespace
        
    Returns:
        Formatted context string ready to include in prompts
    """
    try:
        # Determine which namespaces to include
        namespaces = ["conversations", "longterm"]
        if include_thinking:
            namespaces.append("thinking")
        
        response = requests.post(
            f"{MEMORY_BRIDGE_URL}/context",
            json={
                "query": query,
                "namespaces": namespaces,
                "limit": limit
            }
        )
        response.raise_for_status()
        
        result = response.json()
        context = result.get("context", "")
        
        # Only print context if it's not empty
        if context:
            print(f"\nRetrieved memory context for prompt enhancement")
        
        return context
    except Exception as e:
        print(f"\nError getting context: {e}")
        return ""

def clear_memories(namespace: str) -> Dict[str, Any]:
    """
    Clear all memories in a namespace.
    
    Args:
        namespace: The namespace to clear
        
    Returns:
        Dictionary with success status
    """
    try:
        response = requests.post(f"{MEMORY_BRIDGE_URL}/clear/{namespace}")
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success", False):
            print(f"\nSuccessfully cleared all memories in '{namespace}' namespace")
        else:
            print(f"\nFailed to clear memories in '{namespace}' namespace")
        
        return result
    except Exception as e:
        print(f"\nError clearing memories: {e}")
        return {
            "error": str(e),
            "message": f"Failed to clear memories in '{namespace}' namespace",
            "success": False
        }

if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Claude Memory Helper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check health status")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query memory")
    query_parser.add_argument("query", help="Query string")
    query_parser.add_argument("--namespace", default="conversations", help="Memory namespace to search")
    query_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store memory")
    store_parser.add_argument("key", help="Memory key")
    store_parser.add_argument("value", help="Memory value")
    store_parser.add_argument("--namespace", default="conversations", help="Memory namespace to store in")
    
    # Store thinking command
    thinking_parser = subparsers.add_parser("thinking", help="Store a thought")
    thinking_parser.add_argument("thought", help="Thought to remember")
    
    # Store longterm command
    longterm_parser = subparsers.add_parser("longterm", help="Store important information")
    longterm_parser.add_argument("information", help="Important information to remember")
    
    # Store project command
    project_parser = subparsers.add_parser("project", help="Store project information")
    project_parser.add_argument("project", help="Project name")
    project_parser.add_argument("information", help="Project information")
    
    # Context command
    context_parser = subparsers.add_parser("context", help="Get memory context")
    context_parser.add_argument("query", help="Query string")
    context_parser.add_argument("--no-thinking", action="store_true", help="Exclude thinking memories")
    context_parser.add_argument("--limit", type=int, default=3, help="Maximum number of memories per namespace")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear memories in a namespace")
    clear_parser.add_argument("namespace", help="Namespace to clear")
    
    args = parser.parse_args()
    
    if args.command == "health":
        result = check_health()
        print(json.dumps(result, indent=2))
    
    elif args.command == "query":
        result = query_memory(args.query, namespace=args.namespace, limit=args.limit)
        if "error" not in result:
            print(f"\nFull result:\n{json.dumps(result, indent=2)}")
    
    elif args.command == "store":
        result = store_memory(args.key, args.value, namespace=args.namespace)
        print(json.dumps(result, indent=2))
    
    elif args.command == "thinking":
        result = store_thinking(args.thought)
        print(json.dumps(result, indent=2))
    
    elif args.command == "longterm":
        result = store_longterm(args.information)
        print(json.dumps(result, indent=2))
    
    elif args.command == "project":
        result = store_project_info(args.project, args.information)
        print(json.dumps(result, indent=2))
    
    elif args.command == "context":
        result = get_context(args.query, include_thinking=not args.no_thinking, limit=args.limit)
        print(result)
    
    elif args.command == "clear":
        result = clear_memories(args.namespace)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()
        sys.exit(1)