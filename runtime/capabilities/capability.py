"""
runtime/capabilities/capability.py — Capability dataclass.

Every capability eLo possesses is described here.
The registry never executes — it only advertises.
"""
from __future__ import annotations
from dataclasses import dataclass, field

# ── Authority scopes (WO-CANON-XXIII §A, LAW-017 B2) ─────────────────────────
# Computed by the router before offering to act. Scope never self-promotes.
SCOPE_PERSON   = "PERSON"    # in-flow confirmation; _IMMEDIATE_SAFE allowed
SCOPE_COMPANY  = "COMPANY"   # read-only for eLo; routes through Executive + David L3
SCOPE_RESERVED = "RESERVED"  # structural denial; David is sole L3+LG-2 (software lane)
AUTHORITY_SCOPES = frozenset({SCOPE_PERSON, SCOPE_COMPANY, SCOPE_RESERVED})

# ── Health states ─────────────────────────────────────────────────────────────
ONLINE        = "ONLINE"
OFFLINE       = "OFFLINE"
AUTH_REQUIRED = "AUTH_REQUIRED"
DISABLED      = "DISABLED"
UNAVAILABLE   = "UNAVAILABLE"
FAILED        = "FAILED"
UNKNOWN       = "UNKNOWN"

# ── ACK sources (WO-111 card 05a) ─────────────────────────────────────────────
# Every capability declares which ACK path proves it happened. "unknown" is the
# sentinel default that forces authors to think about it — the registry-level
# test fails if any capability ships with ack_source == ACK_UNKNOWN.
ACK_UNKNOWN     = "unknown"       # not declared — test failure
ACK_SYNC_RETURN = "sync_return"   # agent function returns str on success / raises on failure
ACK_UNITY_ACK   = "unity_ack"     # Unity emits an event to unity_events.json
ACK_NONE        = "none"          # no ACK path yet — executor must report unconfirmed
ACK_SOURCES = frozenset({ACK_SYNC_RETURN, ACK_UNITY_ACK, ACK_NONE})


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
    # WO-111 (card 05a): declared ACK path — the source of truth for how this
    # capability's outcome is confirmed. Must be one of ACK_SOURCES below.
    # Default "unknown" so any newly-added capability that forgets to declare
    # this fails the registry-level test in test_wo111_ack_contract.
    ack_source:             str                 = ACK_UNKNOWN
    # WO-CANON-XXIII §A: authority scope (LAW-017 B2). Router computes this
    # before offering to act; a PERSON "yes" never executes COMPANY or RESERVED.
    authority_scope:        str                 = SCOPE_PERSON

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
