"""faculties/knowledge — Domain knowledge faculties (psychology, social dynamics, ...)."""
from faculties.knowledge.psychology_faculty import (
    query as psychology_query,
    context_block as psychology_context_block,
    is_domain_trigger as is_psychology_trigger,
    HARD_LANE_NOTE as PSYCHOLOGY_HARD_LANE,
)
from faculties.knowledge.social_dynamics_faculty import (
    query as social_dynamics_query,
    context_block as social_dynamics_context_block,
    is_domain_trigger as is_social_dynamics_trigger,
    HARD_LANE_NOTE as SOCIAL_DYNAMICS_HARD_LANE,
)

__all__ = [
    "psychology_query", "psychology_context_block", "is_psychology_trigger", "PSYCHOLOGY_HARD_LANE",
    "social_dynamics_query", "social_dynamics_context_block", "is_social_dynamics_trigger", "SOCIAL_DYNAMICS_HARD_LANE",
]
