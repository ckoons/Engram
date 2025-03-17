#!/usr/bin/env python3
"""
Structured Memory - File-based memory management with organization and importance ranking

This module implements a balanced approach to memory management with:
1. File-Based Storage with Structure
2. Memory Importance Ranking
3. Retrieval Mechanisms
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.structured_memory")

class StructuredMemory:
    """
    Structured memory service with file-based organization and importance ranking.
    
    Key features:
    - Organized, searchable memory files by category/project
    - Standardized formats (JSON) for easier parsing
    - Metadata with timestamps, context, and importance
    - Memory importance ranking (1-5 scale)
    - Context-aware memory loading
    """
    
    def __init__(self, client_id: str = "default", data_dir: Optional[str] = None):
        """
        Initialize the structured memory service.
        
        Args:
            client_id: Unique identifier for the client (default: "default")
            data_dir: Directory to store memory data (default: ~/.engram/structured)
        """
        self.client_id = client_id
        
        # Set up base data directory
        if data_dir:
            self.base_dir = Path(data_dir) / "structured"
        else:
            self.base_dir = Path(os.path.expanduser("~/.engram/structured"))
        
        # Create structured directory layout
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Key directories for different memory categories
        self.memory_dirs = {
            "personal": self.base_dir / "personal",
            "projects": self.base_dir / "projects",
            "facts": self.base_dir / "facts",
            "preferences": self.base_dir / "preferences",
            "session": self.base_dir / "session",
            "private": self.base_dir / "private",
        }
        
        # Create all memory category directories
        for dir_path in self.memory_dirs.values():
            dir_path.mkdir(exist_ok=True)
            
        # Create clients directory within each category
        for dir_path in self.memory_dirs.values():
            client_dir = dir_path / client_id
            client_dir.mkdir(exist_ok=True)
            
        # Track memory categories and their importance factors (1-5)
        self.category_importance = {
            "personal": {
                "default_importance": 5,
                "description": "Personal information about the user"
            },
            "projects": {
                "default_importance": 4,
                "description": "Project-specific information and context"
            },
            "facts": {
                "default_importance": 3,
                "description": "General factual information"
            },
            "preferences": {
                "default_importance": 4,
                "description": "User preferences and settings"
            },
            "session": {
                "default_importance": 3,
                "description": "Session-specific context and information"
            },
            "private": {
                "default_importance": 5,
                "description": "Private thoughts and reflections"
            }
        }
        
        # Importance level descriptions
        self.importance_levels = {
            1: "Low importance, general context",
            2: "Somewhat important, specific details",
            3: "Moderately important, useful context",
            4: "Very important, should remember",
            5: "Critical information, must remember"
        }
        
        # Memory retrieval cache to optimize performance
        self.memory_cache = {}
        
        # Initialize metadata index
        self.metadata_index_file = self.base_dir / f"{client_id}_metadata_index.json"
        self.metadata_index = self._load_metadata_index()
        
    def _load_metadata_index(self) -> Dict[str, Any]:
        """Load the metadata index from file or initialize if it doesn't exist."""
        if self.metadata_index_file.exists():
            try:
                with open(self.metadata_index_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata index: {e}")
                return self._initialize_metadata_index()
        else:
            return self._initialize_metadata_index()
            
    def _initialize_metadata_index(self) -> Dict[str, Any]:
        """Initialize a new metadata index."""
        index = {
            "client_id": self.client_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "categories": {},
            "memory_count": 0,
            "importance_counters": {str(i): 0 for i in range(1, 6)},
            "tags": {},
        }
        
        # Initialize category sub-indices
        for category in self.category_importance.keys():
            index["categories"][category] = {
                "memory_count": 0,
                "last_updated": datetime.now().isoformat(),
                "memories": {}  # Will contain memory_id -> metadata mappings
            }
            
        # Save the initial index
        self._save_metadata_index(index)
        return index
        
    def _save_metadata_index(self, index: Optional[Dict[str, Any]] = None) -> bool:
        """Save the metadata index to file."""
        if index is None:
            index = self.metadata_index
            
        try:
            # Update the last_updated timestamp
            index["last_updated"] = datetime.now().isoformat()
            
            with open(self.metadata_index_file, "w") as f:
                json.dump(index, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving metadata index: {e}")
            return False
            
    def _get_memory_path(self, memory_id: str, category: str) -> Path:
        """Get the file path for a specific memory."""
        return self.memory_dirs[category] / self.client_id / f"{memory_id}.json"
        
    async def add_memory(self, 
                        content: str, 
                        category: str = "session",
                        importance: int = None, 
                        metadata: Optional[Dict[str, Any]] = None,
                        tags: Optional[List[str]] = None) -> Optional[str]:
        """
        Add a new memory with structured metadata and importance ranking.
        
        Args:
            content: The memory content to store
            category: The category to store in (personal, projects, facts, etc.)
            importance: Importance ranking 1-5 (5 being most important)
            metadata: Additional metadata for the memory
            tags: Tags for easier searching and categorization
            
        Returns:
            Memory ID if successful, None otherwise
        """
        # Validate category
        if category not in self.category_importance:
            logger.warning(f"Invalid category: {category}, using 'session'")
            category = "session"
            
        # Set default importance from category if not provided
        if importance is None:
            importance = self.category_importance[category]["default_importance"]
        else:
            # Ensure importance is in valid range
            importance = max(1, min(5, importance))
            
        # Initialize metadata if not provided
        if metadata is None:
            metadata = {}
            
        # Initialize tags if not provided
        if tags is None:
            tags = []
            
        try:
            # Generate memory ID with timestamp for uniqueness
            timestamp = int(time.time())
            memory_id = f"{category}-{timestamp}-{hash(content) % 10000}"
            
            # Prepare memory data
            memory_data = {
                "id": memory_id,
                "content": content,
                "category": category,
                "importance": importance,
                "metadata": {
                    **metadata,
                    "timestamp": datetime.now().isoformat(),
                    "client_id": self.client_id,
                    "importance_reason": metadata.get("importance_reason", "Default category importance")
                },
                "tags": tags
            }
            
            # Save memory to file
            memory_path = self._get_memory_path(memory_id, category)
            
            with open(memory_path, "w") as f:
                json.dump(memory_data, f, indent=2)
                
            # Update metadata index
            self.metadata_index["memory_count"] += 1
            self.metadata_index["importance_counters"][str(importance)] += 1
            self.metadata_index["categories"][category]["memory_count"] += 1
            self.metadata_index["categories"][category]["last_updated"] = datetime.now().isoformat()
            self.metadata_index["categories"][category]["memories"][memory_id] = {
                "importance": importance,
                "timestamp": memory_data["metadata"]["timestamp"],
                "tags": tags
            }
            
            # Update tag index
            for tag in tags:
                if tag not in self.metadata_index["tags"]:
                    self.metadata_index["tags"][tag] = []
                self.metadata_index["tags"][tag].append(memory_id)
                
            # Save updated index
            self._save_metadata_index()
            
            logger.info(f"Added memory {memory_id} to {category} with importance {importance}")
            return memory_id
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return None
            
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            Memory data dictionary if found, None otherwise
        """
        try:
            # Check cache first
            if memory_id in self.memory_cache:
                return self.memory_cache[memory_id]
                
            # Parse category from memory ID
            if "-" not in memory_id:
                logger.warning(f"Invalid memory ID format: {memory_id}")
                return None
                
            category = memory_id.split("-")[0]
            
            if category not in self.category_importance:
                logger.warning(f"Invalid category in memory ID: {memory_id}")
                return None
                
            # Get memory file path
            memory_path = self._get_memory_path(memory_id, category)
            
            if not memory_path.exists():
                logger.warning(f"Memory file not found: {memory_path}")
                return None
                
            # Load memory from file
            with open(memory_path, "r") as f:
                memory_data = json.load(f)
                
            # Cache for future retrievals
            self.memory_cache[memory_id] = memory_data
            
            return memory_data
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None
            
    async def search_memories(self, 
                            query: str = None, 
                            categories: List[str] = None,
                            tags: List[str] = None,
                            min_importance: int = 1,
                            limit: int = 10,
                            sort_by: str = "importance") -> List[Dict[str, Any]]:
        """
        Search for memories based on multiple criteria.
        
        Args:
            query: Text to search for in memory content (optional)
            categories: List of categories to search in (defaults to all)
            tags: List of tags to filter by (optional)
            min_importance: Minimum importance level (1-5)
            limit: Maximum number of results to return
            sort_by: How to sort results ("importance", "recency", or "relevance")
            
        Returns:
            List of matching memory data dictionaries
        """
        try:
            # Default to all categories if not specified
            if categories is None:
                categories = list(self.category_importance.keys())
                
            # Validate categories
            valid_categories = [c for c in categories if c in self.category_importance]
            if not valid_categories:
                logger.warning(f"No valid categories specified")
                return []
                
            # Start with all memory IDs from specified categories
            candidate_ids = []
            
            for category in valid_categories:
                category_memories = self.metadata_index["categories"][category]["memories"]
                
                # Filter by minimum importance
                for memory_id, metadata in category_memories.items():
                    if metadata["importance"] >= min_importance:
                        candidate_ids.append(memory_id)
                        
            # Filter by tags if specified
            if tags:
                tag_filtered_ids = []
                for tag in tags:
                    tag_ids = self.metadata_index["tags"].get(tag, [])
                    tag_filtered_ids.extend(tag_ids)
                    
                # Only keep IDs that match both category/importance and tags
                candidate_ids = [mid for mid in candidate_ids if mid in tag_filtered_ids]
                
            # Load all candidate memories
            memories = []
            for memory_id in candidate_ids:
                memory = await self.get_memory(memory_id)
                if memory:
                    memories.append(memory)
                    
            # Search content if query is provided
            if query:
                filtered_memories = []
                for memory in memories:
                    if query.lower() in memory["content"].lower():
                        filtered_memories.append(memory)
                memories = filtered_memories
                
            # Sort memories
            if sort_by == "importance":
                # Sort by importance (higher first), then by timestamp (newest first)
                memories.sort(key=lambda x: (-(x.get("importance", 0)), x.get("metadata", {}).get("timestamp", "")))
            elif sort_by == "recency":
                # Sort by timestamp (newest first)
                memories.sort(key=lambda x: x.get("metadata", {}).get("timestamp", ""), reverse=True)
            elif sort_by == "relevance" and query:
                # Simple relevance scoring (can be enhanced with better algorithms)
                for memory in memories:
                    query_count = memory["content"].lower().count(query.lower())
                    memory["relevance_score"] = query_count * memory.get("importance", 3)
                memories.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            else:
                # Default to importance
                memories.sort(key=lambda x: (-(x.get("importance", 0)), x.get("metadata", {}).get("timestamp", "")))
                
            # Limit results
            memories = memories[:limit]
            
            return memories
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
            
    async def get_memory_digest(self, 
                              categories: List[str] = None,
                              max_memories: int = 10,
                              include_private: bool = False) -> str:
        """
        Generate a formatted digest of important memories for session start.
        
        Args:
            categories: List of categories to include (defaults to all except private)
            max_memories: Maximum memories to include in digest
            include_private: Whether to include private memories
            
        Returns:
            Formatted text digest of important memories
        """
        try:
            # Default to all categories except private
            if categories is None:
                categories = [c for c in self.category_importance.keys() if c != "private" or include_private]
                
            digest_parts = ["# Memory Digest\n\n"]
            
            # Get most important memories from each category
            for category in categories:
                category_memories = await self.search_memories(
                    categories=[category],
                    min_importance=3,  # Only include moderately+ important memories
                    limit=max_memories // len(categories) + 1,  # Distribute limit across categories
                    sort_by="importance"
                )
                
                if category_memories:
                    digest_parts.append(f"## {category.capitalize()}\n")
                    
                    for memory in category_memories:
                        importance_str = "★" * memory["importance"]
                        date_str = datetime.fromisoformat(memory["metadata"]["timestamp"]).strftime("%Y-%m-%d")
                        
                        digest_parts.append(f"- {importance_str} {memory['content']} ({date_str})\n")
                    
                    digest_parts.append("\n")
                    
            return "".join(digest_parts)
        except Exception as e:
            logger.error(f"Error generating memory digest: {e}")
            return "# Memory Digest\n\nUnable to generate memory digest due to an error."
            
    async def auto_categorize_memory(self, content: str) -> Tuple[str, int, List[str]]:
        """
        Automatically categorize memory based on content analysis.
        
        Args:
            content: The memory content to analyze
            
        Returns:
            Tuple of (category, importance, tags)
        """
        # Initialize with defaults
        category = "session"
        importance = 3
        tags = []
        
        try:
            # Basic keyword matching for demonstration
            # These rules would be enhanced with more sophisticated NLP in production
            content_lower = content.lower()
            
            # Check for personal information patterns - highest priority
            personal_patterns = ["name is", "my name", "i am", "i'm", "i live", "address", "phone", "email"]
            has_personal = any(term in content_lower for term in personal_patterns)
            
            # Check for preferences
            preference_patterns = ["prefer", "like", "dislike", "favorite", "rather", "instead"]
            has_preferences = any(term in content_lower for term in preference_patterns)
            
            # Check for project information
            project_patterns = ["project", "working on", "task", "implement", "design", "feature"]
            has_project = any(term in content_lower for term in project_patterns)
            
            # Check for factual information
            fact_patterns = ["fact", "actually", "remember that", "keep in mind"]
            has_facts = any(term in content_lower for term in fact_patterns)
            
            # Prioritize categories (personal > preferences > projects > facts > session)
            if has_personal:
                category = "personal"
                importance = 5
                tags.append("personal-info")
            elif has_preferences:
                category = "preferences"
                importance = 4
                tags.append("preference")
            elif has_project:
                category = "projects"
                importance = 4
                tags.append("project")
            elif has_facts:
                category = "facts"
                importance = 3
                tags.append("fact")
                
            # Add coding related tags
            if any(term in content_lower for term in ["code", "python", "javascript", "programming", "function", "class"]):
                tags.append("coding")
                
            # Add communication tags
            if any(term in content_lower for term in ["call", "meeting", "discuss", "talk", "conversation"]):
                tags.append("communication")
                
            # Adjust importance based on emphasis cues
            if any(term in content_lower for term in ["important", "critical", "essential", "remember", "don't forget", "key"]):
                importance = min(importance + 1, 5)
                
            if any(term in content_lower for term in ["very important", "most important", "crucial", "vital"]):
                importance = 5
                
            return category, importance, tags
        except Exception as e:
            logger.error(f"Error auto-categorizing memory: {e}")
            return "session", 3, []

    async def add_auto_categorized_memory(self, content: str, 
                                         manual_category: str = None,
                                         manual_importance: int = None,
                                         manual_tags: List[str] = None,
                                         metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Add a memory with automatic categorization, allowing manual overrides.
        
        Args:
            content: The memory content to store
            manual_category: Override the automatic category (optional)
            manual_importance: Override the automatic importance (optional)
            manual_tags: Additional tags to add (optional)
            metadata: Additional metadata for the memory
            
        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            # Auto-categorize unless overridden
            if manual_category is None or manual_importance is None:
                auto_category, auto_importance, auto_tags = await self.auto_categorize_memory(content)
                
                # Use auto values as defaults
                category = manual_category or auto_category
                importance = manual_importance or auto_importance
                
                # Combine auto and manual tags without duplicates
                tags = list(set(auto_tags + (manual_tags or [])))
                
                # Add categorization info to metadata
                if metadata is None:
                    metadata = {}
                
                metadata["auto_categorized"] = (manual_category is None)
                metadata["auto_importance"] = auto_importance
                metadata["importance_reason"] = "Auto-categorized based on content analysis"
                
                if manual_importance is not None:
                    metadata["importance_reason"] = "Manually set importance level"
            else:
                # Use manual values
                category = manual_category
                importance = manual_importance
                tags = manual_tags or []
                
                if metadata is None:
                    metadata = {}
                
                metadata["auto_categorized"] = False
                metadata["importance_reason"] = "Manually categorized"
                
            # Add the memory with the determined category and importance
            return await self.add_memory(
                content=content,
                category=category,
                importance=importance,
                metadata=metadata,
                tags=tags
            )
        except Exception as e:
            logger.error(f"Error adding auto-categorized memory: {e}")
            return None
            
    async def set_memory_importance(self, memory_id: str, importance: int) -> bool:
        """
        Update the importance of an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            importance: New importance level (1-5)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Ensure importance is in valid range
            importance = max(1, min(5, importance))
            
            # Get the memory
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory not found: {memory_id}")
                return False
                
            # Get original importance for index updating
            original_importance = memory["importance"]
            
            # Update the memory
            memory["importance"] = importance
            memory["metadata"]["importance_updated"] = datetime.now().isoformat()
            memory["metadata"]["importance_reason"] = "Manually updated importance"
            
            # Save updated memory to file
            category = memory["category"]
            memory_path = self._get_memory_path(memory_id, category)
            
            with open(memory_path, "w") as f:
                json.dump(memory, f, indent=2)
                
            # Update cache
            self.memory_cache[memory_id] = memory
            
            # Update metadata index
            self.metadata_index["importance_counters"][str(original_importance)] -= 1
            self.metadata_index["importance_counters"][str(importance)] += 1
            self.metadata_index["categories"][category]["memories"][memory_id]["importance"] = importance
            self._save_metadata_index()
            
            return True
        except Exception as e:
            logger.error(f"Error updating memory importance: {e}")
            return False
            
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from storage.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            # Get the memory to find its category
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(f"Memory not found: {memory_id}")
                return False
                
            category = memory["category"]
            importance = memory["importance"]
            tags = memory.get("tags", [])
            
            # Delete the memory file
            memory_path = self._get_memory_path(memory_id, category)
            if memory_path.exists():
                os.remove(memory_path)
                
            # Update the metadata index
            if memory_id in self.metadata_index["categories"][category]["memories"]:
                del self.metadata_index["categories"][category]["memories"][memory_id]
                self.metadata_index["categories"][category]["memory_count"] -= 1
                self.metadata_index["memory_count"] -= 1
                self.metadata_index["importance_counters"][str(importance)] -= 1
                
                # Remove from tag indices
                for tag in tags:
                    if tag in self.metadata_index["tags"] and memory_id in self.metadata_index["tags"][tag]:
                        self.metadata_index["tags"][tag].remove(memory_id)
                        
                        # Clean up empty tag entries
                        if not self.metadata_index["tags"][tag]:
                            del self.metadata_index["tags"][tag]
                
                self._save_metadata_index()
                
            # Remove from cache
            if memory_id in self.memory_cache:
                del self.memory_cache[memory_id]
                
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
            
    async def get_memory_by_content(self, content: str, category: str = None) -> Optional[Dict[str, Any]]:
        """
        Find a memory by its content.
        
        Args:
            content: The exact content to search for
            category: Optional category to limit the search
            
        Returns:
            Memory data if found, None otherwise
        """
        try:
            categories_to_search = [category] if category else self.category_importance.keys()
            
            for cat in categories_to_search:
                if cat not in self.category_importance:
                    continue
                    
                # Search through the metadata index for this category
                for memory_id in self.metadata_index["categories"][cat]["memories"]:
                    memory = await self.get_memory(memory_id)
                    
                    if memory and memory["content"] == content:
                        return memory
                        
            return None
        except Exception as e:
            logger.error(f"Error finding memory by content: {e}")
            return None
            
    async def get_context_memories(self, text: str, max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories relevant to the given context text.
        
        Args:
            text: The context text to find relevant memories for
            max_memories: Maximum number of memories to return
            
        Returns:
            List of relevant memory dictionaries
        """
        try:
            # This is a very basic keyword-based implementation
            # In a production system, this would use embedding similarity
            
            # Extract potential keywords (simple implementation)
            words = text.lower().split()
            keywords = [word for word in words if len(word) > 3]
            
            # Remove common words
            common_words = {"this", "that", "what", "with", "from", "have", "there", "they", "their", "should", "would", "could", "about"}
            keywords = [word for word in keywords if word not in common_words]
            
            # Search memories for each keyword
            all_results = []
            
            for keyword in keywords[:5]:  # Limit to 5 keywords to avoid too many searches
                results = await self.search_memories(
                    query=keyword,
                    min_importance=3,  # Focus on at least moderately important memories
                    limit=max_memories,
                    sort_by="importance"
                )
                all_results.extend(results)
                
            # Deduplicate results
            unique_results = {}
            for memory in all_results:
                if memory["id"] not in unique_results:
                    unique_results[memory["id"]] = memory
                    
            # Sort by importance and limit results
            sorted_results = sorted(
                unique_results.values(),
                key=lambda x: (-x["importance"], x["metadata"]["timestamp"]),
                reverse=True
            )
            
            return sorted_results[:max_memories]
        except Exception as e:
            logger.error(f"Error getting context memories: {e}")
            return []
            
    async def migrate_from_memory_service(self, memory_service, limit: int = 1000) -> int:
        """
        Migrate memories from the old MemoryService to StructuredMemory.
        
        Args:
            memory_service: Instance of the old MemoryService
            limit: Maximum number of memories to migrate
            
        Returns:
            Number of memories migrated
        """
        migrated_count = 0
        
        try:
            # Map old namespaces to new categories
            namespace_to_category = {
                "conversations": "personal",
                "thinking": "private",
                "longterm": "personal",
                "projects": "projects",
                "compartments": "projects",
                "session": "session"
            }
            
            # Get available namespaces
            namespaces = await memory_service.get_namespaces()
            
            for namespace in namespaces:
                # Map to new category
                if namespace.startswith("compartment-"):
                    category = "projects"
                else:
                    category = namespace_to_category.get(namespace, "session")
                
                # Set default importance based on namespace
                if namespace == "longterm":
                    default_importance = 5
                elif namespace == "thinking":
                    default_importance = 4
                elif namespace.startswith("compartment-"):
                    default_importance = 4
                else:
                    default_importance = 3
                
                # Search all memories in this namespace
                results = await memory_service.search(
                    query="",
                    namespace=namespace,
                    limit=limit
                )
                
                # Migrate each memory
                for memory in results.get("results", []):
                    content = memory.get("content", "")
                    metadata = memory.get("metadata", {})
                    
                    # Generate tags based on namespace
                    tags = [namespace]
                    
                    # Add compartment name as a tag if available
                    if namespace.startswith("compartment-"):
                        compartment_id = namespace[len("compartment-"):]
                        tags.append(f"compartment:{compartment_id}")
                    
                    # Add the memory to structured storage
                    memory_id = await self.add_memory(
                        content=content,
                        category=category,
                        importance=default_importance,
                        metadata={
                            "migrated_from": namespace,
                            "original_timestamp": metadata.get("timestamp"),
                            **metadata
                        },
                        tags=tags
                    )
                    
                    if memory_id:
                        migrated_count += 1
                    
                    # Break if we've reached the limit
                    if migrated_count >= limit:
                        break
                
                # Break if we've reached the limit
                if migrated_count >= limit:
                    break
            
            logger.info(f"Migrated {migrated_count} memories from MemoryService to StructuredMemory")
            return migrated_count
        except Exception as e:
            logger.error(f"Error migrating memories: {e}")
            return migrated_count