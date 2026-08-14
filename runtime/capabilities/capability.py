"""
runtime/capabilities/capability.py — Capability dataclass.

Every capability eLo possesses is described here.
The registry never executes — it only advertises.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# ── Health states ─────────────────────────────────────────────────────────────
ONLINE        = "ONLINE"
OFFLINE       = "OFFLINE"
AUTH_REQUIRED = "AUTH_REQUIRED"
DISABLED      = "DISABLED"
UNAVAILABLE   = "UNAVAILABLE"
FAILED        = "FAILED"
UNKNOWN       = "UNKNOWN"

# ── Capability categories ─────────────────────────────────────────────────────
CAT_UTILITY       = "utility"
CAT_KNOWLEDGE     = "knowledge"
CAT_MEMORY        = "memory"
CAT_COMMUNICATION = "communication"
CAT_MEDIA         = "media"
CAT_SYSTEM        = "system"
CAT_CREATIVE      = "creative"
CAT_DEVELOPMENT   = "development"
CAT_DESKTOP       = "desktop"
CAT_ROBOT         = "robot"
CAT_STUDIO        = "studio"


@dataclass
class Capability:
    id:                     str
    display_name:           str
    category:               str
    description:            str
    verbs:                  list[str]
    synonyms:               list[str]           = field(default_factory=list)
    requires_confirmation:  bool                = False
    requires_api:           bool                = False
    requires_authentication:bool                = False
    online:                 bool                = True
    enabled:                bool                = True
    health_state:           str                 = ONLINE
    execution_priority:     int                 = 5         # 1 = highest
    response_style:         str                 = "direct"  # direct | conversational | confirm
    future:                 bool                = False     # not yet implemented
    agent_module:           str                 = ""        # importable path for health check
    # WO-111: ACK contract — physical actions require confirmation; utilities don't
    ack_required:           bool                = False     # True = must ACK or report failure

    def is_available(self) -> bool:
        return self.enabled and not self.future and self.health_state in (ONLINE,)

    def unavailable_reason(self) -> str:
        if self.future:
            return f"{self.display_name} isn't connected yet."
        if self.health_state == AUTH_REQUIRED:
            return f"I can do that once {self.display_name} is authenticated."
        if self.health_state == OFFLINE:
            return f"{self.display_name} is offline right now."
        if self.health_state == DISABLED:
            return f"{self.display_name} is disabled."
        return f"{self.display_name} isn't available right now."
