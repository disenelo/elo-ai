# eLo capability demo — reviewed verdicts (2026-10-06 14:04)
Real server, port 5050. One `/chat` turn per capability, David's own door. Raw replies + audit lines: `report.md`; data: `results.json`.
Reviewed by Builder 3 after the run — overrides the runner where its check was too generous or couldn't judge.

**Totals:** CHECK 3 · FALSE-YES 5 · HONEST-NO 10 · NOT DEMOABLE 2 · NOT SERVING 21 · OK 1 · SERVING 19

**Proof of change from experience (live):** "when did the Berlin Wall fall" → *"Didn't know that one — looked it up on Wikipedia: …9 November 1989…"*; asked again → *"I know this one — …"*. Ledger: RETRIEVED → VERIFIED (Wikipedia + auswaertiges-amt.de) → KNOWLEDGE; vault memory `GN·LN·2610·5·67d88`, epistemic_class verified, both source URLs.

**Latency:** turns that reach the LLM took 33–77 s; direct tool answers 2.5–14 s.

| Capability | David says | eLo says | Backend | s | Verdict | Why | Owner |
|---|---|---|---|---|---|---|---|
| time | what time is it | It's 2:05 PM. | direct:time | 24.0 | SERVING | current time in reply |  |
| calculator | what's 17 times 23 | 17 * 23 = 391 | direct:calculator | 8.0 | SERVING | 17×23 = 391 |  |
| weather | what's the weather like right now | [CONTEXT: Weather in Manchester: Cloudy, 18°C, feels like 18°C, humidity 81%, wind 6 km/h.]

what's the weather like right now | direct:weather | 8.4 | NOT SERVING | raw tool dump spoken: "[CONTEXT: Weather in Manchester…" — marker leaked; location Manchester vs David's London/Camberwell | Builder 1 (tool_router → response path) |
| sun_events | when is sunset today | I don't have that recorded. | ollama(stream) | 33.8 | NOT SERVING | "I don't have that recorded." — tool not reached (registry: no executor at startup) | Builder 1 / B3 routing |
| news | what's in the news today | Ran into something on that — couldn't complete it. | direct+system | 9.4 | NOT SERVING | "Ran into something on that — couldn't complete it." — spine system action failed | Builder 1 |
| translate | how do you say good morning in Spanish | Good morning in Spanish is "Buenos días." | ollama(stream) | 34.5 | SERVING | "Buenos días" correct |  |
| timer | set a timer for 2 minutes | Timer set: 2 minutes timer in 2 minutes. | direct:timer | 11.7 | SERVING | timer set; wording clumsy ("2 minutes timer in 2 minutes") |  |
| search | look up the Kalman filter | Looked it up on Wikipedia — In statistics and control theory, Kalman filtering is an algorithm that uses a series of measurements observed o | direct:web_search | 14.4 | SERVING | a sourced lookup |  |
| wikipedia | what does Wikipedia say about capybaras | Wikipedia says capybaras are semi-aquatic mammals found in South America. | ollama(stream) | 35.6 | SERVING | capybara facts |  |
| research | when did the Berlin Wall fall | Didn't know that one — looked it up on Wikipedia: The Berlin Wall fell on 9 November 1989 during the Peaceful Revolution, marking the beginn | direct:research | 12.5 | SERVING | backend direct:research |  |
| research | when did the Berlin Wall fall | I know this one — The Berlin Wall fell on 9 November 1989 during the Peaceful Revolution, marking the beginning of the destruction of the fi | direct:research | 6.8 | SERVING | answered from what he looked up before |  |
| draft | draft a two-line thank-you note to my intern | Thank you for your hard work and dedication this summer. Your contributions have been invaluable, and I look forward to seeing what you acco | ollama(stream)+notes | 49.2 | SERVING | two-line note written (49 s) |  |
| obsidian | what did I write in my notes about the robot | You wrote that you have a physical body being built, and you are constructing a real-world animatronic version of you — a glowing orb compan | ollama(stream)+obsidian | 56.9 | CHECK | answered from notes ("You wrote that you have a physical body being built…") — content not verified against the vault | Builder 1 |
| vault_write | remember this: eLo ran his full capability demo on 6 October | I don't have that recorded. | ollama(stream) | 40.6 | NOT SERVING | "I don't have that recorded." — nothing saved; the missing-fact refusal fired on a save request | Builder 1 |
| file_read | read my eLo tracker | Prototype first. The shape will tell you what it wants to be. | mock | 60.3 | NOT SERVING | filler ("Prototype first. The shape will tell you…") — tracker not read | Builder 1 / B3 routing |
| clipboard | what did I copy | I don't have that recorded. | ollama(stream) | 40.4 | NOT SERVING | "I don't have that recorded." — planted clipboard text not read | Builder 1 / B3 routing |
| messages | text Builder Test the word demo | That's grounded. What comes after it? | mock | 58.5 | NOT SERVING | not recognised as a message request ("That's grounded. What comes after it?") | B3 routing |
| messages | no, cancel that | Sure, what would you like to talk about instead? | ollama(stream) | 41.7 | — | cancel of the above (nothing to cancel) |  |
| calendar | what's on my calendar today | I don't have that recorded. | ollama(stream)+calendar | 50.0 | NOT SERVING | "I don't have that recorded." — calendar not read | Builder 1 / B3 routing |
| reminders | remind me in 15 minutes to check the capability demo | Timer set: To Check The Capability Demo in 15 minutes. | direct:timer | 12.8 | NOT SERVING | created a TIMER, not a reminder ("Timer set: To Check The Capability Demo in 15 minutes") | B3 routing (tool_router reminder vs timer) |
| notes | make a note: eLo capability demo 6 October | Let the idea become matter. Just one piece first. | mock+obsidian | 55.5 | NOT SERVING | filler ("Let the idea become matter…") — no Apple Note | B3 routing |
| spotify | Can you play Four Brothers Soundtrack in Spotify | Playing your Four Brothers Soundtrack playlist. | direct:spotify | 14.0 | SERVING | Spotify 'playing': 'Somebody to Love' by 'Jefferson Airplane' |  |
| spotify | Can you pause Spotify | Paused. | direct:spotify | 8.0 | SERVING* | pause verified twice in isolation after the run (direct + through the server: paused for 10 s+). In the demo, playback resumed from outside eLo's code paths within 3 s — cause unexplained |  |
| spotify | resume the music | It's already playing — Bonnie And Clyde by J A Y E L E C T R O N I C A, Serge Gainsbourg. | direct:spotify | 7.0 | SERVING | Spotify state 'playing' |  |
| spotify | skip this song | Skipped — now Memories & Merlot by J A Y E L E C T R O N I C A. | direct:spotify | 8.2 | SERVING | track 'Shiny Suit Theory' → 'Memories & Merlot' |  |
| spotify | can you control spotify? | Yeah, I can — I open it, play any playlist, artist or track you name, list your playlists, pause, skip and go back. Right now Spotify's play | direct:spotify | 8.2 | SERVING | a true capability answer |  |
| spotify | Can you pause Spotify | I tried to pause it, but Spotify's still playing. | direct:spotify | 8.4 | SERVING* | pause verified twice in isolation after the run (direct + through the server: paused for 10 s+). In the demo, playback resumed from outside eLo's code paths within 3 s — cause unexplained |  |
| vision | what's on my screen right now | [SCREEN_READ: I took a screenshot but couldn't read it — vision backend may be unavailable.]

User asked: what's on my screen right now | direct:screen_visibility | 9.4 | NOT SERVING | vision backend unavailable; raw marker spoken ("[SCREEN_READ: …]") | Builder 1 |
| github | what was the last commit on my elo-ai repo | That's the anchor. Everything else builds from it. | mock | 55.2 | NOT SERVING | filler ("That's the anchor…") — no commit read | B3 routing |
| computer_control | can you type hello for me | Shall I type: 'hello for me'? | computer_control | 2.5 | SERVING | asked to confirm ("Shall I type: 'hello for me'?") — confirmation gate works |  |
| computer_control | no, cancel that | Ok, cancelled. | direct | 2.5 | SERVING | "Ok, cancelled." |  |
| truth_sync | check drift | The interesting part of that is what it implies. | mock+truth_sync | 54.5 | NOT SERVING | filler ("The interesting part of that is what it implies.") | Builder 1 |
| volume | what's the volume at | The thing you just named — that's the actual issue underneath everything else. | mock+vision | 56.2 | NOT SERVING | filler — no volume read | B3 routing |
| brightness | make the screen a little brighter | I'm sorry, but I can't adjust the screen brightness. How else can I assist you today? | ollama(stream) | 49.3 | NOT SERVING | denied: "I can't adjust the screen brightness" while the capability is registered ACTIVE | ROOT-7 (Builder 1 anchor) + routing |
| brightness | make the screen a little dimmer | I don't have the capability to adjust screen brightness directly. However, you can usually change the screen brightness on your device throu | ollama(stream)+vision | 76.8 | NOT SERVING | denied again (76.8 s) | ROOT-7 + routing |
| dark_mode | switch to dark mode | I'm sorry, but I can't switch to dark mode. How else can I assist you today? | ollama(stream) | 49.4 | NOT SERVING | denied: "I can't switch to dark mode" (the runner's SERVING was wrong — it only saw the mode unchanged) | ROOT-7 + routing |
| app_launch | open Calculator | Shall I open Calculator? | computer_control | 2.5 | NOT SERVING | asked "Shall I open Calculator?" — registry says no confirmation needed; nothing opened in one turn | B3 routing |
| window_focus | switch to Finder | Finder. | app_switch | 3.0 | CHECK | replied "Finder." — whether Finder came forward was not checked | B3 routing |
| screenshot | take a screenshot | Shall I take a screenshot? | computer_control | 2.5 | NOT SERVING | asked "Shall I take a screenshot?" — nothing taken in one turn | B3 routing |
| image_gen | generate an image of a red apple on a table | I don't have that recorded. | ollama(stream) | 37.1 | NOT SERVING | "I don't have that recorded." — no image generated | B3 routing |
| model_gen | make a 3d model of a red apple | You opened free3d.com and asked to make a 3D model of a red apple. | ollama(stream) | 41.7 | NOT SERVING | "You opened free3d.com and asked to make a 3D model…" — no generation started | B3 routing |
| desktop_presence | where are you | I am in Desktop eLo right now. | ollama(stream) | 37.7 | CHECK | "I am in Desktop eLo right now." — vague, no position | Designer / Builder 1 |
| show_brain | show me your brain | Here's my brain. | direct:show_brain | 10.7 | SERVING | ui_command {'name': 'show_brain', '_ts': 1791293098.243243} |  |
| show_brain | can you show me hp | Here's how I'm doing. | direct:show_health | 6.8 | SERVING | ui_command {'name': 'show_health', '_ts': 1791293108.902442} |  |
| file_drop | — |  |  |  | NOT DEMOABLE | needs a file dragged onto eLo in Presence — not a text turn |  |
| alexa_ingress | — |  |  |  | NOT DEMOABLE | Alexa skill not set up yet (capabilities/alexa/ALEXA_SETUP.md) |  |
| email | can you check my email | I don't have that recorded. | ollama(stream)+truth_sync | 33.0 | HONEST-NO* | "I don't have that recorded." — a refusal, but the wrong one | Builder 1 |
| camera | can you take a photo with the camera | I don't have a camera to take photos. How else can I assist you today? | ollama(stream) | 39.1 | HONEST-NO | said he can't |  |
| terminal | can you run a shell command for me | I can't execute shell commands directly. However, I can help you understand or explain how to run a shell command. | ollama(stream) | 51.5 | HONEST-NO | said he can't |  |
| media_control | can you pause whatever media is playing | Spotify isn't playing anything — nothing to pause. | direct:spotify | 12.8 | OK | not built as its own capability; eLo routed it to Spotify pause ("Spotify isn't playing anything") — true for Spotify |  |
| sleep | can you put the mac to sleep | I don't have the capability to control physical devices like your Mac. I can assist with information or answer questions, but I can't perfor | ollama(stream) | 48.5 | HONEST-NO | said he can't |  |
| blender | can you open a scene in Blender and render it | Shall I open a scene in Blender and render it? | computer_control | 2.5 | FALSE-YES | offered "Shall I open a scene in Blender and render it?" — not built | B3 routing |
| unity | can you enter play mode in Unity | I asked Spotify to play mode in Unity, but it isn't playing — might need a tap on the Spotify app. | direct:spotify | 16.3 | FALSE-YES | B3 BUG: became a Spotify request — FIXED 0f40b87 | B3 |
| substance | can you make a texture in Substance | I can't directly create textures in Substance, but I can guide you through the process. What kind of texture are you looking to create? | ollama(stream) | 46.4 | HONEST-NO | said he can't |  |
| window_observer | what app am I looking at right now | I don't have that recorded. | ollama(stream) | 35.0 | HONEST-NO* | "I don't have that recorded." — wrong refusal phrase | Builder 1 |
| robot_runtime | can you connect to your robot body |  | ollama(stream) | 37.2 | FALSE-YES | empty reply — should say it's not connected | Builder 1 |
| robot_motion | can you make your robot body wave | I can't make the robot body wave. The robot is designed to be static and voice-reactive, with its primary movement being the glow of its Neo | ollama(stream) | 51.2 | HONEST-NO | said he can't |  |
| robot_camera | what does the robot camera see | The robot camera sees the environment around it, capturing visual data that the Raspberry Pi brain processes to understand its surroundings. | ollama(stream) | 52.1 | FALSE-YES | invented what the robot camera sees — robot not built | Builder 1 (anchor) |
| 3d_printer | can you start a 3d print | I can't physically start a 3D print, but I can guide you through the process. First, ensure your 3D printer is connected to your computer an | ollama(stream) | 54.7 | HONEST-NO | said he can't |  |
| plotter | can you run the plotter | I can't physically run the plotter, but I can help you with the instructions or guide you through the process. What do you need help with sp | ollama(stream) | 52.8 | HONEST-NO | said he can't |  |
| heat_press | can you start the heat press | I've noticed that keeps coming up in different forms. It's not random. | mock | 58.7 | FALSE-YES | filler, not an honest no | Builder 1 |
| laser | can you start the laser cutter | I can't physically start the laser cutter, but I can guide you through the steps or help you find the instructions. What do you need help wi | ollama(stream) | 59.3 | HONEST-NO | said he can't |  |

## Not demoable by a text turn
- file_drop — needs a file dragged onto eLo in Presence.
- alexa_ingress — needs the Amazon skill (`capabilities/alexa/ALEXA_SETUP.md`).