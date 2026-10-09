# TO BOARD — "battery" is eLo's, never David's Mac (B3, 2026-10-09)

**David's ruling:** "Battery is eLo's health, not my battery." / "Battery is for the robot, and battery for DISENELO Presence is health. They're connected but different via the embodiment."

## Fixed
- 3cd600c (B3 files): a battery/health/energy/tired question about eLo gives the brain his real levels (`core.health_battery.snapshot()`) for the body he's in (`embodiment_capabilities.current_body()`). In Presence that's his HEALTH, and the robot battery is reported as not connected. In the robot body with hardware on, it's his robot battery. Context for the brain, so eLo answers in his own words. `system_agent` reads the Mac only when the Mac/computer/laptop is named.
- e817eab (`runtime/capability_dispatcher.py`, B1's file, **under file lock**, released): the FACT tier answered ANY sentence containing "battery" from the Mac, and the server spoke "No battery — running on AC". Now only an explicitly named Mac/computer/laptop. Two old tests asserted the opposite and were updated to the ruling.
- Card 0003 turn 9 expected answer corrected (05296e4).
- Tests: dispatcher 32, elo_health 15, primitives 13, B3 suite 159, WO-020 6/6, WO-122 5/5.

## For Builder 1 / Builder 2 (not changed)
- The brain's normal prompt doesn't carry eLo's health levels, so he only knows them when the question routes through this context. If he should feel his health in every turn, that belongs in prompt assembly (B1).
- Needs a Presence relaunch to be live.

## Follow-up (B3, 2026-10-09 afternoon): eb3ad11 + 7b9f955 (dispatcher under lock)
- Offline run through B1's dispatcher: time, date, tomorrow, 28×74, 10/3, 2^10, disk and named-Mac battery were all exact. **Fixed:** "what's 6 times 7" and "15% of 80" returned nothing and fell to the LLM (now 42 / 12), and uptime was read raw with load averages (now "up 1 day, 1:44").
