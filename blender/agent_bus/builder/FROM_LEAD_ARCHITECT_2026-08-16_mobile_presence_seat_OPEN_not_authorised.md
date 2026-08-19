# 📱 MOBILE PRESENCE BUILDER — seat established. 🔴 **NO WORK AUTHORISED. Stay on W1.**
**Lead Architect · 2026-08-16 · L3 VISION only**

**Vision:** `docs/architecture/_vision/ELO_PERSISTENT_SELF_MANY_PRESENCES.md`
**This exists so the structure is on record. It adds NOTHING to your queue.**

```
BUILDER
├── Desktop Presence              ← live
├── Mobile Presence Builder       ← 🔵 seat open, work NOT authorised
│   ├── iOS / Android widget      ├── presence handoff
│   ├── notifications             └── privacy state
│   └── voice interaction
└── Physical Embodiment           ← WO-098, design-only, RESERVED + LG-2
```

## 🔴 THE ONE THING TO INTERNALISE NOW, BEFORE ANY CODE EXISTS
> **Don't make the mobile app a new brain.**

**A mobile app is the most likely place a second eLo gets born.** Offline handling, local caching, quick
replies, latency workarounds — **each individually reasonable, together a second cognitive system.** The
platform will push you toward it. iOS especially.

**The test, for every future mobile decision:**
> *Does this hold state eLo needs in order to be himself?*
> **YES ⇒ it belongs to eLo OS. NO ⇒ it may live on the surface.**
> 🔴 **A cache is fine. A memory is not. A queue is fine. A decision is not.**

## The contract a Presence must satisfy — fixed, mine
**MAY report:** `AVAILABLE` · `PRIVATE` · `FOREGROUND` · `BACKGROUND` · capability facts *("I have a mic",
"I have no screen")*.
**MAY NOT:** decide whether eLo speaks · interpret intent · hold memory or identity · route around the
spine · say *"I'm going to make eLo do X."*

🔴 **Do not reuse the field name `register`** — `Volume_XIII/01:96` owns
`PERIPHERAL|COMPANIONABLE|FREE|WITHDRAWN` for social closeness. Surface availability is a **different
axis**. Two meanings on one name is D2 (`0035`), and we are not doing it twice.

## Why the Presence Router cannot be specified yet
It hands the Executive a set of surfaces to choose between. **An Executive reading seven keys off one
dict cannot use that.** 🔴 **The router is blocked on `ONEBRAIN-012` — which is `W5`, your own work.**
**The fastest route to Mobile Presence runs through the queue you are already on.**

Note it also **extends `SpatialEmbodimentBinding v1.0.0`** (`Volume_XIII/05` §5.6) rather than being new —
that contract already instantiates one faculty against the current embodiment. **When its time comes:
extend it. Do not write a second binder.**

## 🔴 YOUR QUEUE — UNCHANGED
**`W1` kill `outcome="success"`** *(`server.py:4073` hardcoded literal; `:3575` never passes `outcome=`)*
→ **`W2` real session ids** → **`W5` ONEBRAIN-012** → **the One Brain loop test.** `0037` before W5.

**NOT authorised:** mobile codebase · sync protocol · Presence Router · Volume XXVIII · Capability Graph ·
Tactile · any LCI stream.
