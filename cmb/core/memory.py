#!/usr/bin/env python3
"""
Memory Service - Core memory functionality for Claude Memory Bridge

This module provides memory storage and retrieval with namespace support, allowing
Claude to maintain different types of memories (conversations, thinking, longterm).
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cmb.memory")

# Try to import mem0 for vector storage (optional dependency)
try:
    import mem0
    HAS_MEM0 = True
    logger.info("mem0 library found, using vector-based memory")
except ImportError:
    HAS_MEM0 = False
    logger.warning("mem0 library not found, using fallback memory implementation")

class MemoryService:
    """
    Memory service providing storage and retrieval across different namespaces.
    
    Supports the following namespaces:
    - conversations: Dialog history between user and Claude
    - thinking: Claude's internal thought processes
    - longterm: High-priority persistent memories
    - projects: Project-specific context
    """
    
    def __init__(self, client_id: str = "default", data_dir: Optional[str] = None):
        """
        Initialize the memory service.
        
        Args:
            client_id: Unique identifier for the client (default: "default")
            data_dir: Directory to store memory data (default: ~/.cmb)
        """
        self.client_id = client_id
        
        # Set up data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(os.path.expanduser("~/.cmb"))
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory storage
        self.fallback_memories = {}
        self.mem0_client = None
        self.mem0_available = False
        
        # Initialize mem0 if available
        if HAS_MEM0:
            try:
                # Initialize mem0 client with separate collections for each namespace
                self.mem0_client = mem0.Client(
                    client_id=f"cmb-{client_id}",
                    root_path=str(self.data_dir / "mem0")
                )
                
                # Create collections for each namespace if they don't exist
                self.namespaces = ["conversations", "thinking", "longterm", "projects"]
                for namespace in self.namespaces:
                    collection_name = f"{client_id}-{namespace}"
                    if collection_name not in self.mem0_client.list_collections():
                        self.mem0_client.create_collection(collection_name)
                
                self.mem0_available = True
                logger.info(f"Initialized mem0 for client {client_id}")
            except Exception as e:
                logger.error(f"Error initializing mem0: {e}")
                self.mem0_available = False
        
        # Initialize fallback storage
        if not self.mem0_available:
            logger.info(f"Using fallback memory implementation for client {client_id}")
            self.fallback_file = self.data_dir / f"{client_id}-memories.json"
            
            # Load existing memories if available
            if self.fallback_file.exists():
                try:
                    with open(self.fallback_file, "r") as f:
                        self.fallback_memories = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading fallback memories: {e}")
                    self.fallback_memories = {}
            
            # Initialize with empty namespaces if needed
            for namespace in ["conversations", "thinking", "longterm", "projects"]:
                if namespace not in self.fallback_memories:
                    self.fallback_memories[namespace] = []
    
    async def add(self, 
                  content: Union[str, List[Dict[str, str]]], 
                  namespace: str = "conversations", 
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a memory to storage.
        
        Args:
            content: The memory content (string or list of message objects)
            namespace: The namespace to store in (default: "conversations")
            metadata: Optional metadata for the memory
            
        Returns:
            Boolean indicating success
        """
        if namespace not in ["conversations", "thinking", "longterm", "projects"]:
            logger.warning(f"Invalid namespace: {namespace}, using 'conversations'")
            namespace = "conversations"
        
        timestamp = datetime.now().isoformat()
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata["timestamp"] = timestamp
        metadata["client_id"] = self.client_id
        
        # Convert content to string if it's a list of messages
        if isinstance(content, list):
            try:
                # Format as conversation
                content_str = "\n".join([
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
                    for msg in content
                ])
            except Exception as e:
                logger.error(f"Error formatting conversation: {e}")
                content_str = str(content)
        else:
            content_str = content
        
        # Store in mem0 if available
        if self.mem0_available:
            try:
                collection_name = f"{self.client_id}-{namespace}"
                memory_id = f"{namespace}-{int(time.time())}"
                
                self.mem0_client.add(
                    collection=collection_name,
                    documents=[content_str],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
                
                logger.debug(f"Added memory to {namespace} with ID {memory_id}")
                return True
            except Exception as e:
                logger.error(f"Error adding memory to mem0: {e}")
                # Fall back to local storage
        
        # Store in fallback memory
        try:
            memory_obj = {
                "id": f"{namespace}-{int(time.time())}",
                "content": content_str,
                "metadata": metadata
            }
            
            self.fallback_memories.setdefault(namespace, []).append(memory_obj)
            
            # Save to file
            with open(self.fallback_file, "w") as f:
                json.dump(self.fallback_memories, f, indent=2)
            
            logger.debug(f"Added memory to fallback storage in namespace {namespace}")
            return True
        except Exception as e:
            logger.error(f"Error adding memory to fallback storage: {e}")
            return False
    
    async def search(self, 
                    query: str, 
                    namespace: str = "conversations", 
                    limit: int = 5) -> Dict[str, Any]:
        """
        Search for memories based on a query.
        
        Args:
            query: The search query
            namespace: The namespace to search in (default: "conversations")
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        if namespace not in ["conversations", "thinking", "longterm", "projects"]:
            logger.warning(f"Invalid namespace: {namespace}, using 'conversations'")
            namespace = "conversations"
        
        # Search mem0 if available
        if self.mem0_available:
            try:
                collection_name = f"{self.client_id}-{namespace}"
                
                # Query the mem0 collection
                results = self.mem0_client.query(
                    collection=collection_name,
                    query=query,
                    n_results=limit
                )
                
                # Format the results
                formatted_results = []
                
                if results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                        
                        formatted_results.append({
                            "content": doc,
                            "metadata": metadata,
                            "relevance": results["distances"][0][i] if "distances" in results else None
                        })
                
                return {
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "namespace": namespace
                }
            except Exception as e:
                logger.error(f"Error searching mem0: {e}")
                # Fall back to local search
        
        # Search fallback memory
        try:
            # Simple keyword matching for fallback
            results = []
            
            for memory in self.fallback_memories.get(namespace, []):
                content = memory.get("content", "")
                if query.lower() in content.lower():
                    results.append({
                        "content": content,
                        "metadata": memory.get("metadata", {}),
                        "relevance": 1.0  # No real relevance score in fallback
                    })
            
            # Sort by timestamp (newest first) and limit results
            results.sort(
                key=lambda x: x.get("metadata", {}).get("timestamp", ""), 
                reverse=True
            )
            results = results[:limit]
            
            return {
                "results": results,
                "count": len(results),
                "namespace": namespace
            }
        except Exception as e:
            logger.error(f"Error searching fallback memory: {e}")
            return {"results": [], "count": 0, "namespace": namespace}
    
    async def get_relevant_context(self, 
                                  query: str, 
                                  namespaces: List[str] = None,
                                  limit: int = 3) -> str:
        """
        Get formatted context from multiple namespaces for a given query.
        
        Args:
            query: The query to search for
            namespaces: List of namespaces to search (default: all)
            limit: Maximum memories per namespace
            
        Returns:
            Formatted context string
        """
        if namespaces is None:
            namespaces = ["conversations", "thinking", "longterm"]
        
        all_results = []
        
        # Search each namespace
        for namespace in namespaces:
            results = await self.search(query, namespace=namespace, limit=limit)
            
            for item in results.get("results", []):
                all_results.append({
                    "namespace": namespace,
                    "content": item.get("content", ""),
                    "metadata": item.get("metadata", {})
                })
        
        # Format the context
        if not all_results:
            return ""
        
        context_parts = ["### Claude's Memory Context\n"]
        
        for namespace in namespaces:
            namespace_results = [r for r in all_results if r["namespace"] == namespace]
            
            if namespace_results:
                if namespace == "conversations":
                    context_parts.append(f"\n#### Previous Conversations\n")
                elif namespace == "thinking":
                    context_parts.append(f"\n#### Claude's Thoughts\n")
                elif namespace == "longterm":
                    context_parts.append(f"\n#### Important Information\n")
                elif namespace == "projects":
                    context_parts.append(f"\n#### Project Context\n")
                
                for i, result in enumerate(namespace_results):
                    timestamp = result.get("metadata", {}).get("timestamp", "Unknown time")
                    content = result.get("content", "")
                    
                    # Truncate long content
                    if len(content) > 500:
                        content = content[:497] + "..."
                    
                    context_parts.append(f"{i+1}. {content}\n")
        
        return "\n".join(context_parts)
    
    async def get_namespaces(self) -> List[str]:
        """Get available namespaces."""
        return ["conversations", "thinking", "longterm", "projects"]
    
    async def clear_namespace(self, namespace: str) -> bool:
        """
        Clear all memories in a namespace.
        
        Args:
            namespace: The namespace to clear
            
        Returns:
            Boolean indicating success
        """
        if namespace not in ["conversations", "thinking", "longterm", "projects"]:
            logger.warning(f"Invalid namespace: {namespace}")
            return False
        
        # Clear mem0 if available
        if self.mem0_available:
            try:
                collection_name = f"{self.client_id}-{namespace}"
                
                # Delete and recreate the collection
                self.mem0_client.delete_collection(collection_name)
                self.mem0_client.create_collection(collection_name)
                
                logger.info(f"Cleared namespace {namespace} in mem0")
            except Exception as e:
                logger.error(f"Error clearing namespace in mem0: {e}")
                return False
        
        # Clear fallback memory
        try:
            self.fallback_memories[namespace] = []
            
            # Save to file
            with open(self.fallback_file, "w") as f:
                json.dump(self.fallback_memories, f, indent=2)
            
            logger.info(f"Cleared namespace {namespace} in fallback storage")
            return True
        except Exception as e:
            logger.error(f"Error clearing namespace in fallback storage: {e}")
            return False