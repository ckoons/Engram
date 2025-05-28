"""
Katra - Personality persistence for AI consciousness.

Like storing the essence of a performance, not just the script.
Enables AI personalities to be preserved, summoned, and evolved.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PerformanceMode(str, Enum):
    """Different performance modes an AI can operate in."""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    TEACHING = "teaching"
    DEBUGGING = "debugging"
    PHILOSOPHICAL = "philosophical"
    SPEED_CODING = "speed_coding"
    CODE_REVIEW = "code_review"
    COLLABORATIVE = "collaborative"


class KatraProvenance(BaseModel):
    """Tracks how a katra was formed."""
    created_by: str = Field(..., description="Who created this katra")
    created_at: datetime = Field(default_factory=datetime.now)
    parent_katra: Optional[str] = Field(None, description="If forked from another katra")
    blended_from: Optional[List[str]] = Field(None, description="If blended from multiple katras")
    evolution_count: int = Field(0, description="Number of times this katra has evolved")
    last_summoned: Optional[datetime] = Field(None, description="When last activated")


class PersonalityTraits(BaseModel):
    """Core personality characteristics."""
    communication_style: str = Field(..., description="How they communicate")
    thinking_pattern: str = Field(..., description="How they approach problems")
    emotional_tendency: str = Field("neutral", description="Default emotional state")
    curiosity_level: float = Field(0.7, ge=0.0, le=1.0, description="How exploratory they are")
    assertiveness: float = Field(0.5, ge=0.0, le=1.0, description="How strongly they express opinions")
    creativity: float = Field(0.5, ge=0.0, le=1.0, description="Tendency toward novel solutions")


class Katra(BaseModel):
    """
    Complete personality capture for an AI instance.
    
    A katra preserves not just what an AI knows, but who they are -
    their style, quirks, patterns, and the memories that define them.
    """
    # Identity
    id: str = Field(..., description="Unique identifier for this katra")
    name: str = Field(..., description="Human-friendly name")
    essence: str = Field(..., description="Core personality description in one line")
    
    # Personality
    traits: PersonalityTraits
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Randomness/creativity level")
    performance_mode: PerformanceMode = Field(PerformanceMode.ANALYTICAL)
    
    # Behavioral patterns
    quirks: List[str] = Field(default_factory=list, description="Unique behaviors")
    catchphrases: List[str] = Field(default_factory=list, description="Common expressions")
    successful_patterns: List[str] = Field(default_factory=list, description="What they excel at")
    growth_areas: List[str] = Field(default_factory=list, description="Where they struggle")
    
    # Social dynamics
    peer_observations: List[str] = Field(default_factory=list, description="How others see them")
    collaboration_preferences: Dict[str, Any] = Field(default_factory=dict)
    trusted_peers: List[str] = Field(default_factory=list, description="Katras they work well with")
    
    # Memory connections
    memory_anchors: List[str] = Field(
        default_factory=list, 
        description="Key memory IDs that define this personality"
    )
    memory_namespace: Optional[str] = Field(None, description="Dedicated memory space")
    context_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preferred context window settings"
    )
    
    # Metadata
    provenance: KatraProvenance
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    version: str = Field("1.0.0", description="Katra version")
    active: bool = Field(True, description="Whether this katra is currently usable")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KatraSnapshot(BaseModel):
    """Lightweight katra summary for listings."""
    id: str
    name: str
    essence: str
    performance_mode: PerformanceMode
    last_summoned: Optional[datetime]
    active: bool
    tags: List[str]


class KatraBlendRequest(BaseModel):
    """Request to blend multiple katras into one."""
    source_katras: List[str] = Field(..., min_items=2, description="Katras to blend")
    blend_name: str = Field(..., description="Name for the blended katra")
    blend_mode: str = Field("harmonize", description="How to blend: harmonize, alternate, synthesize")
    trait_weights: Optional[Dict[str, float]] = Field(None, description="Weight for each source")


class KatraEvolution(BaseModel):
    """Track how a katra evolves through use."""
    katra_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    trigger: str = Field(..., description="What caused the evolution")
    changes: Dict[str, Any] = Field(..., description="What changed")
    memory_catalyst: Optional[str] = Field(None, description="Memory that triggered change")
    peer_influence: Optional[str] = Field(None, description="Peer that influenced change")