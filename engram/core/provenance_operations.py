#!/usr/bin/env python3
"""
Advanced provenance operations: merging, conflicts, squashing.

Handles the complex git-like operations for memory version control.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..models.provenance import ProvenanceAction, ProvenanceEntry
from .provenance_config import ProvenanceConfig


@dataclass
class MergeConflict:
    """Represents a merge conflict between memory versions."""
    memory_id: str
    source_branch: str
    target_branch: str
    source_content: str
    target_content: str
    base_content: Optional[str] = None  # Common ancestor
    conflict_sections: List[Dict[str, Any]] = None


class ProvenanceOperations:
    """Advanced operations for memory provenance."""
    
    def __init__(self, storage, config: ProvenanceConfig):
        self.storage = storage
        self.config = config
        
    async def merge_branches(self, memory_id: str, source_branch: str, 
                           target_branch: str = "main", 
                           actor: str = "system") -> Dict[str, Any]:
        """
        Merge two branches with automatic conflict resolution.
        
        Returns:
            Dict with merge result or conflict information
        """
        # Get both branch contents
        source_data = await self._get_branch_content(memory_id, source_branch)
        target_data = await self._get_branch_content(memory_id, target_branch)
        
        if not source_data or not target_data:
            return {
                "status": "error",
                "message": "Branch not found"
            }
        
        # Try automatic merge
        merge_result = await self._attempt_auto_merge(
            source_data, target_data, memory_id
        )
        
        if merge_result["status"] == "success":
            # Record successful merge
            await self.storage.track_edit(
                memory_id, actor, ProvenanceAction.MERGED,
                note=f"Merged {source_branch} into {target_branch}",
                with_memories=[source_branch]
            )
            return merge_result
            
        elif merge_result["status"] == "conflict" and self.config.auto_conflict_branch:
            # Create conflict branch
            conflict_branch = await self._create_conflict_branch(
                memory_id, source_branch, target_branch,
                merge_result["conflict"], actor
            )
            
            return {
                "status": "conflict",
                "conflict_branch": conflict_branch,
                "message": "Merge conflict - created conflict branch",
                "conflict": merge_result["conflict"]
            }
        
        return merge_result
    
    async def _attempt_auto_merge(self, source: Dict, target: Dict, 
                                memory_id: str) -> Dict[str, Any]:
        """Attempt automatic merge using 3-way merge algorithm."""
        source_content = source.get("content", "")
        target_content = target.get("content", "")
        
        # Simple case: identical content
        if source_content == target_content:
            return {"status": "success", "content": source_content}
        
        # Find common ancestor (simplified - would use LCA in production)
        base_content = await self._find_common_ancestor(memory_id, source, target)
        
        # Try line-by-line merge
        if base_content:
            merge_result = self._three_way_merge(
                base_content, source_content, target_content
            )
            
            if not merge_result.has_conflicts:
                return {
                    "status": "success",
                    "content": merge_result.merged_content
                }
        
        # Conflict detected
        conflict = MergeConflict(
            memory_id=memory_id,
            source_branch=source.get("branch", "unknown"),
            target_branch=target.get("branch", "main"),
            source_content=source_content,
            target_content=target_content,
            base_content=base_content
        )
        
        return {
            "status": "conflict",
            "conflict": conflict
        }
    
    async def _create_conflict_branch(self, memory_id: str, 
                                    source_branch: str, target_branch: str,
                                    conflict: MergeConflict,
                                    actor: str) -> str:
        """Create a branch containing the conflict for later resolution."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        conflict_branch = self.config.conflict_branch_pattern.format(
            base=target_branch,
            timestamp=timestamp
        )
        
        # Create conflict content with markers if configured
        if self.config.include_conflict_markers:
            content = self._format_conflict_content(conflict)
        else:
            # Just concatenate both versions
            content = f"=== {source_branch} version ===\n{conflict.source_content}\n\n"
            content += f"=== {target_branch} version ===\n{conflict.target_content}"
        
        # Create the conflict branch
        await self.storage.create_branch(
            memory_id, conflict_branch, target_branch, actor, content
        )
        
        return conflict_branch
    
    def _format_conflict_content(self, conflict: MergeConflict) -> str:
        """Format conflict with git-style markers."""
        lines = []
        lines.append(f"<<<<<<< {conflict.target_branch}")
        lines.append(conflict.target_content)
        lines.append("=======")
        lines.append(conflict.source_content)
        lines.append(f">>>>>>> {conflict.source_branch}")
        
        if conflict.base_content:
            lines.append("\n||||||| common ancestor")
            lines.append(conflict.base_content)
        
        return "\n".join(lines)
    
    async def squash_provenance_chain(self, memory_id: str, 
                                    keep_milestones: bool = None) -> Dict[str, Any]:
        """
        Squash long provenance chains to prevent unbounded growth.
        
        Keeps important entries (milestones) if configured.
        """
        if keep_milestones is None:
            keep_milestones = self.config.squash_keep_milestones
            
        prov_data = await self.storage.get_provenance(memory_id)
        if not prov_data:
            return {"status": "error", "message": "No provenance found"}
        
        chain = prov_data.get("chain", [])
        if len(chain) <= self.config.max_chain_length:
            return {"status": "skipped", "message": "Chain within limits"}
        
        # Identify entries to keep
        kept_entries = []
        
        # Always keep first and last
        if chain:
            kept_entries.append(chain[0])  # Creation
            
        if keep_milestones:
            # Keep important actions
            important_actions = {
                ProvenanceAction.MERGED.value,
                ProvenanceAction.CRYSTALLIZED.value,
                ProvenanceAction.FORKED.value
            }
            
            for entry in chain[1:-1]:
                if entry.get("action") in important_actions:
                    kept_entries.append(entry)
        
        # Keep recent entries (last 20%)
        recent_count = max(1, len(chain) // 5)
        kept_entries.extend(chain[-recent_count:])
        
        # Add squash marker
        squash_entry = {
            "actor": "system",
            "action": "squashed",
            "timestamp": datetime.now().isoformat(),
            "note": f"Squashed {len(chain)} entries to {len(kept_entries)}",
            "original_count": len(chain)
        }
        kept_entries.append(squash_entry)
        
        # Update provenance
        prov_data["chain"] = kept_entries
        prov_data["squashed"] = True
        prov_data["squash_count"] = prov_data.get("squash_count", 0) + 1
        
        await self.storage._write_provenance(memory_id, prov_data)
        
        return {
            "status": "success",
            "original_length": len(chain),
            "new_length": len(kept_entries),
            "kept_milestones": keep_milestones
        }
    
    async def check_and_auto_squash(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Check if chain needs squashing and do it if configured."""
        if not self.config.auto_squash:
            return None
            
        prov_data = await self.storage.get_provenance(memory_id)
        if not prov_data:
            return None
            
        chain_length = len(prov_data.get("chain", []))
        if chain_length > self.config.max_chain_length:
            return await self.squash_provenance_chain(memory_id)
            
        return None
    
    async def _get_branch_content(self, memory_id: str, branch: str) -> Optional[Dict[str, Any]]:
        """Get content of a specific branch."""
        # Simplified - would query branch storage
        return {
            "branch": branch,
            "content": f"Content of {branch} branch"
        }
    
    async def _find_common_ancestor(self, memory_id: str, 
                                  branch1: Dict, branch2: Dict) -> Optional[str]:
        """Find common ancestor content for 3-way merge."""
        # Simplified - would trace back through provenance
        return None
    
    def _three_way_merge(self, base: str, source: str, target: str) -> Any:
        """Perform 3-way merge on text content."""
        # Simplified - would use proper diff3 algorithm
        class MergeResult:
            has_conflicts = True
            merged_content = ""
        
        return MergeResult()