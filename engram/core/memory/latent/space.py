"""
Latent Memory Space Implementation

Provides the core LatentMemorySpace class for latent space reasoning.
"""

import logging
import uuid
import time
from datetime import datetime

# Import queries
from .queries import get_thought, get_reasoning_trace, list_thoughts, abandon_thought
from typing import Dict, List, Any, Optional, Union, Tuple
import json

from engram.core.memory.base import MemoryService
from .states import ThoughtState

logger = logging.getLogger("engram.memory.latent.space")

class LatentMemorySpace:
    """
    Specialized memory structure for latent space reasoning.
    
    Enables components to store, iteratively refine, and finalize thoughts
    in a dedicated latent reasoning space.
    """
    
    def __init__(self, 
                memory_service: MemoryService,
                space_id: Optional[str] = None,
                owner_component: Optional[str] = None,
                shared: bool = False,
                max_history_length: int = 10):
        """
        Initialize a latent memory space.
        
        Args:
            memory_service: The underlying memory service for storage
            space_id: Unique identifier for this latent space (generated if None)
            owner_component: Component that owns this space (if not shared)
            shared: Whether this is a shared latent space
            max_history_length: Maximum number of refinement iterations to store
        """
        self.memory_service = memory_service
        self.space_id = space_id or f"latent-{uuid.uuid4()}"
        self.owner_component = owner_component
        self.shared = shared
        self.max_history_length = max_history_length
        
        # Namespace for this latent space
        self.namespace = f"latent-{self.space_id}"
        
        # Thought registry - maps thought IDs to metadata
        self.thoughts: Dict[str, Dict[str, Any]] = {}
        
        # Initialize namespace in memory service
        self._initialize_space()
        
        logger.info(f"Initialized latent memory space {self.space_id} (shared: {self.shared})")
    
    def _initialize_space(self):
        """Initialize the latent space in memory service."""
        # Create namespace for this latent space
        if hasattr(self.memory_service.storage, "initialize_namespace"):
            self.memory_service.storage.initialize_namespace(self.namespace)
            
        # Load existing thoughts if any
        self._load_thoughts()
    
    def _load_thoughts(self):
        """Load existing thoughts from storage."""
        try:
            # Check if index file exists
            metadata_file = self.memory_service.data_dir / f"{self.memory_service.client_id}" / f"{self.namespace}-thoughts.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.thoughts = json.load(f)
                logger.info(f"Loaded {len(self.thoughts)} thoughts from {self.namespace}")
            else:
                # Initialize empty thought registry
                self.thoughts = {}
        except Exception as e:
            logger.error(f"Error loading thoughts from {self.namespace}: {e}")
            self.thoughts = {}
    
    def _save_thoughts(self):
        """Save thought registry to storage."""
        try:
            # Ensure directory exists
            metadata_dir = self.memory_service.data_dir / f"{self.memory_service.client_id}"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            
            # Save thought registry
            metadata_file = metadata_dir / f"{self.namespace}-thoughts.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.thoughts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving thoughts to {self.namespace}: {e}")
    
    async def initialize_thought(self, 
                               thought_seed: str, 
                               component_id: Optional[str] = None, 
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create initial thought entry in latent space.
        
        Args:
            thought_seed: Initial thought content
            component_id: ID of component initializing the thought
            metadata: Optional metadata for the thought
            
        Returns:
            Unique thought ID
        """
        # Generate thought ID
        thought_id = f"thought-{uuid.uuid4()}"
        
        # Create thought metadata
        thought_metadata = {
            "thought_id": thought_id,
            "component_id": component_id or self.owner_component or "unknown",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "state": ThoughtState.INITIAL,
            "iteration": 0,
            "iterations": [0],  # List of available iterations
            **(metadata or {})
        }
        
        # Store initial thought
        content = {
            "thought": thought_seed,
            "iteration": 0,
            "state": ThoughtState.INITIAL
        }
        
        success = await self.memory_service.add(
            content=json.dumps(content),
            namespace=self.namespace,
            metadata={
                "thought_id": thought_id,
                "iteration": 0,
                **thought_metadata
            }
        )
        
        if success:
            # Add to thought registry
            self.thoughts[thought_id] = thought_metadata
            self._save_thoughts()
            
            logger.info(f"Initialized thought {thought_id} in space {self.space_id}")
            return thought_id
        else:
            logger.error(f"Failed to initialize thought in space {self.space_id}")
            return None
    
    async def refine_thought(self, 
                           thought_id: str, 
                           refinement: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, int]:
        """
        Process thought through additional reasoning cycle.
        
        Args:
            thought_id: ID of the thought to refine
            refinement: Refinement content
            metadata: Optional metadata for this refinement
            
        Returns:
            Tuple of (success, iteration_number)
        """
        # Check if thought exists
        if thought_id not in self.thoughts:
            logger.error(f"Thought {thought_id} not found in space {self.space_id}")
            return False, -1
        
        # Get thought metadata
        thought_metadata = self.thoughts[thought_id]
        
        # Check if thought can be refined
        if thought_metadata["state"] in [ThoughtState.FINALIZED, ThoughtState.ABANDONED]:
            logger.warning(f"Cannot refine thought {thought_id}: already in state {thought_metadata['state']}")
            return False, -1
        
        # Calculate next iteration
        next_iteration = thought_metadata["iteration"] + 1
        
        # Store refinement
        content = {
            "thought": refinement,
            "iteration": next_iteration,
            "state": ThoughtState.REFINING,
            "previous_iteration": thought_metadata["iteration"]
        }
        
        refinement_metadata = {
            "thought_id": thought_id,
            "iteration": next_iteration,
            "refined_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        success = await self.memory_service.add(
            content=json.dumps(content),
            namespace=self.namespace,
            metadata=refinement_metadata
        )
        
        if success:
            # Update thought metadata
            thought_metadata["iteration"] = next_iteration
            thought_metadata["iterations"].append(next_iteration)
            thought_metadata["state"] = ThoughtState.REFINING
            thought_metadata["updated_at"] = datetime.now().isoformat()
            
            # Prune iterations if needed
            if len(thought_metadata["iterations"]) > self.max_history_length:
                # Keep first and last few iterations
                keep_first = max(1, self.max_history_length // 3)
                keep_last = self.max_history_length - keep_first
                
                iterations = thought_metadata["iterations"]
                thought_metadata["iterations"] = (
                    iterations[:keep_first] + 
                    iterations[-keep_last:]
                )
            
            # Save updated thought registry
            self._save_thoughts()
            
            logger.info(f"Refined thought {thought_id} to iteration {next_iteration}")
            return True, next_iteration
        else:
            logger.error(f"Failed to refine thought {thought_id}")
            return False, -1
    
    async def finalize_thought(self, 
                            thought_id: str, 
                            final_content: Optional[str] = None,
                            persist: bool = True,
                            persist_namespace: Optional[str] = None) -> bool:
        """
        Complete reasoning process and optionally persist insights.
        
        Args:
            thought_id: ID of the thought to finalize
            final_content: Optional final content (if None, uses last refinement)
            persist: Whether to persist the final thought to another namespace
            persist_namespace: Namespace to persist the thought to (defaults to longterm)
            
        Returns:
            Boolean indicating success
        """
        # Check if thought exists
        if thought_id not in self.thoughts:
            logger.error(f"Thought {thought_id} not found in space {self.space_id}")
            return False
        
        # Get thought metadata
        thought_metadata = self.thoughts[thought_id]
        
        # Get final content
        if final_content is None:
            # Retrieve the latest refinement
            search_results = await self.memory_service.search(
                query=thought_id,
                namespace=self.namespace,
                limit=1
            )
            
            if not search_results["results"]:
                logger.error(f"Failed to retrieve latest refinement for thought {thought_id}")
                return False
            
            # Parse content
            try:
                content_obj = json.loads(search_results["results"][0]["content"])
                final_content = content_obj["thought"]
            except Exception as e:
                logger.error(f"Failed to parse thought content: {e}")
                return False
        
        # Store finalized thought
        content = {
            "thought": final_content,
            "iteration": thought_metadata["iteration"] + 1 if final_content else thought_metadata["iteration"],
            "state": ThoughtState.FINALIZED,
            "previous_iteration": thought_metadata["iteration"]
        }
        
        finalized_metadata = {
            "thought_id": thought_id,
            "iteration": content["iteration"],
            "finalized_at": datetime.now().isoformat(),
            "from_iterations": thought_metadata["iterations"]
        }
        
        success = await self.memory_service.add(
            content=json.dumps(content),
            namespace=self.namespace,
            metadata=finalized_metadata
        )
        
        if success:
            # Update thought metadata
            thought_metadata["state"] = ThoughtState.FINALIZED
            thought_metadata["updated_at"] = datetime.now().isoformat()
            thought_metadata["finalized_at"] = datetime.now().isoformat()
            
            if final_content:
                thought_metadata["iteration"] += 1
                thought_metadata["iterations"].append(thought_metadata["iteration"])
            
            # Save updated thought registry
            self._save_thoughts()
            
            # Persist to another namespace if requested
            if persist:
                target_namespace = persist_namespace or "longterm"
                
                # Format for persistence
                persistence_content = (
                    f"Finalized thought from latent space {self.space_id}:\n\n"
                    f"{final_content}\n\n"
                    f"[Final version after {len(thought_metadata['iterations'])} refinement iterations]"
                )
                
                await self.memory_service.add(
                    content=persistence_content,
                    namespace=target_namespace,
                    metadata={
                        "thought_id": thought_id,
                        "latent_space_id": self.space_id,
                        "source": "latent_space",
                        "iterations": len(thought_metadata["iterations"])
                    }
                )
            
            logger.info(f"Finalized thought {thought_id} in space {self.space_id}")
            return True
        else:
            logger.error(f"Failed to finalize thought {thought_id}")
            return False