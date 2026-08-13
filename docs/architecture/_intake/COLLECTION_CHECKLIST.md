# Canon Collection Checklist

What to pull from the different chats, per volume. Tick `[x]` as you gather; paste into
chat or drop a `RAW_*.md` here and I'll canonicalize it.

Legend: **HAVE** = real spec in repo · **STUB** = empty placeholder file · **CODE** =
lives as running code, spec thin · **MISSING** = nothing yet.

---

## Priority 0 — the unlock

- [x] **Master Architecture Bible** — ✅ **FOUND & FILED 2026-07-27** →
      `docs/architecture/ARCHITECTURE_BIBLE.md` (authoritative v1.0, all 27 volumes +
      Knowledge Pyramid + governance model). XXIII–XXVII titles now confirmed.

---

## The 27 volumes — status & what to collect

| Vol | Title | State | What to pull from chats |
|-----|-------|-------|--------------------------|
| I | Philosophy | HAVE (`00_philosophy`) | nothing — confirm only |
| II | Cognitive Principles | HAVE (`17_cognitive_principles`) | nothing |
| III | System Architecture | HAVE (`16_runtime_contracts`) | nothing |
| IV | Cognitive Spine | CODE + `16_spine_runtime` | any spine design notes not in code |
| V | Faculty Contracts | **HAVE — READY FOR REVIEW** | nothing (done this session) |
| VI | Working Memory & Attention | CODE, no volume | working-memory/attention design from the WP_E / attention chats |
| VII | Executive Cortex | CODE (frozen) + STUB `09_executive_faculty` | executive design notes → fill the stub |
| VIII | Memory Architecture | **HAVE — drafted** (`Volume_VIII/`) | ✅ 4 types + consolidation + forgetting spec'd from stack chat; retrieval detail (03 stub) still welcome |
| IX | Dream Architecture | **HAVE — drafted** (`Volume_IX/`) | ✅ canonicalised from the brain/dream chat (2026-07-26); DeepDream + phases spec'd |
| X | Personality Engine | partial (spec'd in V Ch.7) | reconcile with `self/` + `personality_drift` chats |
| XI | Motor Cortex | CODE | avatar/motor notes (UI/Avatar agent chats) |
| XII | Perception System | **HAVE — drafted** (`Volume_XII/`) | ✅ Perception Faculty spec'd from stack chat |
| XIII | Presence Engine | CODE + STUB `14_presence_faculty` | presence design → fill stub |
| XIV | Plugin Architecture | CODE | plugin design notes if any |
| XV | World Model | **HAVE — READY FOR REVIEW** | nothing (done this session) |
| XVI | Multi-Agent Coordination | MISSING | any multi-agent/coordination design |
| XVII | Reflection Engine | spec'd in V Ch.6 | confirm vs any reflection chat |
| XVIII | Self-Evolution | spec'd in V Ch.6/7 | confirm vs any self-evolution chat |
| XIX | Artificial Consciousness Research | MISSING | research questions / framework notes |
| XX | Cognitive Economy | MISSING | cost/latency/attention-budget design |
| XXI | Narrative Identity Engine | partial (`continuity/`) | autobiographical-thread design |
| XXII | Faculty Genome | MISSING | versioned-faculty design |
| XXIII | **_TBD_** | MISSING + no title | **title + scope** (from Bible) |
| XXIV | **_TBD_** | MISSING + no title | **title + scope** |
| XXV | **_TBD_** | MISSING + no title | **title + scope** |
| XXVI | **_TBD_** | MISSING + no title | **title + scope** |
| XXVII | **_TBD_** | MISSING + no title | **title + scope** |

---

## The 11 stub docs (exist as empty placeholders — need content)

Each is one line ("to be written"). Pull the matching design from its chat and I'll fill
it the way I filled `16_spine_runtime` / `17_memory_update`:

- [ ] `01_one_brain.md` (→ Vol IV/I)
- [ ] `02_language_faculty.md`
- [ ] `03_memory_faculty.md` (→ Vol VIII; pairs with `17_memory_update`)
- [ ] `08_capability_faculty.md`
- [ ] `09_executive_faculty.md` (→ Vol VII; note code is FROZEN)
- [ ] `10_cognitive_plan.md`
- [ ] `12_expression_plan.md`
- [ ] `13_conversation_faculty.md`
- [ ] `14_presence_faculty.md` (→ Vol XIII)
- [ ] `15_execution_gate.md`
- [ ] `99_future_embodiments.md`

---

## Where to look, by chat type

- **ChatGPT "Chief Architecture Officer" chats** → the Bible, volume definitions, V/other-volume chapter drafts.
- **Claude Code / builder chats** → runtime contracts, spine, executive, memory internals, WP_* notes.
- **UI / Avatar (Unity) chats** → Motor Cortex (XI), Presence (XIII), expression/embodiment, the `blender_state.json` field agreements.
- **`handovers/` (already in repo)** → S15–S17 Unity↔OS handovers, wiring spec, blendshapes.
- **`~/Documents/DISENELO/memory/memory.md`** → identity/brand Tier 1 (not currently connected).

---

*As you drop content, I update this checklist and the `00_CANON_INDEX.md` status.*
