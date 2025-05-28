#!/usr/bin/env python3
"""
Provenance storage layer for Engram.

Handles storage of provenance data without polluting memory namespaces.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models.provenance import MemoryProvenance, ProvenanceEntry, ProvenanceAction
from ..models.memory_enhanced import EnhancedMemory


class ProvenanceStorage:
    """
    Manages provenance storage separate from memory content.
    
    Uses dedicated namespace to avoid collision with user memories.
    """
    
    PROVENANCE_NAMESPACE = "_provenance"
    BRANCH_NAMESPACE = "_branches"
    PROVENANCE_PREFIX = "prov:"
    BRANCH_PREFIX = "branch:"
    
    def __init__(self, memory_service):
        """Initialize with reference to main memory service."""
        self.memory_service = memory_service
        self._cache = {}  # Simple in-memory cache
        self._write_queue = asyncio.Queue()
        self._writer_task = None
        
    async def start(self):
        """Start background writer for async provenance updates."""
        self._writer_task = asyncio.create_task(self._background_writer())
        
    async def stop(self):
        """Stop background writer gracefully."""
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
    
    async def _background_writer(self):
        """Process provenance writes asynchronously for performance."""
        while True:
            try:
                # Get write operation from queue
                operation = await self._write_queue.get()
                
                if operation['type'] == 'provenance':
                    await self._write_provenance(
                        operation['memory_id'],
                        operation['data']
                    )
                elif operation['type'] == 'branch':
                    await self._write_branch(
                        operation['memory_id'],
                        operation['branch_name'],
                        operation['data']
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log but don't crash - provenance is non-critical
                print(f"Provenance write error: {e}")
    
    async def track_creation(self, memory_id: str, creator: str, 
                           content: str, metadata: Dict[str, Any]) -> None:
        """Track memory creation without blocking main operation."""
        provenance_data = {
            "memory_id": memory_id,
            "chain": [{
                "actor": creator,
                "action": ProvenanceAction.CREATED.value,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            }],
            "current_branch": "main",
            "version": 1
        }
        
        # Queue for async write
        await self._write_queue.put({
            'type': 'provenance',
            'memory_id': memory_id,
            'data': provenance_data
        })
        
        # Cache for immediate reads
        self._cache[memory_id] = provenance_data
    
    async def track_edit(self, memory_id: str, actor: str, 
                        action: ProvenanceAction, note: Optional[str] = None,
                        **kwargs) -> None:
        """Track memory edit asynchronously."""
        # Get existing provenance
        prov_data = await self.get_provenance(memory_id)
        if not prov_data:
            # Initialize if missing
            prov_data = {
                "memory_id": memory_id,
                "chain": [],
                "current_branch": "main",
                "version": 1
            }
        
        # Add new entry
        entry = {
            "actor": actor,
            "action": action.value,
            "timestamp": datetime.now().isoformat(),
            "note": note
        }
        entry.update(kwargs)
        
        prov_data["chain"].append(entry)
        prov_data["version"] += 1
        
        # Queue for async write
        await self._write_queue.put({
            'type': 'provenance',
            'memory_id': memory_id,
            'data': prov_data
        })
        
        # Update cache
        self._cache[memory_id] = prov_data
    
    async def get_provenance(self, memory_id: str, 
                            use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get provenance data for a memory."""
        # Check cache first
        if use_cache and memory_id in self._cache:
            return self._cache[memory_id]
        
        # Load from storage
        key = f"{self.PROVENANCE_PREFIX}{memory_id}"
        try:
            stored = await self.memory_service.retrieve(
                key, 
                self.PROVENANCE_NAMESPACE
            )
            if stored and 'value' in stored:
                prov_data = json.loads(stored['value'])
                self._cache[memory_id] = prov_data
                return prov_data
        except Exception:
            # Provenance is optional - don't fail
            pass
            
        return None
    
    async def create_branch(self, memory_id: str, branch_name: str,
                          from_branch: str, creator: str,
                          content: str) -> Dict[str, Any]:
        """Create a new branch for a memory."""
        branch_data = {
            "branch_name": branch_name,
            "parent_branch": from_branch,
            "created_by": creator,
            "created_at": datetime.now().isoformat(),
            "content": content,
            "memory_id": memory_id
        }
        
        # Store branch data
        await self._write_queue.put({
            'type': 'branch',
            'memory_id': memory_id,
            'branch_name': branch_name,
            'data': branch_data
        })
        
        # Track in provenance
        await self.track_edit(
            memory_id, creator, ProvenanceAction.FORKED,
            note=f"Created branch '{branch_name}' from '{from_branch}'"
        )
        
        return branch_data
    
    async def get_branches(self, memory_id: str) -> List[str]:
        """Get all branches for a memory."""
        # This would query all branches - simplified for now
        prov_data = await self.get_provenance(memory_id)
        if prov_data:
            # Extract branch names from fork actions
            branches = ["main"]
            for entry in prov_data.get("chain", []):
                if entry.get("action") == ProvenanceAction.FORKED.value:
                    if "Created branch" in entry.get("note", ""):
                        # Parse branch name from note
                        import re
                        match = re.search(r"'([^']+)'", entry["note"])
                        if match:
                            branches.append(match.group(1))
            return branches
        return ["main"]
    
    async def _write_provenance(self, memory_id: str, data: Dict[str, Any]):
        """Write provenance data to storage."""
        key = f"{self.PROVENANCE_PREFIX}{memory_id}"
        await self.memory_service.store(
            key,
            json.dumps(data),
            self.PROVENANCE_NAMESPACE
        )
    
    async def _write_branch(self, memory_id: str, branch_name: str, 
                          data: Dict[str, Any]):
        """Write branch data to storage."""
        key = f"{self.BRANCH_PREFIX}{memory_id}:{branch_name}"
        await self.memory_service.store(
            key,
            json.dumps(data),
            self.BRANCH_NAMESPACE
        )


class ProvenanceMemoryService:
    """
    Wrapper around MemoryService that adds provenance tracking.
    
    Maintains backward compatibility while adding opt-in provenance.
    """
    
    def __init__(self, base_service, track_by_default: bool = False):
        """
        Initialize with base memory service.
        
        Args:
            base_service: Original MemoryService instance
            track_by_default: Whether to track provenance by default
        """
        self.base_service = base_service
        self.provenance_storage = ProvenanceStorage(base_service)
        self.track_by_default = track_by_default
        
        # Namespaces that always track provenance
        self.tracked_namespaces = {"shared", "longterm", "projects"}
        
    async def start(self):
        """Start provenance tracking."""
        await self.provenance_storage.start()
        
    async def stop(self):
        """Stop provenance tracking."""
        await self.provenance_storage.stop()
    
    async def store(self, key: str, value: str, namespace: str = "conversations",
                   metadata: Optional[Dict[str, Any]] = None,
                   track_provenance: Optional[bool] = None) -> Dict[str, Any]:
        """
        Store memory with optional provenance tracking.
        
        Maintains full backward compatibility.
        """
        # Determine if we should track provenance
        if track_provenance is None:
            track_provenance = (
                self.track_by_default or 
                namespace in self.tracked_namespaces
            )
        
        # Store the memory (unchanged behavior)
        result = await self.base_service.store(key, value, namespace, metadata)
        
        # Track provenance asynchronously if enabled
        if track_provenance and 'id' in result:
            asyncio.create_task(
                self.provenance_storage.track_creation(
                    memory_id=result['id'],
                    creator=metadata.get('client_id', 'unknown') if metadata else 'unknown',
                    content=value,
                    metadata=metadata or {}
                )
            )
        
        return result
    
    async def retrieve(self, key: str, namespace: str = "conversations",
                      show_provenance: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve memory with optional provenance data.
        
        By default, returns memory without provenance (backward compatible).
        """
        # Get the memory
        memory = await self.base_service.retrieve(key, namespace)
        if not memory or not show_provenance:
            return memory
        
        # Enhance with provenance if requested
        if 'id' in memory:
            prov_data = await self.provenance_storage.get_provenance(memory['id'])
            if prov_data:
                memory['_provenance'] = prov_data
        
        return memory
    
    async def search(self, query: str, namespace: str = None, limit: int = 5,
                    show_provenance: bool = False) -> List[Dict[str, Any]]:
        """
        Search memories with optional provenance data.
        """
        # Perform base search
        results = await self.base_service.search(query, namespace, limit)
        
        if not show_provenance:
            return results
        
        # Enhance with provenance if requested
        for result in results:
            if 'id' in result:
                prov_data = await self.provenance_storage.get_provenance(result['id'])
                if prov_data:
                    result['_provenance'] = prov_data
        
        return results
    
    # Delegate all other methods to base service
    def __getattr__(self, name):
        """Delegate unknown attributes to base service."""
        return getattr(self.base_service, name)