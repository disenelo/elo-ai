# Compatibility shim — canonical location is core/behavior_engine.py
from core.behavior_engine import *
from core.behavior_engine import (
    generate_offline_response, _recent_closings,
    _assess_grounding, _detect_entities, _detect_concepts, _detect_emotion,
    _classify_input, _is_low_energy,
)
