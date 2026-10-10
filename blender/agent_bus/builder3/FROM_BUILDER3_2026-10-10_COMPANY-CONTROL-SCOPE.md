# FROM BUILDER 3 → Board: card 0011 Company Control: scope questions (before building)

## What already exists (checked)
- **Lights:** `capabilities/lights_agent.py` (WO-BA17-LIGHTS-001) via `capability_registry.dispatch_lights` (set_scene / set_brightness / set_colour), wired in `tools/tool_router.py` §8 (scene words: calm / focus / play / dim / off). **Unverified which physical lights it drives, or whether it has ever switched a real light.** B3 will check before anything new is built.
- **Speakers:** the Echo Dot-Studio is now eLo's optional voice (Mac/Echo setting, 185ba6e/0747736). Mac volume/mute: `system_agent`. Spotify playback control: done.
- **macOS:** open apps, dark mode, screenshot, notifications (system_agent / system_primitives).

## Questions for David
1. **Which devices?** Alexa-connected smart plugs/lights (Alexa app), Philips Hue, Apple Home (HomeKit), Govee/LIFX, the heat press, studio lights, something else? Brand names help.
2. **How is it triggered?** Voice through Alexa ("Alexa, tell elo to turn the studio lights off"), chat with eLo, or both?
3. **First 3 commands for the demo?** e.g. studio lights on/off, a "shoot" scene, speaker volume.
4. **Should eLo act on his own** (e.g. dim the lights when he's in Calm) or only when David asks?

## Note on routes (so the answer can be short)
- Apple Home devices → controllable locally from the Mac (Shortcuts / HomeKit), no cloud.
- Alexa-only devices → need Amazon's smart-home APIs (an account link) or an Alexa routine triggered by eLo. More setup.
- Hue → local bridge API, no cloud.
