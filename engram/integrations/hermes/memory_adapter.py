#!/usr/bin/env python3
"""
Hermes Memory Adapter - Integrate Engram memory with Hermes database services

This module provides a MemoryService implementation that uses Hermes's
centralized database services for storage, providing enhanced vector
search capabilities and cross-component integration.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.integrations.hermes")

# Import Hermes database client
try:
    from hermes.utils.database_helper import DatabaseClient
    from hermes.core.database_manager import DatabaseBackend
    HAS_HERMES = True
except ImportError:
    logger.warning("Hermes database services not found, using fallback implementation")
    HAS_HERMES = False


class HermesMemoryService:
    """
    Memory service implementation using Hermes database services.
    
    This class provides the same interface as Engram's MemoryService, but
    uses Hermes's centralized database services for storage and retrieval.
    """
    
    def __init__(self, client_id: str = "default", data_dir: Optional[str] = None):
        """
        Initialize the Hermes memory service.
        
        Args:
            client_id: Unique identifier for the client (default: "default")
            data_dir: Directory to store memory data (default: ~/.engram)
        """
        self.client_id = client_id
        
        # Set up data directory - maintained for compatibility with original
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(os.path.expanduser("~/.engram"))
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Available namespaces
        self.namespaces = ["conversations", "thinking", "longterm", "projects", "compartments", "session"]
        
        # Store active compartments
        self.active_compartments = []
        self.compartment_file = self.data_dir / f"{client_id}-compartments.json"
        self.compartments = self._load_compartments()
        
        # Initialize Hermes client if available
        self.hermes_available = HAS_HERMES
        self.hermes_client = None
        
        if self.hermes_available:
            try:
                # Initialize the DatabaseClient
                self.hermes_client = DatabaseClient(
                    component_id=f"engram.{client_id}",
                    data_path=str(self.data_dir),
                    config={"vector_dim": 1536}  # Default dimension for most embedding models
                )
                logger.info(f"Initialized Hermes database client for Engram ({client_id})")
            except Exception as e:
                logger.error(f"Error initializing Hermes client: {e}")
                self.hermes_available = False
        
        # Initialize fallback storage if Hermes is not available
        if not self.hermes_available:
            logger.info(f"Using fallback file-based memory implementation for client {client_id}")
            self.fallback_file = self.data_dir / f"{client_id}-memories.json"
            self.fallback_memories = {}
            
            # Load existing memories if available
            if self.fallback_file.exists():
                try:
                    with open(self.fallback_file, "r") as f:
                        self.fallback_memories = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading fallback memories: {e}")
                    self.fallback_memories = {}
            
            # Initialize with empty namespaces if needed
            for namespace in self.namespaces:
                if namespace not in self.fallback_memories:
                    self.fallback_memories[namespace] = []
                    
            # Initialize compartment storage in fallback memories
            for compartment_id in self.compartments:
                compartment_ns = f"compartment-{compartment_id}"
                if compartment_ns not in self.fallback_memories:
                    self.fallback_memories[compartment_ns] = []
    
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
        # Check if namespace is a valid base namespace or a compartment
        valid_namespaces = self.namespaces
        
        # Support compartment namespaces 
        if namespace.startswith("compartment-"):
            compartment_id = namespace[len("compartment-"):]
            if compartment_id not in self.compartments:
                logger.warning(f"Invalid compartment: {compartment_id}, using 'conversations'")
                namespace = "conversations"
        elif namespace not in valid_namespaces:
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
        
        # Generate a unique memory ID
        memory_id = f"{namespace}-{int(time.time())}-{hash(content_str) % 10000}"
        metadata["id"] = memory_id
        
        # Store in Hermes if available
        if self.hermes_available:
            try:
                # Get vector database
                vector_db = await self.hermes_client.get_vector_db(namespace=namespace)
                
                # Store the memory with its metadata
                result = await vector_db.store(
                    id=memory_id,
                    vector=None,  # Vector will be generated by the embedding model
                    metadata=metadata,
                    text=content_str
                )
                
                logger.debug(f"Added memory to Hermes vector database in namespace {namespace}")
                return result
            except Exception as e:
                logger.error(f"Error adding memory to Hermes: {e}")
                # Fall back to local storage if Hermes fails
        
        # Store in fallback memory
        try:
            memory_obj = {
                "id": memory_id,
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
        # Check if namespace is a valid base namespace or a compartment
        valid_namespaces = self.namespaces
        
        # Support compartment namespaces
        if namespace.startswith("compartment-"):
            compartment_id = namespace[len("compartment-"):]
            if compartment_id not in self.compartments:
                logger.warning(f"Invalid compartment: {compartment_id}, using 'conversations'")
                namespace = "conversations"
        elif namespace not in valid_namespaces:
            logger.warning(f"Invalid namespace: {namespace}, using 'conversations'")
            namespace = "conversations"
        
        # Get forgotten items if needed
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
        
        # Search Hermes if available
        if self.hermes_available:
            try:
                # Get vector database for this namespace
                vector_db = await self.hermes_client.get_vector_db(namespace=namespace)
                
                # Search for similar vectors
                search_results = await vector_db.search(
                    query_vector=None,  # Let Hermes generate the embedding
                    query=query,  # Provide the raw query for embedding
                    limit=limit * 2,  # Request more results to account for filtering
                    filter={}  # No filter initially
                )
                
                # Format the results
                formatted_results = []
                for result in search_results:
                    formatted_results.append({
                        "id": result.get("id", ""),
                        "content": result.get("text", ""),
                        "metadata": result.get("metadata", {}),
                        "relevance": result.get("relevance", 0.0)
                    })
                
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
                
                # Limit the results
                formatted_results = formatted_results[:limit]
                
                return {
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "namespace": namespace,
                    "forgotten_count": len(forgotten_items) if forgotten_items else 0
                }
                
            except Exception as e:
                logger.error(f"Error searching Hermes vector database: {e}")
                # Fall back to local search
        
        # Search fallback memory
        try:
            # Simple keyword matching for fallback
            results = []
            
            for memory in self.fallback_memories.get(namespace, []):
                content = memory.get("content", "")
                if query.lower() in content.lower():
                    results.append({
                        "id": memory.get("id", ""),
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
            # Include base namespaces
            namespaces = ["conversations", "thinking", "longterm"]
            
            # Add active compartments
            for compartment_id in self.active_compartments:
                namespaces.append(f"compartment-{compartment_id}")
        
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
        
        context_parts = ["### Memory Context\n"]
        
        for namespace in namespaces:
            namespace_results = [r for r in all_results if r["namespace"] == namespace]
            
            if namespace_results:
                if namespace == "conversations":
                    context_parts.append(f"\n#### Previous Conversations\n")
                elif namespace == "thinking":
                    context_parts.append(f"\n#### Thoughts\n")
                elif namespace == "longterm":
                    context_parts.append(f"\n#### Important Information\n")
                elif namespace == "projects":
                    context_parts.append(f"\n#### Project Context\n")
                elif namespace == "session":
                    context_parts.append(f"\n#### Session Memory\n")
                elif namespace == "compartments":
                    context_parts.append(f"\n#### Compartment Information\n")
                elif namespace.startswith("compartment-"):
                    compartment_id = namespace[len("compartment-"):]
                    compartment_name = self.compartments.get(compartment_id, {}).get("name", compartment_id)
                    context_parts.append(f"\n#### Compartment: {compartment_name}\n")
                
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
        base_namespaces = ["conversations", "thinking", "longterm", "projects", "compartments", "session"]
        
        # Add compartment namespaces
        compartment_namespaces = [f"compartment-{c_id}" for c_id in self.compartments]
        
        return base_namespaces + compartment_namespaces
    
    async def clear_namespace(self, namespace: str) -> bool:
        """
        Clear all memories in a namespace.
        
        Args:
            namespace: The namespace to clear
            
        Returns:
            Boolean indicating success
        """
        valid_namespaces = ["conversations", "thinking", "longterm", "projects", "compartments", "session"]
        
        # Support compartment namespaces
        if namespace.startswith("compartment-"):
            compartment_id = namespace[len("compartment-"):]
            if compartment_id not in self.compartments:
                logger.warning(f"Invalid compartment: {compartment_id}")
                return False
        elif namespace not in valid_namespaces:
            logger.warning(f"Invalid namespace: {namespace}")
            return False
        
        # Clear Hermes storage if available
        if self.hermes_available:
            try:
                # Delete all documents in the namespace
                vector_db = await self.hermes_client.get_vector_db(namespace=namespace)
                await vector_db.delete()  # Delete all vectors in this namespace
                
                logger.info(f"Cleared namespace {namespace} in Hermes storage")
                return True
            except Exception as e:
                logger.error(f"Error clearing namespace in Hermes storage: {e}")
                # Fall back to basic storage
        
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
    
    async def create_compartment(self, name: str, description: str = None, parent: str = None) -> Optional[str]:
        """
        Create a new memory compartment.
        
        Args:
            name: Name of the compartment
            description: Optional description
            parent: Optional parent compartment ID for hierarchical organization
            
        Returns:
            Compartment ID if successful, None otherwise
        """
        try:
            # Generate a unique ID for the compartment
            compartment_id = f"{int(time.time())}-{name.lower().replace(' ', '-')}"
            
            # Create compartment data
            compartment_data = {
                "id": compartment_id,
                "name": name,
                "description": description,
                "parent": parent,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "expiration": None  # No expiration by default
            }
            
            # Store in compartments
            self.compartments[compartment_id] = compartment_data
            
            # Save to file
            self._save_compartments()
            
            # Store the compartment info in the compartments namespace
            await self.add(
                content=f"Compartment: {name} (ID: {compartment_id})\nDescription: {description or 'N/A'}\nParent: {parent or 'None'}",
                namespace="compartments",
                metadata={"compartment_id": compartment_id}
            )
            
            return compartment_id
        except Exception as e:
            logger.error(f"Error creating compartment: {e}")
            return None
    
    async def activate_compartment(self, compartment_id_or_name: str) -> bool:
        """
        Activate a compartment to include in automatic context retrieval.
        
        Args:
            compartment_id_or_name: ID or name of compartment to activate
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if the input is a compartment ID
            if compartment_id_or_name in self.compartments:
                compartment_id = compartment_id_or_name
            else:
                # Look for a compartment with matching name
                for c_id, c_data in self.compartments.items():
                    if c_data.get("name", "").lower() == compartment_id_or_name.lower():
                        compartment_id = c_id
                        break
                else:
                    logger.warning(f"No compartment found matching '{compartment_id_or_name}'")
                    return False
            
            # Update last accessed time
            self.compartments[compartment_id]["last_accessed"] = datetime.now().isoformat()
            self._save_compartments()
            
            # Add to active compartments if not already active
            if compartment_id not in self.active_compartments:
                self.active_compartments.append(compartment_id)
                
            return True
        except Exception as e:
            logger.error(f"Error activating compartment: {e}")
            return False
    
    async def deactivate_compartment(self, compartment_id_or_name: str) -> bool:
        """
        Deactivate a compartment to exclude from automatic context retrieval.
        
        Args:
            compartment_id_or_name: ID or name of compartment to deactivate
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if the input is a compartment ID
            if compartment_id_or_name in self.compartments:
                compartment_id = compartment_id_or_name
            else:
                # Look for a compartment with matching name
                for c_id, c_data in self.compartments.items():
                    if c_data.get("name", "").lower() == compartment_id_or_name.lower():
                        compartment_id = c_id
                        break
                else:
                    logger.warning(f"No compartment found matching '{compartment_id_or_name}'")
                    return False
            
            # Remove from active compartments
            if compartment_id in self.active_compartments:
                self.active_compartments.remove(compartment_id)
                
            return True
        except Exception as e:
            logger.error(f"Error deactivating compartment: {e}")
            return False
    
    async def set_compartment_expiration(self, compartment_id: str, days: int = None) -> bool:
        """
        Set expiration for a compartment in days.
        
        Args:
            compartment_id: ID of the compartment
            days: Number of days until expiration, or None to remove expiration
            
        Returns:
            Boolean indicating success
        """
        if compartment_id not in self.compartments:
            logger.warning(f"No compartment found with ID '{compartment_id}'")
            return False
        
        try:
            if days is None:
                # Remove expiration
                self.compartments[compartment_id]["expiration"] = None
            else:
                # Calculate expiration date
                expiration_date = datetime.now() + timedelta(days=days)
                self.compartments[compartment_id]["expiration"] = expiration_date.isoformat()
            
            # Save to file
            self._save_compartments()
            return True
        except Exception as e:
            logger.error(f"Error setting compartment expiration: {e}")
            return False
    
    async def list_compartments(self, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        List all compartments.
        
        Args:
            include_expired: Whether to include expired compartments
            
        Returns:
            List of compartment information dictionaries
        """
        try:
            result = []
            now = datetime.now()
            
            for compartment_id, data in self.compartments.items():
                # Check expiration if needed
                if not include_expired and data.get("expiration"):
                    try:
                        expiration_date = datetime.fromisoformat(data["expiration"])
                        if expiration_date < now:
                            # Skip expired compartments
                            continue
                    except Exception as e:
                        logger.error(f"Error parsing expiration date: {e}")
                
                # Add active status
                compartment_info = data.copy()
                compartment_info["active"] = compartment_id in self.active_compartments
                
                result.append(compartment_info)
            
            return result
        except Exception as e:
            logger.error(f"Error listing compartments: {e}")
            return []
    
    async def write_session_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write a memory to the session namespace for persistence across sessions.
        
        Args:
            content: The content to store
            metadata: Optional metadata
            
        Returns:
            Boolean indicating success
        """
        try:
            # Add to session namespace
            return await self.add(content=content, namespace="session", metadata=metadata)
        except Exception as e:
            logger.error(f"Error writing session memory: {e}")
            return False
            
    async def keep_memory(self, memory_id: str, days: int = 30) -> bool:
        """
        Keep a memory for a specified number of days by setting expiration.
        
        Args:
            memory_id: The ID of the memory to keep
            days: Number of days to keep the memory
            
        Returns:
            Boolean indicating success
        """
        try:
            # For Hermes storage, we would need to update metadata
            # This is best done with a document database, which is not yet implemented
            # For now, only implement fallback support
            
            # Find the memory in fallback storage
            for namespace, memories in self.fallback_memories.items():
                for memory in memories:
                    if memory.get("id") == memory_id:
                        # Set expiration date in metadata
                        if "metadata" not in memory:
                            memory["metadata"] = {}
                        
                        expiration_date = datetime.now() + timedelta(days=days)
                        memory["metadata"]["expiration"] = expiration_date.isoformat()
                        
                        # Save to file
                        with open(self.fallback_file, "w") as f:
                            json.dump(self.fallback_memories, f, indent=2)
                        
                        return True
            
            logger.warning(f"Memory {memory_id} not found in fallback storage")
            return False
        except Exception as e:
            logger.error(f"Error keeping memory: {e}")
            return False
    
    def _load_compartments(self) -> Dict[str, Dict[str, Any]]:
        """Load compartment definitions from file."""
        if self.compartment_file.exists():
            try:
                with open(self.compartment_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading compartments: {e}")
        
        # Initialize with empty compartments dict if none exists
        return {}
        
    def _save_compartments(self) -> bool:
        """Save compartment definitions to file."""
        try:
            with open(self.compartment_file, "w") as f:
                json.dump(self.compartments, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving compartments: {e}")
            return False
    
    async def close(self) -> None:
        """Close connections and clean up resources."""
        if self.hermes_available and self.hermes_client:
            try:
                await self.hermes_client.close_connections()
                logger.debug("Closed Hermes database connections")
            except Exception as e:
                logger.error(f"Error closing Hermes connections: {e}")


# For backwards compatibility, allow this to be imported as MemoryService
MemoryService = HermesMemoryService