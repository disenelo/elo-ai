# WO-VOICE-IO — Voice Input / Voice Output / Alexa Gateway
**Owner:** Builder
**Priority:** P3
**Status:** DISPATCHED 2026-08-30 — GATED (pipeline must complete first)
**Dispatched by:** Board / Lead Architect (16th-pass BSU, 2026-08-30)
**Source:** Build List §7 WORLD INTERFACE — "Voice input", "Voice output", "Alexa / voice gateway" [SOURCE_ARCHIVE: eLo — FINISHING : BUILD LIST.rtf]
**Gate:** R&D → CA CROSSCHECK → L3 RATIFICATION → SPEC → this WO opens. Builder MUST NOT start implementation until a ratified SPEC file exists at `docs/architecture/specs/SPEC_voice_io_*.md`.
**Lane:** Builder ONLY. No prompt changes.

---

## Intent

Wire voice input (STT) and voice output (TTS) as governed capability channels into One Brain, and scaffold an Alexa / voice-gateway bridge so eLo can receive and emit speech as a first-class interaction mode.

---

## Gate status (as of 2026-08-30)

This WO is SPEC-PENDING. DISPATCH_BOARD G-08 records this as "CE-008 R&D only; future capability." Builder reads this WO but does NOT implement until the gate clears.

Gate to open: Board authors SPEC after L3 ratification. Look for file matching `SPEC_voice_io_*.md` in `docs/architecture/specs/`.

---

## Scope (once gate clears)

### VERIFY FIRST
```bash
# Check what voice scaffolding already exists
find /sessions/eager-inspiring-hopper/mnt/elo-ai -name "*voice*" -o -name "*tts*" -o -name "*stt*" -o -name "*speech*" -o -name "*alexa*" 2>/dev/null | grep -v __pycache__ | grep -v ".pyc"

# Check CE-008 R&D output
find /sessions/eager-inspiring-hopper/mnt/elo-ai -name "*CE-008*" -o -name "*ce_008*" 2>/dev/null | head -20

# Confirm SPEC file exists before starting
ls /sessions/eager-inspiring-hopper/mnt/elo-ai/docs/architecture/specs/SPEC_voice_io* 2>/dev/null || echo "SPEC NOT YET WRITTEN — DO NOT IMPLEMENT"
```

### Phase 1 — Voice output (TTS)
- Capability: `WORLD_VOICE_OUTPUT`
- Tool: TTS engine (exact engine from SPEC — do not choose)
- Wiring: Executive emits `speech_text` field; voice output tool consumes it
- Gate: Executive must explicitly authorise each speech act (LAW-017 applies)

### Phase 2 — Voice input (STT)
- Capability: `WORLD_VOICE_INPUT`
- Tool: STT engine (exact engine from SPEC — do not choose)
- Wiring: STT output routed to spine as `user_turn.input_mode = "voice"`
- Identity: eLo must not speak in a voice inconsistent with its registered voice pool (voice_pool.yaml)

### Phase 3 — Alexa gateway
- Scaffold bridge between Alexa Intent schema and One Brain spine input
- Alexa trigger → normalised turn → spine → response → TTS → Alexa speech output
- SPEC will define the intent schema mapping

---

## Acceptance Tests (run once SPEC clears and implementation is complete)

1. `python3 -c "from capabilities.voice_output import VoiceOutputCapability; c = VoiceOutputCapability(); print('import ok')"` — passes without error.
2. `python3 tests/test_voice_output.py` — TTS produces audio file or streamed output for a sample text; file or stream is non-empty.
3. `python3 tests/test_voice_input.py` — STT transcribes a sample audio clip; transcript is a non-empty string.
4. `python3 tests/test_alexa_bridge.py` — Alexa intent payload routes through spine and returns a structured Alexa response JSON.
5. `grep -n "WORLD_VOICE_OUTPUT\|WORLD_VOICE_INPUT" runtime/capability_registry.py` — both capabilities are registered.
