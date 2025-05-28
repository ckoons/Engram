#!/usr/bin/env python3
"""
Display and visualization for provenance chains.

Text-based and future graphical representations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from io import StringIO

from ..models.provenance import ProvenanceAction


class ProvenanceDisplay:
    """Format provenance for human-readable display."""
    
    # Unicode characters for tree drawing
    BRANCH = "├─"
    LAST_BRANCH = "└─"
    VERTICAL = "│ "
    EMPTY = "  "
    
    @classmethod
    def format_tree(cls, memory_id: str, provenance_data: Dict[str, Any],
                   show_timestamps: bool = True,
                   highlight_current: bool = True) -> str:
        """
        Format provenance chain as a tree.
        
        Example output:
        memory.123 (main)
        ├─ Apollo: created "Port config at 8080" [10:30]
        ├─ Engram: merged with Rhetor.456 [10:45]
        │  └─ Rhetor.456: "Port config via ENV"
        └─ Apollo: revised "Added fallback" [11:00]
           └─ [CURRENT]
        """
        output = StringIO()
        
        # Header
        current_branch = provenance_data.get("current_branch", "main")
        output.write(f"{memory_id} ({current_branch})\n")
        
        # Process chain
        chain = provenance_data.get("chain", [])
        if not chain:
            output.write("└─ (no history)\n")
            return output.getvalue()
        
        # Format each entry
        for i, entry in enumerate(chain):
            is_last = i == len(chain) - 1
            prefix = cls.LAST_BRANCH if is_last else cls.BRANCH
            
            # Format entry line
            line = cls._format_entry(entry, show_timestamps)
            output.write(f"{prefix} {line}\n")
            
            # Add sub-items (like merged memories)
            if entry.get("with"):
                sub_prefix = cls.EMPTY if is_last else cls.VERTICAL
                for with_id in entry["with"]:
                    output.write(f"{sub_prefix}  └─ {with_id}\n")
            
            # Mark current if it's the last entry
            if is_last and highlight_current:
                sub_prefix = cls.EMPTY if is_last else cls.VERTICAL
                output.write(f"{sub_prefix}  └─ [CURRENT]\n")
        
        return output.getvalue()
    
    @classmethod
    def format_compact(cls, memory_id: str, provenance_data: Dict[str, Any]) -> str:
        """
        Compact one-line format for lists.
        
        Example: memory.123: 3 edits by Apollo, Engram, Apollo (last: 2h ago)
        """
        chain = provenance_data.get("chain", [])
        if not chain:
            return f"{memory_id}: no history"
        
        # Get unique actors
        actors = []
        seen = set()
        for entry in chain:
            actor = entry.get("actor", "unknown")
            if actor not in seen:
                actors.append(actor)
                seen.add(actor)
        
        # Get last edit time
        last_entry = chain[-1]
        last_time = cls._format_relative_time(last_entry.get("timestamp"))
        
        return f"{memory_id}: {len(chain)} edits by {', '.join(actors)} (last: {last_time})"
    
    @classmethod
    def format_detailed(cls, memory_id: str, provenance_data: Dict[str, Any]) -> str:
        """
        Detailed format with full information.
        
        Shows all metadata, branches, squash info, etc.
        """
        output = StringIO()
        
        # Header
        output.write(f"=== Provenance for {memory_id} ===\n\n")
        
        # Metadata
        output.write("Metadata:\n")
        output.write(f"  Current Branch: {provenance_data.get('current_branch', 'main')}\n")
        output.write(f"  Version: {provenance_data.get('version', 1)}\n")
        output.write(f"  Squashed: {provenance_data.get('squashed', False)}\n")
        if provenance_data.get('squashed'):
            output.write(f"  Squash Count: {provenance_data.get('squash_count', 0)}\n")
        output.write("\n")
        
        # Branches
        branches = provenance_data.get("branches", {})
        if branches:
            output.write("Branches:\n")
            for branch_name in branches:
                output.write(f"  - {branch_name}\n")
            output.write("\n")
        
        # Full chain with details
        output.write("History:\n")
        chain = provenance_data.get("chain", [])
        for i, entry in enumerate(chain):
            output.write(f"\n[{i+1}] {cls._format_entry_detailed(entry)}\n")
        
        return output.getvalue()
    
    @classmethod
    def format_diff(cls, memory_id: str, prov1: Dict[str, Any], 
                   prov2: Dict[str, Any]) -> str:
        """Show differences between two provenance states."""
        output = StringIO()
        output.write(f"=== Provenance Diff for {memory_id} ===\n\n")
        
        # Compare chain lengths
        len1 = len(prov1.get("chain", []))
        len2 = len(prov2.get("chain", []))
        
        if len2 > len1:
            output.write(f"+ {len2 - len1} new entries\n\n")
            
            # Show new entries
            new_entries = prov2["chain"][len1:]
            for entry in new_entries:
                output.write(f"+ {cls._format_entry(entry, True)}\n")
        else:
            output.write("No new entries\n")
        
        return output.getvalue()
    
    @classmethod
    def _format_entry(cls, entry: Dict[str, Any], show_timestamp: bool = True) -> str:
        """Format a single provenance entry."""
        actor = entry.get("actor", "unknown")
        action = entry.get("action", "unknown")
        note = entry.get("note", "")
        
        # Special formatting for different actions
        if action == ProvenanceAction.CREATED.value:
            desc = f'created "{note[:50]}..."' if len(note) > 50 else f'created "{note}"'
        elif action == ProvenanceAction.MERGED.value:
            with_ids = entry.get("with", [])
            desc = f"merged with {', '.join(with_ids)}"
        elif action == ProvenanceAction.CRYSTALLIZED.value:
            desc = "crystallized insight"
        else:
            desc = action
            if note:
                desc += f' "{note}"'
        
        line = f"{actor}: {desc}"
        
        if show_timestamp and "timestamp" in entry:
            time_str = cls._format_relative_time(entry["timestamp"])
            line += f" [{time_str}]"
        
        return line
    
    @classmethod
    def _format_entry_detailed(cls, entry: Dict[str, Any]) -> str:
        """Format entry with all details."""
        lines = []
        lines.append(f"Actor: {entry.get('actor', 'unknown')}")
        lines.append(f"Action: {entry.get('action', 'unknown')}")
        lines.append(f"Timestamp: {entry.get('timestamp', 'unknown')}")
        
        if entry.get("note"):
            lines.append(f"Note: {entry['note']}")
        
        if entry.get("with"):
            lines.append(f"With: {', '.join(entry['with'])}")
        
        if entry.get("confidence"):
            lines.append(f"Confidence: {entry['confidence']}")
        
        # Any extra fields
        known_fields = {"actor", "action", "timestamp", "note", "with", "confidence"}
        for key, value in entry.items():
            if key not in known_fields:
                lines.append(f"{key.title()}: {value}")
        
        return "\n  ".join(lines)
    
    @classmethod
    def _format_relative_time(cls, timestamp: str) -> str:
        """Format timestamp as relative time (e.g., '2h ago')."""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromtimestamp(timestamp)
                
            now = datetime.now(dt.tzinfo)
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                return f"{diff.seconds // 3600}h ago"
            elif diff.seconds > 60:
                return f"{diff.seconds // 60}m ago"
            else:
                return "just now"
        except:
            return timestamp
    

class ProvenanceGraphBuilder:
    """
    Future: Build graph data for visualization libraries.
    
    Prepares data for mermaid.js, d3.js, etc.
    """
    
    @classmethod
    def to_mermaid(cls, memory_id: str, provenance_data: Dict[str, Any]) -> str:
        """
        Generate mermaid.js graph definition.
        
        Example output:
        graph TD
            A[Apollo: created] --> B[Engram: merged]
            B --> C[Apollo: revised]
            D[Rhetor: created] --> B
        """
        output = StringIO()
        output.write("graph TD\n")
        
        chain = provenance_data.get("chain", [])
        nodes = {}
        
        # Create nodes
        for i, entry in enumerate(chain):
            node_id = f"N{i}"
            label = f"{entry['actor']}: {entry['action']}"
            nodes[i] = node_id
            output.write(f'    {node_id}["{label}"]\n')
        
        # Create edges
        for i in range(1, len(chain)):
            output.write(f"    {nodes[i-1]} --> {nodes[i]}\n")
        
        # Add merge connections
        for i, entry in enumerate(chain):
            if entry.get("action") == ProvenanceAction.MERGED.value and entry.get("with"):
                # Would need to find the node for merged memory
                output.write(f'    X["{entry["with"][0]}"] --> {nodes[i]}\n')
        
        return output.getvalue()
    
    @classmethod
    def to_d3_json(cls, memory_id: str, provenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate D3.js compatible JSON structure."""
        nodes = []
        links = []
        
        chain = provenance_data.get("chain", [])
        
        # Create nodes
        for i, entry in enumerate(chain):
            nodes.append({
                "id": f"node_{i}",
                "label": f"{entry['actor']}: {entry['action']}",
                "actor": entry['actor'],
                "action": entry['action'],
                "timestamp": entry.get('timestamp')
            })
        
        # Create links
        for i in range(1, len(chain)):
            links.append({
                "source": f"node_{i-1}",
                "target": f"node_{i}",
                "type": "sequence"
            })
        
        return {
            "nodes": nodes,
            "links": links,
            "memory_id": memory_id
        }