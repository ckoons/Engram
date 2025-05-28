"""
Enhanced memory model with provenance tracking.

This module extends the basic memory structure to include provenance,
versioning, and branching capabilities.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .provenance import (
    MemoryProvenance, ProvenanceEntry, ProvenanceAction,
    RetrievalOptions, MemoryBranch
)


class MemoryMetadata(BaseModel):
    """Extended metadata including provenance."""
    timestamp: datetime = Field(default_factory=datetime.now)
    client_id: Optional[str] = None
    importance_reason: Optional[str] = None
    
    # Provenance fields
    created_by: str = "unknown"
    last_modified_by: Optional[str] = None
    version: int = 1
    branch: str = "main"
    parent_memory_id: Optional[str] = None
    
    # Collaborative fields
    confidence: float = 1.0
    resonance_count: int = 0  # How many others found this meaningful
    spark_count: int = 0  # How many new thoughts this sparked
    
    # Preserve any additional fields
    extra: Dict[str, Any] = Field(default_factory=dict)


class EnhancedMemory(BaseModel):
    """Memory with full provenance tracking."""
    id: str
    content: str
    category: str = "general"
    importance: int = 3
    tags: List[str] = Field(default_factory=list)
    
    # Enhanced metadata
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    
    # Provenance tracking
    provenance: Optional[MemoryProvenance] = None
    
    # Branching support
    branches: Dict[str, str] = Field(default_factory=dict)  # branch_name -> content
    active_branch: str = "main"
    
    def add_provenance_entry(self, actor: str, action: ProvenanceAction, 
                           note: Optional[str] = None, **kwargs) -> None:
        """Add a provenance entry to this memory."""
        if not self.provenance:
            self.provenance = MemoryProvenance(memory_id=self.id)
            # Add creation entry
            creation_entry = ProvenanceEntry(
                actor=self.metadata.created_by,
                action=ProvenanceAction.CREATED,
                timestamp=self.metadata.timestamp
            )
            self.provenance.add_provenance(creation_entry)
        
        entry = ProvenanceEntry(
            actor=actor,
            action=action,
            timestamp=datetime.now(),
            note=note,
            **kwargs
        )
        self.provenance.add_provenance(entry)
        
        # Update metadata
        self.metadata.last_modified_by = actor
        self.metadata.version += 1
    
    def create_branch(self, branch_name: str, actor: str) -> str:
        """Create a new branch of this memory."""
        if not self.provenance:
            self.provenance = MemoryProvenance(memory_id=self.id)
        
        branch = self.provenance.create_branch(branch_name, self.active_branch)
        branch.created_by = actor
        branch.content = self.content
        
        self.branches[branch_name] = self.content
        
        # Record the branching action
        self.add_provenance_entry(
            actor=actor,
            action=ProvenanceAction.FORKED,
            note=f"Created branch '{branch_name}' from '{self.active_branch}'"
        )
        
        return branch_name
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch."""
        if branch_name in self.branches or branch_name == "main":
            self.active_branch = branch_name
            if branch_name in self.branches:
                self.content = self.branches[branch_name]
            return True
        return False
    
    def to_display(self, options: RetrievalOptions) -> Dict[str, Any]:
        """Convert memory to display format based on retrieval options."""
        display = {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata.dict()
        }
        
        if options.show_provenance and self.provenance:
            display["provenance"] = [
                {
                    "actor": e.actor,
                    "action": e.action.value,
                    "timestamp": e.timestamp.isoformat(),
                    "note": e.note
                }
                for e in self.provenance.provenance_chain
            ]
        
        if options.show_branches:
            display["branches"] = list(self.branches.keys())
            display["active_branch"] = self.active_branch
        
        if options.show_edits and self.provenance:
            # Show just edit count and last editor
            display["edit_count"] = len(self.provenance.provenance_chain) - 1
            if self.provenance.provenance_chain:
                last_edit = self.provenance.provenance_chain[-1]
                display["last_edited_by"] = last_edit.actor
                display["last_edit_time"] = last_edit.timestamp.isoformat()
        
        return display


class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    memory: EnhancedMemory
    options: RetrievalOptions = Field(default_factory=RetrievalOptions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with display options applied."""
        return self.memory.to_display(self.options)