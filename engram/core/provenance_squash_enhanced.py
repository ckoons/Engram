#!/usr/bin/env python3
"""
Enhanced squashing strategy for provenance chains.

Casey's insight: Keep the story arc, not just endpoints.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class SmartSquasher:
    """
    Intelligent squashing that preserves the narrative flow.
    
    Instead of just keeping first/last/important, we keep:
    1. Origin (where it started)
    2. Key turning points (major edits, merges)
    3. Recent context (last few steps)
    4. A summary placeholder in the middle
    """
    
    @staticmethod
    def squash_with_narrative(chain: List[Dict[str, Any]], 
                            target_size: int = 8) -> List[Dict[str, Any]]:
        """
        Squash while preserving the story of how the memory evolved.
        
        Args:
            chain: Full provenance chain
            target_size: Target number of entries (default 8)
            
        Returns:
            Squashed chain that tells the story
        """
        if len(chain) <= target_size:
            return chain
            
        # Always keep these
        origin = chain[0]  # The beginning
        current = chain[-1]  # Where we are now
        
        # Find key turning points
        turning_points = SmartSquasher._find_turning_points(chain)
        
        # Keep recent context (last 20% or 3 entries, whichever is smaller)
        recent_count = min(3, max(1, len(chain) // 5))
        recent = chain[-recent_count-1:-1]  # Exclude the last one we already have
        
        # Calculate how many slots we have left
        kept_count = 2 + len(turning_points) + len(recent)  # origin + current + turns + recent
        
        if kept_count < target_size - 1:  # Room for summary
            # We have room, keep everything so far
            result = [origin]
            result.extend(turning_points)
            
            # Add summary placeholder for the squashed middle
            squashed_count = len(chain) - kept_count
            if squashed_count > 0:
                summary = SmartSquasher._create_summary_entry(
                    chain, 
                    start_idx=1, 
                    end_idx=len(chain) - recent_count - 1
                )
                result.append(summary)
            
            result.extend(recent)
            result.append(current)
        else:
            # Need to be more selective
            # Prioritize: origin, most important turns, summary, recent, current
            important_turns = SmartSquasher._rank_turning_points(turning_points)[:target_size-5]
            
            result = [origin]
            result.extend(important_turns)
            result.append(SmartSquasher._create_summary_entry(chain, 1, -recent_count-1))
            result.extend(recent[-2:])  # Just last 2 recent
            result.append(current)
        
        return result
    
    @staticmethod
    def _find_turning_points(chain: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key moments in the memory's evolution."""
        turning_points = []
        
        # Actions that represent key moments
        key_actions = {
            "merged",      # Convergence with another thought
            "forked",      # Divergence into alternatives  
            "crystallized", # Insight emerged
            "conflicted",  # Disagreement recorded
            "revised"      # Major revision (check note for "major")
        }
        
        for i, entry in enumerate(chain[1:-1], 1):  # Skip first and last
            action = entry.get("action", "")
            
            if action in key_actions:
                turning_points.append(entry)
            elif action == "revised" and "major" in entry.get("note", "").lower():
                turning_points.append(entry)
            elif entry.get("confidence", 1.0) < 0.5:  # Low confidence moments
                turning_points.append(entry)
                
        return turning_points
    
    @staticmethod
    def _create_summary_entry(chain: List[Dict[str, Any]], 
                             start_idx: int, end_idx: int) -> Dict[str, Any]:
        """Create a summary entry for squashed portion."""
        if end_idx < 0:
            end_idx = len(chain) + end_idx
            
        squashed_section = chain[start_idx:end_idx]
        
        # Analyze what happened in this section
        actors = defaultdict(int)
        actions = defaultdict(int)
        
        for entry in squashed_section:
            actors[entry.get("actor", "unknown")] += 1
            actions[entry.get("action", "unknown")] += 1
        
        # Create narrative summary
        top_actors = sorted(actors.items(), key=lambda x: x[1], reverse=True)[:3]
        top_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        actor_summary = ", ".join([f"{actor}({count})" for actor, count in top_actors])
        action_summary = ", ".join([f"{action}({count})" for action, count in top_actions])
        
        return {
            "actor": "system",
            "action": "summary",
            "timestamp": datetime.now().isoformat(),
            "note": f"[{len(squashed_section)} steps squashed] {actor_summary} performed {action_summary}",
            "squashed_count": len(squashed_section),
            "squashed_actors": dict(actors),
            "squashed_actions": dict(actions),
            "is_summary": True
        }
    
    @staticmethod
    def _rank_turning_points(turning_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank turning points by importance."""
        # Simple ranking - could be more sophisticated
        def importance_score(entry):
            score = 0
            action = entry.get("action", "")
            
            # Action weights
            if action == "crystallized":
                score += 10
            elif action == "merged":
                score += 8
            elif action == "forked":
                score += 7
            elif action == "conflicted":
                score += 6
                
            # Low confidence is important to preserve
            confidence = entry.get("confidence", 1.0)
            if confidence < 0.5:
                score += 5
                
            # Entries with many connections
            if entry.get("with") and len(entry["with"]) > 1:
                score += 3
                
            return score
        
        return sorted(turning_points, key=importance_score, reverse=True)


class AdaptiveSquasher:
    """
    Even smarter: Adapts squashing based on memory importance and access patterns.
    """
    
    @staticmethod
    def squash_by_importance(chain: List[Dict[str, Any]], 
                           memory_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Important memories keep more history, trivial ones get aggressively squashed.
        """
        importance = memory_metadata.get("importance", 3)
        access_count = memory_metadata.get("access_count", 0)
        resonance = memory_metadata.get("resonance_count", 0)
        
        # Calculate target size based on importance
        base_size = 6
        
        if importance >= 5:
            target_size = base_size + 6  # Keep 12 for critical memories
        elif importance >= 4:
            target_size = base_size + 3  # Keep 9 for important
        elif importance >= 3:
            target_size = base_size      # Keep 6 for normal
        else:
            target_size = 4               # Aggressive squash for trivial
            
        # Adjust for access patterns
        if access_count > 100:
            target_size += 2  # Frequently accessed, keep more
        if resonance > 10:
            target_size += 2  # Many others found meaningful
            
        return SmartSquasher.squash_with_narrative(chain, target_size)