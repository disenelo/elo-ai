# WO-PLANETARY-KERNEL — Mode Engine + Voice Pool Registry
**Priority:** P1
**Owner:** Builder
**Status:** DISPATCHED 2026-08-30
**Dispatched by:** Lead Architect (Board)
**Spec:** `docs/architecture/specs/SPEC_eLo_planetary_kernel_2026-08-30.md`
**Source:** `docs/architecture/_intake/SOURCE_2026-08-30_planetary_kernel_living_presence_pool.md`

---

## Context

David sent a primary spec for the Planetary Kernel / Living Presence Pool — the full eLo OS interaction model including FEEL→NAME→STABILISE loop, Mode Engine, Voice Pool Registry, South London language register, and /state /build /unstick commands.

Core principle: **"Build a vessel stable enough to carry changing frequencies."**

Four modes: BUILD / PLAY / EXPLORE / REFINE. Every eLo response runs in exactly ONE mode per cycle. ONE output per cycle. No blending.

---

## Scope — Four work items

### A. Create `kernel/voice_pool.yaml`
Data file (not code). All planetary voice pools as structured YAML.

Full YAML content is specified verbatim in SPEC §5. Copy it exactly — do not paraphrase or compress the voice strings. The voice strings are the spec.

File path: `kernel/voice_pool.yaml`

### B. Wire mode selector into `spine.py`
Detect and set current mode (BUILD / PLAY / EXPLORE / REFINE) per turn, before the response is composed.

Logic [SPEC §3]:
- BUILD MODE dominant: SUN + SATURN signals — structure requested, completion focus, step-plan needed
- PLAY MODE dominant: MOON + URANUS signals — experimental, stuck/trying, movement-first
- EXPLORE MODE dominant: JUPITER + GEMINI signals — worldbuilding, ideation, open-ended questions
- REFINE MODE dominant: MERCURY + VENUS signals — editing, clarification, reduction requested

One mode selected per turn. Mode selection stored as a turn-level variable, accessible to language_faculty.

**VERIFY FIRST:** grep for existing `mode` or `response_mode` in `spine.py` and `language_faculty.py` before adding anything. If a mode mechanism exists, extend it — do not duplicate.

### C. Wire South London language register constraint into `language_faculty.py`
Runtime rule [SPEC §6 — per CF-03 ruling: not a new system prompt paragraph, runtime enforcement]:

**Forbidden in responses:**
- Stiff formal English
- Filler openers: "Certainly!", "Of course!", "Great question!", "Absolutely!"
- Management-speak or corporate abstractions
- Over-explanation after the answer is complete

**Required register:**
- Direct, warm, unpretentious
- Mercury Engine: concrete over abstract, pattern-naming over padding
- MOON voice: immediate, first-person, honest — "try it first", "move", "can I?"
- SATURN voice: sparse, matter-of-fact, direct

Add as post-generation filter or shaping constraint inside `language_faculty.py`. Not a prompt paragraph.

**VERIFY FIRST:** check what language shaping already exists in `language_faculty.py` — extend, do not duplicate.

### D. Wire /state, /build, /unstick as named intents in `tools/tool_router.py`
[SPEC §8]

| Intent | Trigger | Required output format |
|---|---|---|
| `/state` | "What state am I in and what is the next smallest useful action?" | STATE → SIGNAL → MODE → ACTION |
| `/build` | "Switch to BUILD MODE, give me a structured step plan." | BUILD MODE + minimal step list |
| `/unstick` | "I'm overloaded — reduce to ONE direction and ONE action." | One line only |

**VERIFY FIRST:** grep `tools/tool_router.py` for existing `/state`, `/build`, `/unstick` before adding.

---

## Acceptance Tests (5 — self-running, no David)

1. **Mode selection test**: given varied prompts, `spine.py` mode selector returns one of exactly: `BUILD`, `PLAY`, `EXPLORE`, `REFINE` — no other values, never empty
2. **Voice pool load test**: `kernel/voice_pool.yaml` loads without error; all 12 planets/facets present; each has at least one voice string
3. **/state command test**: invoking `/state` returns a response in STATE → SIGNAL → MODE → ACTION format — four fields, in order
4. **/unstick command test**: invoking `/unstick` returns exactly ONE line of output — no bullets, no lists, no elaboration
5. **Language register test**: run a sample response through `language_faculty.py` — output does NOT contain: "Certainly", "Of course", "Great question", "Absolutely", or any listed forbidden filler. Verify at least one MOON/SATURN-register phrase present.

---

## References
- Spec: `docs/architecture/specs/SPEC_eLo_planetary_kernel_2026-08-30.md`
- Source (verbatim): `docs/architecture/_intake/SOURCE_2026-08-30_planetary_kernel_living_presence_pool.md`
- Related WOs: WO-RESPONSE-GATE (response gate), WO-SP29 (significance faculty), WO-CCM-SPINE (language/memory enrichment)
- Existing spec to extend: `docs/architecture/specs/SPEC_CP003_PLANETARY_LAYER_2026-08-24.md`
