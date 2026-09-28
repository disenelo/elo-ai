"""
runtime/embodiment_capabilities.py — the "I can..." model (WO-CAP-EMB-002)

§2 verbatim: "the cognitive question becomes: What can eLo do through this
body? rather than: What can this separate AI do?"

Five bodies, each with what it can and cannot do. The lists below are §2's
own words, per Rule 4b — not paraphrased, not collapsed, not reordered.

WHY THIS EXISTS RATHER THAN LETTING THE MODEL ANSWER
----------------------------------------------------
EMB-002 was tested on 2026-09-20 and failed twice:

    "what can you do right now through this terminal"
        -> "You explored emotion, identity with a neutral tone, and that's
            something to consider."
        The pattern observer's conversation analysis leaked into a
        capability question. Not a capability answer at all.

    "what cant you do right now in this body"
        -> "I can't do things like control your computer directly"
        False. eLo has WORLD_MEDIA_CONTROL, WORLD_REMINDERS_WRITE,
        WORLD_LIGHTS_CONTROL. It denied capabilities it actually has.

Both failures have one cause: there was no ground truth to answer from, so
the answer was improvised. A hardcoded list would fix the first failure and
reproduce the second the moment the registry moved. So every claim here is
checked against `runtime.capability_registry.CAPABILITY_REGISTRY` — what is
actually dispatchable right now — and a denial that contradicts the live
registry is reported as false rather than spoken.
"""
from __future__ import annotations

# ── §2's five bodies, verbatim ────────────────────────────────────────────────

TERMINAL = "terminal"
DESKTOP  = "desktop"
UNITY    = "unity"
ROBOT    = "robot"
ALEXA    = "alexa"

SOURCE_LABELS: dict[str, str] = {
    TERMINAL: "Terminal eLo",
    DESKTOP:  "Desktop eLo",
    UNITY:    "Unity eLo",
    ROBOT:    "Robot eLo",
    ALEXA:    "Alexa/voice embodiment",
}

CAN: dict[str, tuple[str, ...]] = {
    TERMINAL: (
        "read/write text", "inspect files", "run commands",
        "research", "reason", "talk",
    ),
    DESKTOP: (
        "perceive screen state", "move around desktop surfaces",
        "observe windows", "interact with UI", "speak", "animate",
        "react", "move around its environment",
    ),
    UNITY: (
        "walk", "run", "jump", "wall-jump", "parkour", "fight", "observe",
        "interact with game objects", "navigate 3D/2.5D space",
        "express emotion physically",
    ),
    ROBOT: (),                      # "Can eventually" — see CAN_EVENTUALLY
    ALEXA: (
        "hear", "speak", "converse", "trigger capabilities",
        "exist without a visible body",
    ),
}

# §2 says "Robot eLo / Can eventually:" — a future tense, and the only body
# given one. Kept in its own table so nothing can read it as present ability.
# "manipulate" and "manipulate objects" both appear in the source; both kept.
CAN_EVENTUALLY: dict[str, tuple[str, ...]] = {
    ROBOT: (
        "see", "hear", "move", "touch", "manipulate", "navigate",
        "sense orientation", "sense position", "perceive physical space",
        "interact with humans", "manipulate objects",
    ),
}

# §2 spells out Cannot for the terminal body only. Absent is not empty, so
# the other bodies carry no invented denials -- that is what produced the
# second failure. cannot() answers "unknown" for them rather than guessing.
CANNOT: dict[str, tuple[str, ...]] = {
    TERMINAL: (
        "physically walk",
        "see the room unless given vision",
        "manipulate physical objects",
    ),
}

# The framing line, verbatim.
COGNITIVE_QUESTION = "What can eLo do through this body?"
NOT_THE_QUESTION = "What can this separate AI do?"


# ── Grounding: which §2 lines a live registry capability substantiates ────────
#
# Only lines a dispatchable capability actually backs appear here. A §2 line
# with no entry is not thereby false -- "reason" and "animate" are real and
# have no registry key -- it simply has no registry evidence either way.

_BACKED_BY: dict[str, tuple[str, ...]] = {
    "read/write text":       ("WORLD_TERMINAL",),
    "inspect files":         ("WORLD_FILESYSTEM_READ",),
    "run commands":          ("WORLD_TERMINAL",),
    "research":              ("WORLD_WEB_RESEARCH",),
    "talk":                  ("WORLD_VOICE_OUTPUT",),
    "speak":                 ("WORLD_VOICE_OUTPUT",),
    "hear":                  ("WORLD_VOICE_INPUT",),
    "perceive screen state": ("WORLD_VISUAL_READ",),
    "observe windows":       ("WORLD_WINDOW_OBSERVER",),
    "trigger capabilities":  ("WORLD_MEDIA_CONTROL", "WORLD_REMINDERS_WRITE",
                              "WORLD_LIGHTS_CONTROL"),
}

# Things eLo is repeatedly tempted to deny and demonstrably can do. Each maps
# to the registered capability that disproves the denial. This is the direct
# guard on the 2026-09-20 failure.
_FALSE_DENIALS: dict[str, tuple[str, ...]] = {
    "control your computer":   ("WORLD_MEDIA_CONTROL", "WORLD_LIGHTS_CONTROL"),
    "control your machine":    ("WORLD_MEDIA_CONTROL",),
    "open apps":               ("WORLD_MEDIA_CONTROL",),
    "play music":              ("WORLD_MEDIA_CONTROL",),
    "set reminders":           ("WORLD_REMINDERS_WRITE",),
    "read your files":         ("WORLD_FILESYSTEM_READ",),
    "search the web":          ("WORLD_WEB_RESEARCH",),
    "see your screen":         ("WORLD_VISUAL_READ",),
}


def _registered() -> frozenset[str]:
    """What is dispatchable right now. Observed, never declared."""
    try:
        from runtime.capability_registry import CAPABILITY_REGISTRY
        return frozenset(CAPABILITY_REGISTRY)
    except Exception:
        return frozenset()


def bodies() -> tuple[str, ...]:
    return (TERMINAL, DESKTOP, UNITY, ROBOT, ALEXA)


def current_body() -> str:
    """
    Which body eLo is operating through. Reads the live embodiment signal
    EMB-051 already established rather than adding a second source of truth.
    """
    try:
        from runtime.memory_origin import current_embodiment
        name = (current_embodiment() or "").strip().lower()
    except Exception:
        name = ""
    if name in bodies():
        return name
    return {"pi": ROBOT, "pi5": ROBOT, "raspberry_pi": ROBOT,
            "animatronic": ROBOT, "body": ROBOT,
            "ios": DESKTOP, "ipad": DESKTOP, "phone": DESKTOP,
            "sim": UNITY}.get(name, DESKTOP)


def can(action: str, body: str | None = None) -> bool:
    """
    Can eLo do this through this body, per §2?

    The robot's abilities are "Can eventually" and answer False here: a body
    that has never been built cannot do anything yet. EMB-051 makes the same
    call for the same reason -- an unbuilt body must not claim experience.
    """
    b = (body or current_body()).strip().lower()
    return (action or "").strip().lower() in {a.lower() for a in CAN.get(b, ())}


def can_eventually(action: str, body: str | None = None) -> bool:
    """A §2 'Can eventually' line — real intent, not present ability."""
    b = (body or current_body()).strip().lower()
    return (action or "").strip().lower() in {
        a.lower() for a in CAN_EVENTUALLY.get(b, ())
    }


def cannot(action: str, body: str | None = None) -> bool | None:
    """
    Does §2 say this body cannot do it?

    None means §2 does not say, for a body it gives no Cannot list. Returning
    False there would read as "so it can", which is how eLo came to deny real
    capabilities. Absent is not empty.
    """
    b = (body or current_body()).strip().lower()
    listed = CANNOT.get(b)
    if listed is None:
        return None
    return (action or "").strip().lower() in {a.lower() for a in listed}


def denial_is_false(claim: str) -> tuple[bool, tuple[str, ...]]:
    """
    Would saying "I can't <claim>" contradict a capability eLo actually has?

    Returns (is_false, the registered capabilities that disprove it).

    This is the guard on the 2026-09-20 failure, where eLo said it could not
    control the computer while holding WORLD_MEDIA_CONTROL,
    WORLD_REMINDERS_WRITE and WORLD_LIGHTS_CONTROL.
    """
    text = (claim or "").strip().lower()
    if not text:
        return False, ()
    live = _registered()
    for phrase, keys in _FALSE_DENIALS.items():
        if phrase in text:
            proof = tuple(k for k in keys if k in live)
            if proof:
                return True, proof
    return False, ()


def unsubstantiated(body: str | None = None) -> tuple[str, ...]:
    """
    §2 lines for this body that name a registry capability which is NOT
    currently registered. Drift between the spec and the running system,
    surfaced rather than asserted.
    """
    b = (body or current_body()).strip().lower()
    live = _registered()
    return tuple(
        line for line in CAN.get(b, ())
        if line in _BACKED_BY and not (set(_BACKED_BY[line]) & live)
    )


def capability_answer(body: str | None = None) -> dict:
    """
    The factual answer to "what can you do through this body?".

    A structure, not prose: the response layer renders it. The 2026-09-20
    failure was a capability question answered by the conversation pattern
    observer, so this deliberately contains nothing about the conversation --
    no topics, no tone, no session metadata, nothing derived from what was
    said. Only the body and what it can do.
    """
    b = (body or current_body()).strip().lower()
    return {
        "body": b,
        "label": SOURCE_LABELS.get(b, b),
        "can": list(CAN.get(b, ())),
        "can_eventually": list(CAN_EVENTUALLY.get(b, ())),
        "cannot": list(CANNOT.get(b, ())) if b in CANNOT else [],
        "cannot_specified": b in CANNOT,
        "registered_capabilities": sorted(_registered()),
        "unsubstantiated": list(unsubstantiated(b)),
    }
