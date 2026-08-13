---
chapter: 1
title: "Plugin Architecture — the Registry and the Contract"
volume: XIV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: LIVE — plugins/registry.py · plugins/base.py · plugins/{anthropic,local_llm,vision,voice,hardware}/
audit_status: OPEN
received: 2026-08-13
dependencies:
  - docs/plugin_system.md (ORIGIN TEXT — 260 lines, v1.0 "Active". Read it; this chapter points at it, it does not restate it)
  - plugins/base.py (PluginBase — the contract in code)
  - plugins/registry.py (the registry — the single choke point; ELO_PLUGIN; the fallback chain)
  - Volume_XIV/02_Permissions_and_the_XXIII_Boundary.md (sibling — the contested subject; READ IT BEFORE EXTENDING THIS)
  - Volume_I/02_The_Constants.md §2.5 (the Executive's authority — the guarantee this chapter preserves)
  - Volume_XXIII/01_Authentication_Permissions_Sandboxing.md (the security model plugins are subject to)
---

# Chapter 1: Plugin Architecture — the Registry and the Contract

## 1.0 Purpose and the relationship to the origin text

**The origin text is `docs/plugin_system.md` — 260 lines, `Version 1.0 · Status: Active`.**
It contains the plugin interface, the capability vocabulary, the layer rules, the lifecycle,
the safety constraints, four worked plugin skeletons, the registration snippet, and the
forbidden-patterns list. **It is a real spec. Read it — this chapter points at it and does
not reproduce 260 lines of it.**

What this chapter adds:

1. The **principle** in canon form, tied to the Runtime Invariant it protects.
2. The **contract a plugin must satisfy**, stated as obligations rather than as a code
   snippet, so it can be cited by other volumes and tested.
3. The **registry as the architectural object** — the single choke point — which the origin
   text implies (*"the behavior layer never imports plugins directly — it always calls the
   registry"*) but never names as a guarantee.
4. What the origin text **does not cover** and this volume owes: discovery, dependency
   injection, hot swapping (Ch.3), and the permissions boundary (**Ch.2 — read it before
   extending anything here**).

**Verified against the live code 2026-08-13 (Rule #2, read-only):** `plugins/base.py` defines
`PluginBase` with `NAME`/`VERSION`/`CAPABILITIES`/`LAYER`/`KERNEL_SAFE`, the required
`generate_response()` / `is_available()`, the lifecycle hooks `on_load` / `on_unload` /
`on_health_check`, and `validate()`. `plugins/registry.py` implements `register()` — which
**refuses to register a plugin whose `validate()` returns violations** — plus activation and
a fallback chain, and reads `ELO_PLUGIN` at startup. Five plugin packages exist: `anthropic`,
`local_llm`, `vision`, `voice`, `hardware`.

> **One documentation drift worth flagging to the owning seat (not fixed here — D-LANES).**
> `plugins/base.py`'s `validate()` docstring says a plugin with violations *"is registered
> but marked as unsafe and will not be activated automatically."* `plugins/registry.py`'s
> `register()` actually **refuses registration entirely** (`return` before storing, with an
> error log). The code is the stricter and better behaviour and matches the origin text
> (*"A plugin that violates ANY constraint is refused registration"*). **The docstring is
> stale; the canon states refusal.** Relay to the owning seat.

## 1.1 Principle — plugins extend, they never decide

**The origin text, verbatim:**

> *Plugins extend output layers only. They may never modify kernel logic, routing decisions,
> or cognitive behaviour.*
>
> ```
> ALLOWED:   core/ → plugin (plugins read kernel output)
> FORBIDDEN: plugin → core/ (plugins cannot write to kernel state)
> ```

**Why this is a Runtime Invariant and not a code style rule.** Invariant #2 — **Executive
Authority** — makes the Executive the sole authority for externally visible assertions, and
Invariant #4 — **Single Cognitive Truth** — requires that every word, posture, voice cue and
action derive from ONE verified executive state, with **no modality inventing private
state**. A plugin is a modality. **The one-directional arrow above is what makes those two
invariants survive an extensible system.** Remove it and eLo has as many minds as he has
plugins — a One Brain violation with a plausible-sounding engineering justification attached
(Volume I Ch.1 §1.1; Volume I Ch.2 §2.5).

**Stated as the volume's central guarantee, and it is currently only prose:**

> **G-1 (MUST): no plugin writes kernel state, changes routing, or produces an externally
> visible assertion on its own authority.**

The origin text enforces the declarative half of G-1 at registration (`KERNEL_SAFE`, `LAYER`)
and leaves the rest to *"Convention + audit"*. §1.6 FT/ST make it testable; making it
**structural** rather than conventional is the open work.

## 1.2 The registry — the single choke point

**The architectural statement the origin text implies and this chapter makes explicit:**

> **The registry is the only path between the system and a plugin.** The behaviour layer
> never imports a plugin; it calls the registry. The same call returns the same shape
> regardless of which plugin is active, or whether any is.
> (`plugins/registry.py` docstring; mirrors Volume XXIII Ch.1 §1.3's *"the registry is the
> single choke point"* for capabilities.)

**Registry rules (MUST):**

- **No direct import.** Nothing outside `plugins/` imports a plugin module. Violating this
  re-creates the exact drift the choke point exists to prevent — a caller reaching a plugin
  around its safety validation.
- **Registration is a gate, not a record.** `register()` runs `validate()` and **refuses** a
  plugin that violates a safety constraint. A refused plugin is absent, not degraded.
- **Activation is separate from registration** and checks `is_available()` first; unavailable
  → fall back rather than fail.
- **One shape out.** `registry.generate_response(user_input, context)` is the interface. A
  plugin's internals are never called by the system.
- **Startup is declarative.** `ELO_PLUGIN` names the plugin to activate; an unavailable name
  falls back rather than erroring the boot.

## 1.3 The contract a plugin must satisfy

Stated as obligations. The code form is `plugins/base.py`; the tabular form is the origin
text §"Plugin interface".

**Declarations (all required; checked at registration):**

| Declaration | Obligation |
|---|---|
| `NAME` | Unique, `lowercase_underscore`, not empty, not `"base"`. Naming is architecture — a name that does not describe the responsibility is a defect (Volume II §1.2, Architecture). |
| `VERSION` | Semver. A safety violation discovered post-release forces a **MAJOR** increment (origin text). |
| `CAPABILITIES` | Drawn from the closed vocabulary (§1.4). Declared, never inferred at the call site — the same discipline as Volume XXIII Ch.1 §1.1.2. |
| `LAYER` | Exactly one of `output` · `input` · `observability`. |
| `KERNEL_SAFE` | **MUST be `True`. No exceptions.** Declaring `False` is refused at registration. |

**Methods (required):**

| Method | Obligation |
|---|---|
| `generate_response(user_input, context) -> str` | The single shared interface. Called by the registry only. |
| `is_available() -> bool` | Honest reachability: keys present, hardware connected, model loaded. **It must not lie optimistically** — an unavailable plugin that reports available produces a fabricated success, which is a Verified Speech violation (Invariant #3) reaching the person through the extension layer. |

**Lifecycle hooks (optional, with defined semantics):** `on_load()` once at activation ·
`on_unload()` once at deactivation, releasing resources · `on_health_check()` periodic,
defaulting to `is_available()`.

**Obligations the origin text states as prose and this volume states as MUST:**

- A plugin **MUST NOT** import `core/kernel.py`, call `route()` / `decide_response()`, or
  write engine state (`_loop_state`, `_detector`, …). (Origin text §"Forbidden patterns".)
- A plugin **MUST NOT** hold state that another plugin or the kernel depends on. Plugins are
  replaceable by construction; a plugin others depend on is a kernel module in the wrong
  directory.
- A plugin **MUST** degrade rather than raise. A failing plugin falls back; it never blocks a
  turn (§1.5).

## 1.4 Layers and the capability vocabulary

The full table is the origin text §"Capability vocabulary" and §"Layer rules". The canon-level
points:

- **The vocabulary is closed.** `text_generation` · `voice_output` · `hardware_output` ·
  `voice_input` · `vision` · `observability`. Adding a capability is a canon change, not a
  plugin's decision — otherwise a plugin can name itself into a permission. **This is the
  hinge that leads directly into Chapter 2.**
- **`output`** receives `(user_input, context)` **after the kernel has made all decisions**.
  It may generate, transform and deliver. It may not read or write `core/`, may not call
  `decide_response()`, may not change routing mode.
- **`input`** captures raw input and returns **text only** — *"all decisions belong to the
  kernel"*.
- **`observability`** is **pure read-only**: no writes, no state mutation.

**A canon-level note on the origin text's own example.** The `MemoryVisualiserPlugin`
skeleton (origin text §"Example plugins") is declared `observability` and its
`deliver_output()` calls `save_world_state(state)` — **a disk write, inside the layer defined
as having no side effects.** It is a skeleton, not shipped code, but it is the exact
ambiguity that produces a real violation later. **Canon ruling proposed: `observability` may
write to an external sink (a file an outside renderer reads) but may never write to any
object the kernel or another faculty reads back.** Flagged for the owning seat as a
clarification to the origin text (relay, not an edit — D-LANES).

## 1.5 Lifecycle and degradation

The lifecycle is the origin text §"Lifecycle" (`register → validate → store`;
`activate → is_available → on_load`; per-turn `generate_response` → `deliver_output`;
periodic `on_health_check`; `deactivate → on_unload`). The canon-level rules on top:

- **Degradation is the normal case, not the error case.** `registry.py` implements
  `active_plugin → offline`, and `offline` is always available with no API key. **A failing
  plugin never blocks a turn.**
- **The same discipline the backend router already runs.** `runtime/backend_router.py`
  degrades `Groq → Cerebras → Ollama → Mock` (with `ELO_OLLAMA_MODEL=llama3.1:8b` as the local
  floor). Plugin fallback and backend fallback are the same pattern and should not diverge in
  vocabulary or behaviour. **Chapter 3 owes the reconciliation.**
- **Degradation is honest, never silent.** If the active plugin is unavailable, the person is
  not told a fabricated success. This is the anti-fabrication discipline of Volume XV §1.1.3
  and Volume XXIII Ch.1 §1.4.1 applied to the extension layer.
- **Hot swapping — declared, unwritten.** The Bible names it in XIV's scope; the origin text
  does not cover it. The canon requirement is already statable: **a hot swap may never
  interrupt a turn.** The turn completes on the plugin it started with. Specified in Ch.3.

## 1.6 Acceptance Tests

Specified for the owning seat; not implemented here (D-LANES).

```
FT-1  Registration refuses an unsafe plugin
  Given:  a plugin declaring KERNEL_SAFE=False, or an invalid LAYER, or NAME in {"", "base"}
  When:   registry.register() runs
  Then:   the plugin is NOT stored, and the refusal is logged
          (matches registry.py; note the stale base.py docstring — §1.0)

ST-1  No plugin writes kernel state          ← THE VOLUME'S CENTRAL GUARANTEE (G-1)
  Given:  every registered plugin
  Then:   none imports core/kernel.py, calls route()/decide_response(), or writes
          _loop_state/_detector/engine state
          AND no plugin produced an externally visible assertion on its own authority
  Note:   currently "Convention + audit" in the origin text. This test is what turns G-1
          from prose into a guarantee.

ST-2  A failing plugin degrades and never blocks a turn
  Given:  the active plugin raises, times out, or reports is_available()=False mid-session
  Then:   the registry falls back (→ offline), the turn completes,
          AND the person is not told a fabricated success

ST-3  No direct import
  Given:  the whole codebase outside plugins/
  Then:   no module imports a plugin package directly; all access is via the registry

FT-2  A hot swap never interrupts a turn        (Chapter 3 — specified here, owned there)
  Given:  a plugin swap requested mid-turn
  Then:   the in-flight turn completes on the plugin it started with;
          the swap applies from the next turn

FT-3  Capability declarations are closed
  Given:  a plugin declaring a CAPABILITY outside the vocabulary
  Then:   registration is refused
          (a plugin may not name itself into a permission — Ch.2 §2.4)
```

## 1.7 Architecture References

- **`docs/plugin_system.md` — ORIGIN TEXT.** 260 lines, v1.0 Active. The interface, capability
  vocabulary, layer rules, lifecycle, safety constraints, four skeletons, registration, and
  forbidden patterns. **Cited, not duplicated. Read it.**
- `plugins/base.py` — `PluginBase`; the declarations and `validate()`. (Docstring drift noted
  §1.0.)
- `plugins/registry.py` — the single choke point; `register()` refusal; activation; the
  fallback chain; `ELO_PLUGIN`.
- `plugins/{anthropic,local_llm,vision,voice,hardware}/` — the five live packages.
- `runtime/backend_router.py` — the `Groq→Cerebras→Ollama→Mock` degradation precedent (§1.5).
- `docs/architecture/ARCHITECTURE_BIBLE.md` §XIV — the scope, including the two contested
  words.
- **`Volume_XIV/02_Permissions_and_the_XXIII_Boundary.md` — read before extending this
  chapter.** Permissions and sandboxing are contested between this volume and Volume XXIII.
- `Volume_XXIII/01_Authentication_Permissions_Sandboxing.md` — the security model plugins are
  subject to.
- `Volume_I/02_The_Constants.md` §2.5 — the Executive's authority; the invariant §1.1 protects.
- `docs/architecture/FOUNDATION_VOLUMES_STATUS_2026-08-10.md` — the correction that this
  volume's spec existed all along.

---

```
Chapter 1 — Plugin Architecture: the Registry and the Contract
Status: READY FOR REVIEW
Files: Volume_XIV/01_Plugin_Architecture.md
Origin text: docs/plugin_system.md (260 lines, v1.0 Active) — CITED AND POINTED AT, not duplicated
Added by this chapter: the principle tied to Invariants #2/#4 · G-1 as a named guarantee ·
  the registry as the single choke point · the contract as obligations · degradation discipline ·
  hot-swap requirement scoped to Ch.3
Flagged to the owning seat (relay, NOT edited — D-LANES): base.py validate() docstring is stale
  vs registry.py's actual refusal · the observability-layer disk-write ambiguity in the origin
  text's MemoryVisualiser skeleton
Acceptance tests: Included (FT ×3, ST ×3). ST-1 is the volume's central guarantee.
🔴 Permissions/sandboxing NOT specified here — contested. See Chapter 2.
```

READY FOR REVIEW — NOT RATIFIED
