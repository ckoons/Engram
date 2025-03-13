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
    logger.info(f"Using mem0 version: {mem0.__version__}")
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
                # Initialize using the current mem0 API (MemoryClient)
                self.namespaces = ["conversations", "thinking", "longterm", "projects"]
                
                # Set up environment for local storage (if no API key present)
                os.environ["MEM0_API_KEY"] = os.environ.get("MEM0_API_KEY", "local")
                
                # Create memory client
                self.mem0_client = mem0.MemoryClient()
                
                # Create memories for each namespace
                self.namespace_memories = {}
                for namespace in self.namespaces:
                    memory_name = f"cmb-{client_id}-{namespace}"
                    
                    # Create Memory object with collection name
                    from mem0.configs.base import MemoryConfig
                    from mem0.configs.vector_store import VectorStoreConfig, QdrantConfig
                    
                    # Configure vector store with the namespace as collection name
                    vector_config = VectorStoreConfig(
                        provider="qdrant",
                        config=QdrantConfig(
                            collection_name=memory_name,
                            path=str(self.data_dir / "mem0")
                        )
                    )
                    
                    # Create memory config
                    memory_config = MemoryConfig(
                        vector_store=vector_config
                    )
                    
                    # Create memory for this namespace
                    self.namespace_memories[namespace] = mem0.Memory(config=memory_config)
                
                self.mem0_available = True
                logger.info(f"Initialized mem0 MemoryClient for client {client_id}")
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
                memory_id = f"{namespace}-{int(time.time())}"
                
                if hasattr(self, 'namespace_memories'):
                    # Using Memory API (current mem0 version)
                    memory = self.namespace_memories.get(namespace)
                    if memory:
                        # Add to memory
                        memory.add(
                            messages=content_str,
                            metadata=metadata
                        )
                        logger.debug(f"Added memory to {namespace} using Memory API")
                        return True
                
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
                    limit: int = 5,
                    check_forget: bool = True) -> Dict[str, Any]:
        """
        Search for memories based on a query.
        
        Args:
            query: The search query
            namespace: The namespace to search in (default: "conversations")
            limit: Maximum number of results to return
            check_forget: Whether to check for and filter out forgotten information
            
        Returns:
            Dictionary with search results
        """
        if namespace not in ["conversations", "thinking", "longterm", "projects"]:
            logger.warning(f"Invalid namespace: {namespace}, using 'conversations'")
            namespace = "conversations"
        
        # Search mem0 if available
        if self.mem0_available:
            try:
                formatted_results = []
                
                if hasattr(self, 'namespace_memories'):
                    # Using Memory API (current mem0 version)
                    memory = self.namespace_memories.get(namespace)
                    if memory:
                        # Search memory
                        results = memory.search(query=query, limit=limit)
                        
                        # Format the results
                        for result in results:
                            formatted_results.append({
                                "content": result.get("text", "") if isinstance(result, dict) else result,
                                "metadata": result.get("metadata", {}) if isinstance(result, dict) else {},
                                "relevance": result.get("score", 1.0) if isinstance(result, dict) else 1.0
                            })
                
                # If check_forget is enabled, get forget instructions from longterm memory
                forgotten_items = []
                if check_forget and namespace != "longterm":
                    try:
                        # Search for FORGET instructions
                        forget_results = await self.search(
                            query="FORGET/IGNORE",
                            namespace="longterm",
                            limit=100,
                            check_forget=False  # Prevent recursion
                        )
                        
                        # Extract the forgotten items
                        for item in forget_results.get("results", []):
                            content = item.get("content", "")
                            if content.startswith("FORGET/IGNORE: "):
                                forgotten_text = content[len("FORGET/IGNORE: "):]
                                forgotten_items.append(forgotten_text)
                    except Exception as e:
                        logger.error(f"Error checking for forgotten items: {e}")
                
                # Filter out forgotten items
                if forgotten_items:
                    filtered_results = []
                    for result in formatted_results:
                        should_include = True
                        content = result.get("content", "")
                        
                        # Check if any forgotten item appears in this content
                        for forgotten in forgotten_items:
                            if forgotten.lower() in content.lower():
                                # This memory contains forgotten information
                                should_include = False
                                logger.debug(f"Filtered out memory containing: {forgotten}")
                                break
                        
                        if should_include:
                            filtered_results.append(result)
                    
                    formatted_results = filtered_results
                
                return {
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "namespace": namespace,
                    "forgotten_count": len(forgotten_items) if forgotten_items else 0
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
            
            # If check_forget is enabled, filter out forgotten items from fallback too
            forgotten_items = []
            if check_forget and namespace != "longterm":
                try:
                    # Look for FORGET instructions in longterm namespace
                    for memory in self.fallback_memories.get("longterm", []):
                        content = memory.get("content", "")
                        if content.startswith("FORGET/IGNORE: "):
                            forgotten_text = content[len("FORGET/IGNORE: "):]
                            forgotten_items.append(forgotten_text)
                except Exception as e:
                    logger.error(f"Error checking for forgotten items in fallback: {e}")
            
            # Filter results if needed
            if forgotten_items:
                filtered_results = []
                for result in results:
                    should_include = True
                    content = result.get("content", "")
                    
                    # Check if any forgotten item appears in this content
                    for forgotten in forgotten_items:
                        if forgotten.lower() in content.lower():
                            # This memory contains forgotten information
                            should_include = False
                            logger.debug(f"Filtered out fallback memory containing: {forgotten}")
                            break
                    
                    if should_include:
                        filtered_results.append(result)
                
                results = filtered_results
            
            return {
                "results": results,
                "count": len(results),
                "namespace": namespace,
                "forgotten_count": len(forgotten_items) if forgotten_items else 0
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
                if hasattr(self, 'namespace_memories'):
                    # Using Memory API (current mem0 version)
                    memory = self.namespace_memories.get(namespace)
                    if memory:
                        # Clear the memory
                        memory.reset()
                        logger.info(f"Cleared namespace {namespace} in mem0 Memory")
                        return True
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