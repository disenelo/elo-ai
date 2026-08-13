"""
company_runtime/company_graph.py — the DISENELO org connectome (divisions → faculties → seats).

Static org structure. Colours are the canonical eLo MoodPalette (runtime/light_engine HSV → hex),
so the Company Brain visualiser obeys the same absolute colour rule as the One Brain.
Dynamic state (work orders, priorities) is NOT here — that is parsed live from the dispatch board.
"""
from __future__ import annotations

# division id -> (label, faculty, mood, mood-hex from light_engine)
DIVISIONS = [
    ("DIV-ARCH", "Architect",        "Executive",       "focus",              "#436b94"),
    ("DIV-ENG",  "Engineering",      "Body / Runtime",  "momentum",           "#e0962d"),
    ("DIV-CRE",  "Creative",         "Imagination",     "creative_discovery", "#3ed1c5"),
    ("DIV-DES",  "Design / Fashion", "Vision",          "play",               "#e65f32"),
    ("DIV-MKT",  "Marketing",        "Expression",      "celebration",        "#fac61e"),
    ("DIV-BIZ",  "Business",         "Planning",        "challenge",          "#c26d23"),
    ("DIV-LEG",  "Legal",            "Constraint",      "thinking",           "#4c3575"),
    ("DIV-RND",  "R&D",              "Learning",        "curiosity",          "#408fb8"),
    ("DIV-MEM",  "Knowledge",        "Memory",          "reflection",         "#543870"),
]

# seat -> (division, label, occupant, capability, status)
SEATS = [
    ("SEAT-EXE-004", "DIV-ARCH", "Lead Architect",  "Claude Opus",             "Systems / canon", "WORKING"),
    ("SEAT-EXE-003", "DIV-ARCH", "Chief Architect", "ChatGPT",                 "Review",          "REVIEW"),
    ("SEAT-ENG-001", "DIV-ENG",  "Python Builder",  "Claude Code",             "Repo code",       "READY"),
    ("SEAT-ENG-004", "DIV-ENG",  "Unity / Avatar",  "Unity agent",             "Avatar",          "WORKING"),
    ("SEAT-ENG-005", "DIV-ENG",  "Game",            "Unity agent",             "Game",            "WORKING"),
    ("SEAT-CRE-001", "DIV-CRE",  "Creative Partner","ChatGPT",                 "Ideation",        "READY"),
    ("SEAT-DES-ID",  "DIV-DES",  "Industrial",      "Claude",                  "Product spec",    "READY"),
    ("SEAT-MKT-002", "DIV-MKT",  "Social Studio",   "ChatGPT",                 "Campaigns",       "READY"),
    ("SEAT-BIZ-002", "DIV-BIZ",  "Finance",         "Claude",                  "Modelling",       "READY"),
    ("SEAT-LEG-006", "DIV-LEG",  "Product Safety",  "Claude + human",          "Compliance",      "READY"),
    ("SEAT-RND-002", "DIV-RND",  "Robotics R&D",    "Gemini",                  "Research",        "READY"),
    ("SEAT-MEM-001", "DIV-MEM",  "Knowledge Mgr",   "Claude",                  "Company memory",  "READY"),
]

# cross-division dependency web (the connectome edges)
LINKS = [
    ("DIV-BIZ", "DIV-LEG"), ("DIV-CRE", "DIV-MKT"), ("DIV-RND", "DIV-ENG"),
    ("DIV-MEM", "DIV-ARCH"), ("DIV-DES", "DIV-MKT"), ("DIV-BIZ", "DIV-DES"),
    ("DIV-ARCH", "DIV-ENG"), ("DIV-MEM", "DIV-CRE"),
]

# which agent/lane string on the board maps to which division (for the board view colour)
LANE_FOR_AGENT = {
    "builder": "Engineering", "python": "Engineering",
    "ui/avatar": "Creative", "design": "Creative", "unity": "Engineering",
    "game": "Game", "architecture": "Runtime", "architect": "Runtime",
    "marketing": "Marketing", "co-creative": "Creative",
    "business": "Business", "legal": "Legal", "r&d": "R&D",
}


def build_graph():
    """Return the graph{} block for company_state.json."""
    seats_by_div = {}
    for sid, div, label, occ, cap, status in SEATS:
        seats_by_div.setdefault(div, []).append(
            {"id": sid, "label": label, "occ": occ, "cap": cap, "status": status}
        )
    divisions = [
        {"id": did, "label": label, "color": hexc, "mood": mood, "faculty": fac,
         "seats": seats_by_div.get(did, [])}
        for (did, label, fac, mood, hexc) in DIVISIONS
    ]
    return {
        "center": {"id": "FOUNDER", "label": "David", "role": "Founder · Intent", "occupant": "David"},
        "divisions": divisions,
        "links": [list(l) for l in LINKS],
    }


def lane_for(agent: str) -> str:
    a = (agent or "").lower()
    for key, lane in LANE_FOR_AGENT.items():
        if key in a:
            return lane
    return "Runtime"
