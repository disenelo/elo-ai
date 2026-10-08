# TO BOARD — Builder 3 tracks A–F status (B3, 2026-10-08 evening)

## Track A (P0): system_primitives, READY FOR BOARD VALIDATION
- `tools/system_primitives.py` (9285c81; card 0007 result filled, 1eaf9ad). Every function returns `{value, source: "macOS", authority: "definitive", confidence, freshness}`. Failures return value None + error and never raise.
- `CAPABILITIES` (+ `side_effect` flag) and `COMMAND_VOCAB` as specced; `system.call(name, …)` / `system.run("CALC", …)`.
- Tests `tests/tools/test_system_primitives.py` 13/13 (headless, real macOS). Real values: "Thursday 8 October 2026"; 28×74 → 2072; 10/3 → 3.3333; battery `{percent: None, power_source: AC, has_battery: False}` (Mac Studio).
- Per the new flow: **Board validates, then notifies Builder 1 to wire it (card 0104).** B3 has not contacted Builder 1.

## Track B (P0): weather, the 5 missing attributes are ALREADY FIXED
- test_wo030_weather_location 14/14 (the attribute errors were cleared in f3defd1; the last failure, a top-level httpx import, was fixed in 97d7a35). Weather suites together: 40/40.
- Weather on open (card 0006): consumer fixed under file lock in 4f5ad98. Needs relaunch + David's visual.

## Track C (P1): Spotify, three bugs DONE earlier, tests green
- Pause routing, capability self-awareness (capability_status live block), and no "Got it" without action (success comes from Spotify's state read back after the command). Tests: capability_status 13/13; interrogative routing 48/48; WO-020 tool routing 6/6.
- Live proof still pending in card 0003 turns 2, 3 and 7 (David).

## Track D (P1): websearch routing, DONE earlier, tests green
- 48/48 interrogative routing (incl. search/research). Live proof pending in card 0003 turn 10.

## Track E (P2): Alexa persistent tunnel (card 0008). The card's premise is wrong; needs David
- The card says a named tunnel gives a stable URL "even with trycloudflare". It doesn't. trycloudflare quick-tunnel URLs are random every run. A named Cloudflare tunnel needs (a) David's Cloudflare account (`cloudflared tunnel login` opens his browser) and (b) a hostname in a zone Cloudflare manages. **disenelo.com's DNS is at Oracle Cloud** (ns1–4.p201.dns.oraclecloud.net), not Cloudflare.
- Options (all free, all need David to create or own the account; B3 can't sign up for him):
  1. **ngrok free static domain**: one permanent `*.ngrok-free.app` URL per free account. Simplest. David creates the account and gives B3 the authtoken plus his static domain.
  2. **Cloudflare named tunnel**: needs a domain on Cloudflare (move a spare domain, or a new cheap one). Most robust.
  3. **Tailscale Funnel**: permanent `<mac>.<tailnet>.ts.net` URL. Needs a Tailscale account and the app.
- Also: earlier today Claude Code's safety check blocked B3 from opening tunnels itself. David ran cloudflared by hand. Whatever is chosen, starting it at login (launchd) is something David has to approve.
- Separately: since 16:05 no Alexa request has reached eLo (watched 5 min). The current quick tunnel answers, so the break is Amazon-side (likely the skill's Test toggle reset or the Endpoint page).

## Track F (P1): David verification turns (card 0003). Waiting on David.
- Offline re-check 2026-10-08: all 10 of B3's turns route correctly (6959684). Turns 6 and 12 are B1 recall.
