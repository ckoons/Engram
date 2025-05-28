"""
Provenance tracking for Engram memories.

This module provides git-like version control for AI memories,
enabling transparent collaborative cognition.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class ProvenanceAction(Enum):
    """Types of actions that can be taken on a memory."""
    CREATED = "created"
    REVISED = "revised"
    MERGED = "merged"
    FORKED = "forked"
    CONNECTED = "connected"
    SYNTHESIZED = "synthesized"
    WONDERED = "wondered"
    CRYSTALLIZED = "crystallized"


@dataclass
class ProvenanceEntry:
    """A single entry in the provenance chain."""
    actor: str  # Component or AI that made the change
    action: ProvenanceAction
    timestamp: datetime
    note: Optional[str] = None
    with_memories: Optional[List[str]] = None  # For merges/connections
    context: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class MemoryBranch:
    """A branch containing a version of a memory."""
    branch_id: str
    base_memory_id: str
    content: str
    version: int
    created_at: datetime
    created_by: str
    is_active: bool = True
    parent_branch: Optional[str] = None


@dataclass
class MemoryProvenance:
    """Complete provenance information for a memory."""
    memory_id: str
    provenance_chain: List[ProvenanceEntry] = field(default_factory=list)
    branches: Dict[str, MemoryBranch] = field(default_factory=dict)
    current_branch: str = "main"
    forks: List[str] = field(default_factory=list)
    merge_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_provenance(self, entry: ProvenanceEntry) -> None:
        """Add a new provenance entry to the chain."""
        self.provenance_chain.append(entry)
    
    def create_branch(self, branch_name: str, from_branch: str = None) -> MemoryBranch:
        """Create a new branch from current or specified branch."""
        from_branch = from_branch or self.current_branch
        base_branch = self.branches.get(from_branch)
        
        if not base_branch and from_branch == "main":
            # Initialize main branch if it doesn't exist
            base_branch = MemoryBranch(
                branch_id="main",
                base_memory_id=self.memory_id,
                content="",
                version=1,
                created_at=datetime.now(),
                created_by="system"
            )
            self.branches["main"] = base_branch
        
        new_branch = MemoryBranch(
            branch_id=branch_name,
            base_memory_id=self.memory_id,
            content=base_branch.content,
            version=base_branch.version + 1,
            created_at=datetime.now(),
            created_by="",  # Will be set by caller
            parent_branch=from_branch
        )
        
        self.branches[branch_name] = new_branch
        return new_branch
    
    def get_branch_history(self, branch_name: str) -> List[ProvenanceEntry]:
        """Get provenance entries related to a specific branch."""
        # Filter provenance entries related to this branch
        # This is simplified - in production would track branch info in entries
        return self.provenance_chain
    
    def detect_merge_conflict(self, source_branch: str, target_branch: str) -> bool:
        """Check if merging would cause conflicts."""
        source = self.branches.get(source_branch)
        target = self.branches.get(target_branch)
        
        if not source or not target:
            return False
            
        # Simple conflict detection - in practice would be more sophisticated
        return source.parent_branch != target.branch_id and \
               target.parent_branch != source.branch_id


@dataclass
class RetrievalOptions:
    """Options for retrieving memories with provenance."""
    show_provenance: bool = False
    show_branches: bool = False
    show_edits: bool = False
    include_forks: bool = False
    branch: Optional[str] = None
    as_of: Optional[datetime] = None  # Time travel!


class ProvenanceManager:
    """Manages provenance operations for memories."""
    
    def __init__(self):
        self.provenances: Dict[str, MemoryProvenance] = {}
    
    def initialize_provenance(self, memory_id: str, creator: str) -> MemoryProvenance:
        """Initialize provenance for a new memory."""
        provenance = MemoryProvenance(memory_id=memory_id)
        
        # Create initial entry
        entry = ProvenanceEntry(
            actor=creator,
            action=ProvenanceAction.CREATED,
            timestamp=datetime.now()
        )
        provenance.add_provenance(entry)
        
        # Initialize main branch
        main_branch = provenance.create_branch("main")
        main_branch.created_by = creator
        
        self.provenances[memory_id] = provenance
        return provenance
    
    def record_edit(self, memory_id: str, actor: str, action: ProvenanceAction, 
                   note: Optional[str] = None, **kwargs) -> ProvenanceEntry:
        """Record an edit to a memory."""
        provenance = self.provenances.get(memory_id)
        if not provenance:
            provenance = self.initialize_provenance(memory_id, actor)
        
        entry = ProvenanceEntry(
            actor=actor,
            action=action,
            timestamp=datetime.now(),
            note=note,
            **kwargs
        )
        
        provenance.add_provenance(entry)
        return entry
    
    def format_provenance_display(self, provenance: MemoryProvenance) -> Dict[str, Any]:
        """Format provenance for display."""
        return {
            "provenance": [
                {
                    "actor": entry.actor,
                    "action": entry.action.value,
                    "timestamp": entry.timestamp.isoformat(),
                    "note": entry.note,
                    "with": entry.with_memories
                }
                for entry in provenance.provenance_chain
            ],
            "branches": list(provenance.branches.keys()),
            "current_branch": provenance.current_branch,
            "forks": provenance.forks
        }