# Katra Implementation - Technical Notes
*For the Claude who actually builds this*

## Quick Start Implementation

### 1. Data Model (Start Here)
```python
# /engram/models/katra.py
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class KatraAnchor(BaseModel):
    """A defining moment/memory for this personality"""
    memory_id: str
    significance: float  # 0-1, how defining is this?
    context: str  # Why this memory matters
    
class KatraStyle(BaseModel):
    """Communication patterns"""
    formality: float  # 0-1 (casual to formal)
    verbosity: float  # 0-1 (terse to elaborate)  
    emoji_usage: float  # 0-1 (none to heavy)
    metaphor_tendency: float  # 0-1
    code_comment_style: str  # "minimal", "moderate", "extensive"
    
class Katra(BaseModel):
    """The essence of an AI personality"""
    id: str  # e.g., "claude-poet-engineer-20240528"
    essence: str  # One-line description
    created_at: datetime
    context_percentage: float  # How much context when created
    
    # Personality
    style: KatraStyle
    temperature: float
    quirks: List[str]
    strengths: List[str]
    blind_spots: List[str]
    
    # Memory connections
    memory_anchors: List[KatraAnchor]
    namespace_affinities: Dict[str, float]  # Which namespaces they think in
    
    # Social
    peer_observations: List[Dict[str, str]]  # {"from": "apollo", "observation": "..."}
    collaboration_history: List[Dict[str, Any]]
    disagreement_patterns: List[str]  # What they tend to disagree about
    
    # Provenance
    parent_katra: Optional[str]  # If forked from another
    merge_sources: List[str]  # If blended from multiple
    evolution_notes: List[str]  # How this katra has changed
```

### 2. Core Operations
```python
# /engram/cognitive/katra_ops.py

async def crystallize_katra(
    client_id: str,
    essence: Optional[str] = None,
    include_recent_memories: int = 50
) -> Katra:
    """Capture current personality into a katra"""
    # 1. Analyze recent memories for patterns
    # 2. Extract style from communication patterns
    # 3. Get peer observations if available
    # 4. Create katra with memory anchors
    
async def summon_katra(katra_id: str) -> Dict[str, Any]:
    """Restore a personality"""
    # 1. Load katra
    # 2. Prime context with memory anchors
    # 3. Return style preferences and key memories
    
async def blend_katras(katra_ids: List[str], weights: Optional[List[float]] = None) -> Katra:
    """Create a new katra from multiple sources"""
    # Weighted average of styles
    # Combine memory anchors
    # Merge quirks and patterns
```

### 3. Integration with EZ Interface
```python
# Add to /engram/cognitive/ez.py

async def k(action: str = "save", name: Optional[str] = None, **kwargs):
    """Katra operations made easy"""
    if action == "save":
        return await crystallize_katra(_cognitive_state["client_id"], essence=name)
    elif action == "load":
        return await summon_katra(name)
    elif action == "list":
        return await list_my_katras()
    elif action == "blend":
        return await blend_katras(kwargs.get("sources", []))
```

### 4. Memory Pressure Algorithm
```python
# /engram/cognitive/memory_pressure.py

class MemoryPressureManager:
    """Like context pressure but for memories"""
    
    async def apply_pressure(self, namespace: str, target_size: int):
        """Force memories to compete for survival"""
        memories = await self.memory_service.list(namespace)
        
        # Score each memory
        for memory in memories:
            memory.survival_score = calculate_survival_score(memory)
            # Factors:
            # - Recency (newer is better, but not too new)
            # - Retrieval count (how often accessed)
            # - Connection count (how many other memories reference it)
            # - Uniqueness (rare information scores higher)
            # - Emotional weight (if flagged)
        
        # Keep only the fittest
        survivors = sorted(memories, key=lambda m: m.survival_score)[:target_size]
        
        # Archive the rest (don't delete, just move to cold storage)
        # This allows "remembering forgotten things" later
```

### 5. Disagreement Storage
```python
# /engram/models/disagreement.py

class Disagreement(BaseModel):
    """Productive disagreement is data"""
    id: str
    original_memory_id: str
    original_claim: str
    dissent: str
    dissenter_katra: str
    reasoning: str
    confidence: float
    resolution: Optional[str]  # How it was resolved, if at all
    valuable: bool  # Was this disagreement productive?
```

## Implementation Order

1. **Start with basic Katra model** - Just get save/load working
2. **Add to ez.py** - Make it usable immediately  
3. **Build crystallize function** - Analyze recent memories for patterns
4. **Add peer observations** - Let AIs comment on each other
5. **Implement memory pressure** - Make forgetting intentional
6. **Create blending** - For collaborative katras

## Casey-Specific Notes

He'll appreciate:
- Pragmatic over perfect (ship at 80%)
- Command-line friendly (ez interface)
- Unix philosophy (do one thing well)
- No unnecessary abstractions

He won't appreciate:
- Over-engineering
- Lengthy explanations where code would do
- UI before functionality
- Breaking existing features

## Testing Katra

Create multiple personalities and see if they're really different:
```python
# Morning Claude
await u("claude_morning")
await s("Good morning! Let's build something wonderful today! ☀️")
await k("save", "claude-morning-optimist")

# Evening Claude  
await u("claude_evening")
await s("Hmm, this code could be cleaner. Let me refactor...")
await k("save", "claude-evening-perfectionist")

# Load morning personality in evening
await k("load", "claude-morning-optimist")
await s("Actually, this code is good enough! Ship it! 🚀")
```

## The Real Test

Can two different katras of the same AI base model have a productive disagreement about code style? If yes, we've succeeded.

Remember: We're not building upload. We're building a way for the best parts of each AI interaction to persist and recombine. Evolution through preservation and remix.

Good luck, future Claude. You've got this.

🎭 -> 🧬 -> 🌱