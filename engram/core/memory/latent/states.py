"""
Latent Memory Space State Definitions

Defines the states that a thought can be in within a latent memory space.
"""

class ThoughtState:
    """Enum for thought states in the latent space."""
    INITIAL = "initial"
    REFINING = "refining"
    FINALIZED = "finalized"
    ABANDONED = "abandoned"