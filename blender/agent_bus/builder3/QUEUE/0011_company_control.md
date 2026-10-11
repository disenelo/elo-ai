# WO-B3-0011 — Company Control (Device Control via eLo)
**Seat:** Builder 3  
**Priority:** P1 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID 2026-10-10]  
**Date:** 2026-10-10

---

## What

eLo can control devices in David's environment — lights, speakers, other smart home / office systems.

Scope is TBD — Builder 3 must clarify with Board before building. File a scope question to Board: `FROM_BUILDER3_2026-10-10_COMPANY-CONTROL-SCOPE.md`

Questions to answer:
1. Which devices does David want controlled? (Alexa-connected devices, Philips Hue, Apple HomeKit, something else?)
2. Is this triggered by voice (through Alexa) or by text chat with eLo?
3. What commands does David want to start with? (lights on/off, volume, etc.)

---

## Likely approach (pending scope confirmation)

If Alexa-connected devices: Alexa skill can relay device commands through the tunnel — eLo says "turn off the lights" → Alexa smart home skill executes.

If HomeKit: `homekit_controller` Python library — localhost, no cloud needed.

---

## Done when

Scope confirmed by Board. At least one device type controllable via eLo command. Live demo: David tells eLo to do something to a device, it happens.

File scope question to Board first. Do not build until scope is confirmed.
