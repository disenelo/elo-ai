# eLo's Planet — Game Technical Specification
### *A Soft Cosmic Adventure of the Inner Child*
**Version:** 4.0 — Updated Draft  
**Engine:** Unity (in development)  
**Genre:** 2.5D Side-Scrolling Platformer / Action-Adventure  
**Target Platforms:** PC (Steam), PS5, Xbox, Nintendo Switch, Mobile  
**Mode:** Single Player (Co-op / Multiplayer — phased roadmap, see Section 6)

---

## Table of Contents

1. [Game Overview](#1-game-overview)
2. [Narrative Structure — Book vs Game](#2-narrative-structure--book-vs-game)
3. [Core Gameplay Loop](#3-core-gameplay-loop)
4. [Characters & Companion System](#4-characters--companion-system)
5. [Weapons, Guu & Upgrade System](#5-weapons-guu--upgrade-system)
6. [Multiplayer & Co-op Roadmap](#6-multiplayer--co-op-roadmap)
7. [Core Mechanic — Depth Plane Shifting](#7-core-mechanic--depth-plane-shifting)
8. [World Structure & Stage Map](#8-world-structure--stage-map)
9. [The Lab — Hub World](#9-the-lab--hub-world)
10. [Crates, Collectibles & Power-Ups](#10-crates-collectibles--power-ups)
11. [World Restoration System](#11-world-restoration-system)
11. [Enemy Design](#11-enemy-design)
12. [Camera System](#12-camera-system)
13. [Visual Style](#13-visual-style)
14. [Audio Direction](#14-audio-direction)
15. [UI & UX](#15-ui--ux)
16. [Easter Eggs & Retro References](#16-easter-eggs--retro-references)
17. [Side Content — eLo Racing: Sweetcore Drift](#17-side-content--elo-racing-sweetcore-drift)
18. [Post-Sugarcore Expansion Worlds](#18-post-sugarcore-expansion-worlds)
19. [Technical Notes (Unity)](#19-technical-notes-unity)
20. [Development Roadmap](#20-development-roadmap)

---

## 1. Game Overview

**eLo's Planet** is a 2.5D side-scrolling platformer-adventure inspired by *Metal Slug*, *Zool*, *Rayman*, and *Super Mario*, built around a deeply original narrative universe rooted in inner child healing and emotional growth.

The game is adapted from — but not a retelling of — the illustrated book *eLo: A Soft Cosmic Adventure of the Inner Child*. The book serves as background lore and a prologue experience. The game proper begins at the moment of the invasion: when the Crashing Sugarcore arrives and eLo must use everything he has built to fight back and restore his world.

**Core Motto:** *"Connecting childhood imagination with adult reality."*

**Tone:** Playful. Warm. Emotionally layered. Soft but bold. Think *Metal Slug*'s run-and-gun satisfaction in a world made of candy, solarpunk tech, and cosmic wonder — with heart.

---

## 2. Narrative Structure — Book vs Game

This is the most important structural decision in eLo's Planet. The book and the game are two distinct but connected experiences. The book is not the game. The game expands far beyond the book.

### 2.1 The Book (Prologue Arc)

The book's story — eLo finding the Core Orb, meeting K-7, discovering Chunk's lab, gathering Chunk's six body parts across the planet, and rebuilding Chunk — is experienced in-game as a **prologue arc**. This arc uses a mix of:

- **Cinematic cutscenes** for key emotional story beats (meeting K-7, Chunk awakening, the first sugar disturbance)
- **Light playable stages** woven between cutscenes — low combat, high exploration, tutorial mechanics introduced naturally

The prologue arc teaches the player:

| Stage | What the Player Learns |
|-------|----------------------|
| eLo's World | Basic movement, depth plane shifting |
| Gummy Orchard / K-7 Encounter | K-7 companion mechanics |
| The Living Lab | Lab as home base, Chunk's world, upgrade stations |
| Gathering Chunk's Parts (6 stages) | Stage traversal, light platforming, crate collection |
| Chunk Rebuilt | Full party assembled — all abilities available |

The prologue ends with a cinematic: **the Sugarcore Mothership arrives**. The sky compresses. Sugar spores fall. The world begins to change. This is the moment the *real game begins*.

### 2.2 The Game (Invasion Arc — Main Game)

From the invasion moment onwards, the game diverges completely from the book. The book described the *feeling* of the threat. The game is where the player *lives through it* — stage by stage, tool by tool, restoring eLo's world.

The game's core question is: **Can eLo, K-7, and Chunk reverse the mutation and reclaim the planet before the Sugarcore fully corrupts it?**

Every stage is a corrupted version of a world the player glimpsed during the prologue. Every victory visually restores it. The loop is: **explore → fight → collect → restore**.

### 2.3 Structural Summary

```
PROLOGUE (Book Arc)
├── Cinematic: eLo's World
├── Playable: Gummy Orchard (light / tutorial)
├── Cinematic: Meeting K-7
├── Playable: Tube Waters (exploration focus)
├── Cinematic: The Living Lab & Core Orb
├── Playable: 6 Chunk Part Stages (light combat introduced)
├── Cinematic: Chunk Awakens
└── Cinematic: THE INVASION — Sugarcore Arrives

MAIN GAME (Invasion Arc)
├── Stage 1: Gummy Orchard — CORRUPTED
├── Stage 2: Tube Waters — OVERLOADED
├── Stage 3: Sky Stage — OCCUPIED
├── Stage 4: Desert Dessert — INFECTED
├── Stage 5: Jungle Caves — INFESTED
├── Stage 6: Ice Cream Mountains — CRYSTALLISED
├── Stage 7: Chocolate Mountains — MELTING
├── Stage 8: Ocean Depths — OVERCHARGED
├── Boss Stage: The Sugarcore Mothership
└── Ending Cinematic: World Restored / Universe Opens
```

---

## 3. Core Gameplay Loop

The game loop is the heartbeat of eLo's Planet. It is simple, satisfying, and repeatable — with depth added through upgrades, companions, and depth plane exploration.

### 3.1 The Loop

```
ENTER STAGE (corrupted world)
        ↓
EXPLORE — move through depth planes, find paths
        ↓
FIGHT — encounter mutated sugar enemies
        ↓
COLLECT — smash crates, gather Liquid Guu from enemies,
          pick up food/apples/power-ups
        ↓
BUILD / UPGRADE — use Crystallised Guu at upgrade stations
                  to unlock new weapons and tools
        ↓
CLEAR STAGE — defeat stage boss or reach restoration point
        ↓
WORLD RESTORES — corrupted stage visually heals
        ↓
NEXT STAGE UNLOCKS
```

### 3.2 Stage Entry

eLo runs in from the left. No preamble, no setup. The corrupted world is immediately visible — over-saturated colours, jittery enemies patrolling, the air thick with sugar disturbance. The player is dropped straight into it, **SuperGuu Pistol drawn**.

Between stages, eLo returns to **the lab** — the hub world where upgrades happen, companions regroup, and the next stage is selected.

### 3.3 Stage Completion

When a stage is cleared, a **restoration sequence** plays: the corruption lifts, colours return to their natural soft palette, mutated enemies dissolve into gentle sparkles, and the environment literally heals — gummy plants regrow, water clears, sky softens. This is a core emotional reward. It should feel *earned*.

---

## 4. Characters & Companion System

### 4.1 Companion Model

The companion system is inspired by two classic references:

- **Sonic the Hedgehog 2 (Tails model):** K-7 follows eLo automatically in single player, mirroring his movements, assisting in combat, and can be nudged/directed by the player without requiring a full control switch.
- **Donkey Kong Country 2 (Diddy/Dixie model):** In single player, the player can **switch active control** between eLo, K-7, and Chunk at any time. Each character has a distinct move set and purpose. When not active, companions follow automatically (like Tails). In multiplayer, each player controls one character independently.

### 4.2 eLo (Primary Player Character)

> *The inner child. Curious, calm, always moving forward.*

| Attribute | Detail |
|-----------|--------|
| Movement | Fluid, bouncy, responsive. Rayman-influenced platforming. |
| Combat | Ranged — SuperGuu Pistol as base weapon, upgradeable arsenal |
| Special | Depth plane shifting — only eLo can initiate a plane shift |
| Expression | No eyes. Mouth only. Posture and glow communicate emotion. |
| Default State | Solo runner with SuperGuu Pistol — no navigation tool in hand |

### 4.3 K-7 (Speed / Recon Companion)

> *Seven forms. Night. Knight. Pure instinct.*

| Attribute | Detail |
|-----------|--------|
| Movement | Fastest of the three — dashes, leaps, rapid direction changes |
| Combat | Close-range — tackles, bite attacks, form-based special moves |
| Special | Sniffs out hidden depth plane entrances, secret crates, and lore collectibles. Form shifts change combat ability. |
| Expression | No eyes, no mouth. 100% body language and colour shifts. |
| Colour States | Black = alert/combat → Brown = calm/explore → Amber = joyful → Grey = sensing/hidden |
| Seven Forms | Each form grants a specific ability (speed burst, stealth, heavy strike, sonar ping, etc.) — forms unlock progressively through gameplay |

**K-7 in Single Player:** Follows eLo automatically (Tails-style). Can be switched to active control. When active, eLo follows K-7.

**K-7 in Co-op:** Player 2 controls K-7 independently.

### 4.4 Chunk (Heavy / Base Companion)

> *Ever-learning. Soft but unstoppable. The team's foundation.*

| Attribute | Detail |
|-----------|--------|
| Movement | Slowest — deliberate, weighty, satisfying. Each footfall has impact. |
| Combat | Heavy — magnetic arm throws, stomp attacks, vehicle deployment |
| Special | Size-shifting (keyring to mountain). Opens blocked paths. Deploys vehicles. Interior access when large. |
| Expression | No eyes. Communicates through mechanical hums, glows, and movement. |
| Size States | Keyring (carried by eLo), Standard (combat companion), Large (blocks/bridge), Mountain (traversal/boss assist) |
| Vehicles | Deploys: buggy, helicopter, submarine, jetpack, skateboard — each unlocked progressively |

**Chunk in Single Player:** Follows eLo automatically. Switch to active control for size shifts and vehicle deployment. When Chunk is mountain-size and eLo enters his interior, the camera switches to inside-Chunk perspective.

**Chunk in Co-op:** Player 3 controls Chunk independently.

### 4.5 Character Switch Summary

| Active Character | Following Automatically |
|-----------------|------------------------|
| eLo | K-7 trails + assists combat, Chunk follows at distance |
| K-7 | eLo follows K-7's lead, Chunk trails |
| Chunk | eLo and K-7 follow — useful for clearing paths before switching back |

---

## 5. Weapons, Guu & Upgrade System

### 5.1 Guu — The Core Resource

Guu is the substance that powers eLo's weapons. It is harvested from defeated enemies and found in crates. Guu exists in two forms:

| Type | Source | Use |
|------|--------|-----|
| **Liquid Guu** | Drops from defeated enemies, found in crates | Ammo — fuels all weapons |
| **Crystallised Guu** | Found in deep crates, rare enemy drops, stage secrets | Upgrade currency — spent at upgrade stations |

Liquid Guu is abundant and flows freely through combat. Crystallised Guu is rare and precious — the player must choose upgrades carefully.

### 5.2 The SuperGuu Pistol (Starting Weapon)

eLo's default weapon. Single shot, reliable, infinite as long as Liquid Guu supply holds. The pistol itself can be upgraded through Crystallised Guu — it does not transform into a different weapon, but its stats improve.

| Upgrade Tier | Effect |
|-------------|--------|
| Tier 1 (Base) | Single shot, moderate speed, standard Guu cost |
| Tier 2 | Faster fire rate, slightly larger projectile |
| Tier 3 | Double shot (two simultaneous projectiles) |
| Tier 4 | Charged shot — hold to charge, release for a heavy blast |
| Tier 5 (Max) | Full auto mode with visual glow effect |

### 5.3 Unlockable Weapons

New weapons are unlocked by spending Crystallised Guu at **upgrade stations** (found within stages and inside Chunk's lab). Each weapon has its own Liquid Guu cost per shot.

| Weapon | Description | Unlock Stage |
|--------|-------------|--------------|
| SuperGuu Pistol | Starting weapon — reliable, upgradeable | Default |
| Guu Cannon | Wide spread shot — great for crowds | Stage 2 |
| Sticky Blaster | Fires adhesive Guu — slows enemies, sticks to surfaces | Stage 3 |
| Reversal Launcher | Restores mutated enemies to neutral — non-lethal option | Stage 4 |
| Heavy Guu Mortar | Slow fire, massive damage — unlocked with Fat Mode | Stage 5 |
| Energy Beam | High-energy concentrated beam — pierces through enemies | Stage 7 |
| Guu Grenades | Lob-arc explosive — area damage | Stage 6 |

### 5.4 Upgrade Stations

Upgrade stations appear at the end of stages and inside Chunk's lab interior. The player spends Crystallised Guu here to:

- Upgrade the SuperGuu Pistol tiers
- Unlock new weapons
- Upgrade K-7's form abilities
- Unlock Chunk's vehicle deployments
- Purchase power-up capacity increases (carry more food/health items)

---

## 6. Multiplayer & Co-op Roadmap

Multiplayer is planned but not the current development priority. The game is being built solo-first — the companion AI handles K-7 and Chunk in single player. Multiplayer layers on top of the same system.

### 6.1 Development Phases

| Phase | Mode | Description |
|-------|------|-------------|
| Phase 1 (Current) | Single Player | eLo solo, K-7 and Chunk as AI companions (Tails/DKC2 model) |
| Phase 2 | Local Co-op | 2-player split — Player 1: eLo, Player 2: K-7 or Chunk |
| Phase 3 | Full 3-Player Co-op | Each player controls one character independently |
| Phase 4 | Online Multiplayer | Full online co-op across all platforms |

### 6.2 Character Roles in Co-op

| Player | Character | Role |
|--------|-----------|------|
| Player 1 | eLo | Lead — depth shifting, ranged combat, stage exploration |
| Player 2 | K-7 | Recon — scouting, speed, secret detection, close combat |
| Player 3 | Chunk | Heavy — path clearing, vehicle deployment, base access |

---

## 7. Core Mechanic — Depth Plane Shifting

The defining mechanic of eLo's Planet. The world is not a series of linear levels — it is one continuous layered planet with 5+ depth planes within each stage.

### 7.1 How It Works

- eLo can shift between depth planes using a dedicated input (button + direction)
- Each plane has its own terrain, enemies, crates, and secrets
- The camera smoothly transitions to frame the new depth layer
- K-7 can **sniff out** entrances to hidden planes — a visual cue (colour shift + sniff animation) alerts the player
- Chunk's size-shifting can **open** blocked plane transitions — shrink to pass through a gap, grow to bridge a drop

### 7.2 Plane Structure Per Stage

| Plane | Content | Access |
|-------|---------|--------|
| Foreground | Primary combat, main path, crates | Default |
| Mid-Ground | Exploration, standard collectibles | Default |
| Background 1 | Hidden paths, bonus enemies, Crystallised Guu | Wall jump or K-7 sniff |
| Background 2 | Stage secrets, upgrade station access | Unlocked by clearing Background 1 |
| Deep Background | Lore collectibles, retro easter eggs, rare crates | Full exploration reward |

### 7.3 Visual Feedback

- Active plane: sharp focus, full colour saturation
- Inactive planes: soft parallax blur, slight desaturation
- Shift animation: brief depth shimmer — translucent portal ripple around eLo
- Camera transition: smooth ease, approximately 0.3–0.5 seconds

---

## 8. World Structure & Stage Map

### 8.1 Prologue Stages (Book Arc — Light Play)

| Stage | Environment | Primary Purpose |
|-------|-------------|-----------------|
| eLo's World | Soft candy forest, floating lands, healing waters | Movement tutorial, world introduction |
| Gummy Orchard | Dense candy trees, glowing roots, fireflies | Depth plane intro, K-7 encounter |
| Tube Waters | Translucent neon tubes over water, floating islands | Crate collection intro, Guu introduction |
| Candy Orchard (Doughnut Cave) | Gummy apple trees, cherry bushes | Light combat intro |
| Cotton Candy Sky | Floating clouds, wind platforms | Vertical movement, jetpack preview |
| Soda Pop Geysers | Fizzing ground, soda-burst launch pads | Physics traversal |
| Marshmallow Mist Maze | Soft shifting fog paths | Patience / instinct navigation |
| Stardust Hollow | Glitter crater, celestial silence | Zero-gravity movement |
| The Living Lab | Chunk's cyberpunk garden interior | Chunk awakening, full team assembled — **the hub introduced here** |

### 8.2 Main Game Stages (Invasion Arc — Full Combat)

Each stage is a corrupted version of a world the player saw in the prologue. The corruption changes the visual tone, enemy population, and traversal hazards.

| Stage | Corrupted Environment | Key Mechanic | Boss |
|-------|----------------------|--------------|------|
| 1 — Gummy Orchard CORRUPTED | Over-saturated, mutated gummy trees, sticky terrain | Sticky Blaster introduced | Gummy Lord — giant mutated gummy bear |
| 2 — Tube Waters OVERLOADED | Neon tubes crackling with energy, water turned to Guu | Submarine deployment | Tube Hydra — overcharged water beast |
| 3 — Sky Stage OCCUPIED | Doughnut spaceships patrolling, cloud platforms unstable | Jetpack / helicopter combat | Doughnut Flagship — aerial boss |
| 4 — Desert Dessert INFECTED | Caramel hardened to rock, gummy cactus firing spines | Buggy / skateboard deployment | Caramel Colossus — slow, massive |
| 5 — Jungle Caves INFESTED | Dark cookie-crystal formations, thick Guu fog | High-energy beam weapon unlocked | Cookie Hive Queen |
| 6 — Ice Cream Mountains CRYSTALLISED | Frozen sugar spires, slippery crystallised paths | Heavy Guu Mortar unlocked | Frost Sugarcore Shard — mini-boss |
| 7 — Chocolate Mountains MELTING | Fudge rivers, collapsing cocoa cliffs | All vehicles available | Chocolate Titan |
| 8 — Ocean Depths OVERCHARGED | Electric jellyfish swarms, deep Guu currents | Submarine full combat | Jellyfish Mothernet |
| Final — Sugarcore Mothership | Crystalline white rotating cube-rooms, pure energy | All tools and abilities required | The Sugarcore Core (3 phases) |

### 8.3 Stage Connections

Stages connect via depth plane shifts at their edges. Completing a stage's deep background plane may unlock a shortcut into the next stage's mid-ground — rewarding thorough explorers.
---

## 9. The Lab — Hub World

### 9.1 Overview

The lab is Chunk's cyberpunk garden base — first seen at the end of the prologue when Chunk is fully assembled. Once the invasion begins, the lab becomes the **hub world** eLo returns to between every stage. It is a place to breathe, upgrade, and regroup before heading back into the corrupted world.

The lab is not a menu screen. It is a fully explorable space — warm, living, and growing. Spending time in it is its own small reward.

### 9.2 What the Lab Contains

| Area | Function |
|------|----------|
| Upgrade Station | Spend Crystallised Guu to unlock weapons and upgrade the SuperGuu Pistol |
| Weapon Rack | View, equip, and switch between unlocked weapons |
| K-7 Den | K-7's resting area — interact to check form unlock progress |
| Chunk's Interior | Accessible when Chunk is in large form — extra upgrade options and lore |
| World Map Table | Holographic planet map showing which stages are cleared and restored |
| Crate Storage | Any carried crates not opened in-stage can be smashed here |
| Healing Station | Restore health to full before the next stage |
| Lore Wall | Reflection Phrases and retro cartridges collected are displayed here |

### 9.3 Lab Progression

The lab itself **grows visually** as the player clears stages and restores the world. Early in the game it is dark and minimal — running on emergency power after the invasion. As more stages are restored, more of the lab's natural solarpunk character returns: plants regrow inside, lights brighten, robotic arms tend to seedlings again. By the time the Sugarcore is defeated, the lab is fully alive.

### 9.4 The Core Orb in the Lab

The Core Orb sits at the centre of the lab — it does not travel with eLo into stages. It pulses gently in the background while eLo is in the hub, and its glow strengthens as more of the world is restored. It is a visual indicator of overall progress, not a gameplay tool in the field.

### 9.5 Stage Selection

From the lab, the player selects the next stage via the **World Map Table** — a holographic display showing eLo's Planet and the current state of each region (corrupted, in progress, or restored). eLo walks to the map, selects a region, and runs directly into the stage from the left. No loading screen overlay — the transition is seamless.


---

## 10. Crates, Collectibles & Power-Ups

### 10.1 Crates

Crates are **randomised** — each crate is a risk/reward moment. The player never knows exactly what they'll get, which keeps the loop exciting. Crate types are visually distinct by colour and texture, giving loose hints at contents without guaranteeing them.

| Crate Type | Visual | Possible Contents |
|------------|--------|------------------|
| Standard Crate | Wooden, candy-striped | Liquid Guu, food, common power-up |
| Metal Crate | Chrome, dented | More Liquid Guu, medium power-up |
| Glowing Crate | Gold glow, orb-like | Crystallised Guu, rare power-up |
| Dark Crate | Deep purple, cracked | High-risk: large reward OR trap (enemy spawns) |
| Tiny Crate | Small, bouncing | Small Guu refill, single food item |

### 10.2 Food & Health Items

Food items restore health. All food fits the candy-cosmic aesthetic.

| Item | Health Restored |
|------|----------------|
| Gummy Apple | Small restore |
| Doughnut | Medium restore |
| Ice Cream Scoop | Large restore |
| Healing Water Drop | Full restore (rare) |
| Cotton Candy | Gradual restore over time |

### 10.3 Power-Up States

| Power-Up | Effect | Visual |
|----------|--------|--------|
| Sugar Rush | Speed boost, rapid fire | Orange glow, motion trail |
| Fat Mode | Slowed movement, heavy bullets, crush enemies by landing | eLo expands, bouncy physics |
| Core Charged | All abilities enhanced, brief invincibility | Gold aura, eLo pulses with energy |
| K-7 Frenzy | K-7 enters rapid combat mode automatically | K-7 glows amber, all seven forms flicker |
| Chunk Surge | Chunk grows mid-stage, clears a path | Chunk briefly enlarges, screen shakes |
| Stealth | Near-invisible, reduced enemy aggro | Deep black shimmer on both eLo and K-7 |

---

## 11. World Restoration System

### 11.1 Overview

World restoration is a core emotional and visual mechanic. When a stage is cleared, the player witnesses their effort translated into a visible, beautiful change in the world. This is the game's primary reward loop beyond weapons and upgrades.

### 11.2 Restoration Sequence

When a stage boss is defeated or the stage restoration point is reached:

1. The corruption visual filter lifts — colours shift from over-saturated/distorted back to the world's natural soft palette
2. Mutated enemies in the stage dissolve into gentle sparkles and reset
3. Environmental healing animations play — plants regrow, water clears, damaged terrain repairs
4. A brief cinematic shows the restored version of the stage — the same environment the player saw in the prologue, now healed
5. The stage is added to a **world map restoration tracker** — the player can visually see their planet healing across the full map

### 11.3 Partial Restoration

During a stage (before clearing), collecting enough Liquid Guu and using the Reversal Launcher on enemies triggers **partial local restoration** — small areas of the stage visually heal while eLo is still fighting. This rewards the non-lethal approach and makes the world feel alive.

---

## 12. Enemy Design

All enemies are mutated versions of the world's natural sweetness — overloaded, not evil. Defeating them with the Reversal Launcher restores them to neutral; defeating them with standard weapons neutralises them. Both count as a clear.

Enemy designs will be updated directly from the creator's existing enemy artwork. The categories below define the design language and behaviour logic. Final visual design matches the creator's pre-built assets.

### 12.1 Enemy Design Language

All enemies fall into one of four sweet-food categories. This keeps the world consistent and gives each stage a distinct enemy flavour.

| Category | Examples | Visual Quality | Behaviour Tendency |
|----------|---------|---------------|-------------------|
| Gummy | Gummy bears, gummy worms, gummy apples, gummy rings | Translucent, stretchy, jelly-like | Bouncy, unpredictable movement. Divide or split on hit. |
| Fizzy | Sherbet creatures, soda-charged blobs, effervescent swarms | Fizzing edges, bubble aura, crackling energy | Erratic, fast, swarm in groups. Burst on defeat. |
| Chocolate | Chocolate soldiers, fudge crawlers, cocoa drones | Matte dark brown, cracked or melting surface | Slow, tanky, high damage. Break into smaller chocolate chunks. |
| Sugar Crystal | Crystallised cube enemies, hard-candy shells, spun sugar | Geometric, sharp-edged, glinting | Rigid patrol routes. Shatter into shards on defeat. |

### 12.2 Enemy Roster by Stage

**Note:** Visual designs match creator's existing enemy assets. Entries below define behaviour, not final appearance.

| Enemy | Category | Behaviour | Stage |
|-------|----------|-----------|-------|
| Gummy Soldiers | Gummy | March and shoot sugar blobs. Stretch when hit before snapping back. | Multiple |
| Gummy Apple Bouncers | Gummy | Bounce unpredictably across terrain. Hard to predict, easy to dodge. | Gummy Orchard |
| Gummy Worm Tunnellers | Gummy | Burrow underground, erupt beneath player. | Jungle Caves |
| Fizzy Swarm | Fizzy | Fast-moving groups. Low individual damage, dangerous in numbers. | Multiple |
| Soda Blob | Fizzy | Floats, splits into two smaller blobs when hit. | Tube Waters |
| Sherbet Shooter | Fizzy | Stationary. Fires rapid sherbet bursts in arcs. | Sky Stage |
| Doughnut Spaceships | Fizzy | Aerial bombing runs. Drop Fizzy payload on descent. | Sky, Mothership |
| Caramel Crawler | Chocolate | Slow, sticky. Clings to terrain, slows player on contact. | Desert Dessert |
| Fudge Soldier | Chocolate | Heavy melee, slow walk, high damage hit. | Chocolate Mountains |
| Cookie Drone | Chocolate | Hard outer shell, patrol route. Cracks on hit, breaks on third. | Jungle Caves |
| Sugar Cube Crasher | Sugar Crystal | Multiplies on hit — splits into two smaller cubes. | Mothership |
| Frosted Giant | Sugar Crystal | Slow, large, high damage. Shatters into crystal shards on defeat. | Ice Mountains |
| Crystal Cactus | Sugar Crystal | Stationary, fires crystal spines. | Desert Dessert |
| Marshmallow Mites | Gummy | Tiny swarm enemies, fast and low damage individually. | Multiple |
| Jellyfish Overcharge | Fizzy | Electric fizzy jellyfish. Erratic swim, shock radius on proximity. | Ocean Stage |

### 12.3 Easter Egg Enemies

Hidden enemies that reference retro games and food culture. Finding them is a reward for thorough explorers.

| Enemy | Reference | Stage | Trigger |
|-------|-----------|-------|---------|
| Cactuar | Final Fantasy VIII — the classic 1000 Needles cactus enemy, reimagined as a sugar-crystal cactus | Desert Dessert | Hidden in deep background plane |
| Tomato Slime | Food easter egg — a wobbly tomato-based creature, debates whether it's a fruit or vegetable | Jungle Caves | Found behind a hidden wall |
| Candy Chocobo | Final Fantasy — a cotton candy yellow bird that runs away rather than fighting | Sky Stage | Rare random spawn |
| Gummy Slime | Dragon Quest — classic blue slime shape, gummy texture | Gummy Orchard | Hidden crate trigger |
| Pretzel Knight | Food culture — armoured pretzel soldier, stiff and formal | Desert Dessert | Deep background plane |

### 12.2 Sugarcore Mothership — Final Boss (3 Phases)

**Phase 1 — Aerial Assault:** The Mothership hovers above. Waves of Doughnut Spaceships and Sugar Cube Crashers flood the stage. eLo fights using jetpack and helicopter with Chunk providing ground-level anti-air. K-7 scouts weak points.

**Phase 2 — Interior Breach:** eLo, K-7, and Chunk enter the Mothership. Rotating crystalline cube rooms shift and rearrange. All enemy types appear. Chunk's size-shifting is essential to navigate the rotating geometry. The Reversal Launcher can temporarily stabilise rotating sections.

**Phase 3 — The Core:** The Sugarcore's actual heart — a massive white energy cube. eLo uses the high-energy beam weapon and Reversal Launcher simultaneously. K-7's combat form reveals the vulnerable pulse points. Chunk holds back the energy surge. Defeating this phase does not destroy the Sugarcore — it **redirects** it. The energy dissolves into harmless sweet mist. The planet begins to heal.

---

## 12. Camera System

| Situation | Camera Behaviour |
|-----------|-----------------|
| Standard platforming | Side-scrolling follow, ahead-of-player lead |
| Depth plane shift | Smooth ease transition (0.3–0.5 seconds) to new plane |
| Inside Chunk (large) | Perspective switch — interior camera, exploration mode |
| Boss encounters | Dynamic zoom-out to show boss scale; tightens on vulnerability |
| Stage restoration sequence | Cinematic pull-back to show full stage healing |
| Chunk size shift | Wide angle on grow; tight on shrink |
| K-7 sniff (hidden plane) | Brief camera nudge toward hidden entrance |

---

## 13. Visual Style

### 13.1 Core Aesthetic

True 2.5D — 3D models on a 2D plane. Cartoon-stylised. Flexible visual palette drawing from:

- **Solarpunk** — organic tech, living machinery, warm greens and golds
- **Cyberpunk** — neon circuits, dark-to-bright contrast, data aesthetics (Chunk's interior)
- **Candy / Food textures** — translucent jellies, frosted surfaces, sprinkle details
- **Children's toy design** — plush textures, rounded edges, soft plastics

The corrupted versions of stages deliberately distort these aesthetics — over-saturated candy colours, jittery textures, unstable lighting. Restoration returns them to their natural soft beauty.

### 13.2 Stage Colour System

| Stage | Natural Palette | Corrupted Palette |
|-------|----------------|-------------------|
| Gummy Orchard | Sage, warm green, soft gold | Toxic green, flickering black |
| Tube Waters | Aqua, neon primary, translucent white | Crackling orange, electric overload |
| Sky Stage | Cotton candy pink, lavender, soft white | Storm grey, doughnut-ship red |
| Desert Dessert | Caramel, warm sand, cookie brown | Hardened amber, cracked dark red |
| Ice Cream Mountains | Mint, vanilla white, pastel blue | Ice-sharp cyan, crystallised white |
| Sugarcore Mothership | N/A — always corrupted | Stark white, rotating cube grey, piercing neon blue |

### 13.3 Character Visual Rules

- eLo, K-7, and Chunk have **no eyes** — expression through posture, movement, and colour shifts only
- eLo has a mouth; K-7 and Chunk do not
- All three glow subtly in response to emotional beats and power states
- Enemies are visually *distorted versions* of their natural forms — stretched, over-saturated, jittery

---

## 14. Audio Direction

| Element | Direction |
|---------|-----------|
| Music (Prologue) | Warm, gentle, wonder-filled — book tone |
| Music (Invasion) | Adds tension layer while keeping the warm candy-world base. Never fully dark. |
| Music (Restored Stage) | Returns to prologue warmth — player hears the world healing |
| eLo SFX | Soft, bouncy non-verbal vocalisations — reacts to movement and state |
| K-7 SFX | Balloon squeaks, soft thumps — form shifts have distinct audio signatures |
| Chunk SFX | Low mechanical hum, robotic warmth — garden-lab has ambient plant/water sounds |
| SuperGuu Pistol | Satisfying soft pop — upgrades shift the sound progressively heavier |
| Liquid Guu collect | Wet, satisfying squelch |
| Crystallised Guu collect | Bright crystal chime |
| Crate smash | Wooden crack followed by item-specific reveal sound |
| Enemy defeated | Soft reset chime — not a destruction sound |
| Stage restored | Full musical swell — emotional payoff |

---

## 15. UI & UX

| Element | Design |
|---------|--------|
| HUD | Minimal. Health indicator (soft pulse rings around eLo). Liquid Guu bar. Crystallised Guu count. K-7 form indicator. |
| Companion Status | Small K-7 and Chunk icons showing their state (following / active / special ability ready) |
| Depth Plane Indicator | Subtle layered icon on screen edge — shows current plane and available planes |
| Pause Menu | Organic, grown aesthetic — matches lab visual style |
| World Map | Holographic depth-layered planet map — stages show corrupted or restored state |
| Upgrade Station | Clean, tactile interface — spend Crystallised Guu on visual upgrade trees |
| Dialogue | Soft speech bubbles, no dialogue screens — story flows without interrupting gameplay |
| Death / Respawn | eLo dissolves into light, reforms at last Healing Water checkpoint — no game-over screen |
| Crate Contents Reveal | Brief particle burst with item icon — satisfying, quick, not intrusive |

---

## 16. Easter Eggs & Retro References

| Reference | Trigger | In-World Form |
|-----------|---------|---------------|
| Final Fantasy | Collect all 7 Reflection Phrases in prologue | Tiny Moogle appears in Chunk's lab corner |
| Super Mario | Hidden warp pipe in Tube Waters deep background | Brief 8-bit side room |
| Metal Slug | Hidden tank sprite in Desert Dessert background plane | eLo rides a candy-coloured Metal Slug tank briefly |
| Zool | Speed-run Gummy Orchard under 60 seconds | Zool-style speed trail effect unlocked permanently |
| Sonic | Hidden ring trail in Ice Cream Mountains | Classic ring SFX plays, speed burst activates |
| Street Fighter | Specific input on pause menu in Chunk's lab | Chunk does a Hadouken-style pose |
| Donkey Kong Country | Find the hidden DK barrel in Jungle Caves | K-7 briefly wears a tiny red cap |

Finding all retro easter eggs unlocks a **Retro Gallery** — pixel art versions of eLo, K-7, and Chunk.

---

## 17. Side Content — eLo Racing: Sweetcore Drift

A companion racing game using the same world, characters, and aesthetic. Planned as an in-game unlockable mode initially, with a standalone release on the roadmap.

### 17.1 Core Concept

- All vehicles have **doughnut wheels** — customisable flavours (glazed, sprinkled, jelly-filled, chocolate-frosted)
- Tracks are built directly from the main game's stages — players race through worlds they've already fought through
- Boost pads are candy geysers; hazards include caramel puddles, gummy obstacles, and falling doughnut ship debris

### 17.2 Track List

| Track | Based On | Special Feature |
|-------|----------|-----------------|
| Tube Falls Raceway | Tube Waters | Looping translucent tubes, water splash zones |
| Skybound Circuit | Sky Stage | Floating island gaps, wind gust boosts |
| Gummy Apple Grove Dash | Gummy Orchard | Bush shortcuts, sour patch hazard patches |
| Dessert Desert Drift | Desert Dessert | Sand dunes, caramel trap zones |
| Jungle Caves Run | Jungle Caves | Dark shortcuts, glow-lit turns |
| Ice Cream Mountain Slide | Ice Cream Mountains | Slippery cream banks, marshmallow bumpers |
| Chocolate Rumble | Chocolate Mountains | Rocky cocoa jumps, fudge rivers |
| Mothership Circuit | Sugarcore Mothership | Moving cube walls, energy hazards |

### 17.3 Race Modes

- **Sweetcore Cup** — Story-linked race series, stages unlock with main game progress
- **Gummy Mayhem** — Battle racing with candy power-ups
- **Time Syrup Trials** — Speed-focused challenge mode
- **Local / Online Multiplayer** — 4-player

---

## 18. Post-Sugarcore Expansion Worlds

Unlocked after completing the main game. Foundation for DLC and sequels.

| World | Aesthetic | Emotional Theme | Boss |
|-------|-----------|-----------------|------|
| Bubble Circuit City | Cyberpunk pastel — glass roads, data clouds | Processing emotions | Motherbyte Nougat |
| Marshmallow Skies | Pastel dreamscape, hot cocoa lakes | Rest as resistance | Dreamdrip |
| The Cracked Crayon Wastes | Forgotten creativity, greyscale patches | Reclaiming joy | Sketchy Mallow |
| Neon Echo Fields | Bold pop-art, glitching mirrors | Self-reflection | Mirror Gloop Queen |
| Echo Glades | Memory whispers, sound-wave plants | Healing old stories | Wisp Echo Chorus |
| Echo Syrup Swamp | Deep chocolate, reflective surfaces | Facing distorted self-perception | Mirror Gloop Monarch |
| Gelato Gear Gardens | Melting machines, frozen plants | Reconnecting with wonder | Mint-Vine Warden |

---

## 19. Technical Notes (Unity)

### 19.1 Current Development Status

| Element | Status |
|---------|--------|
| Unity project | Started |
| Stage environments | In progress — Tube Stage built |
| Characters | Modelled and imported |
| Animations | Pending — primary current blocker |
| Gameplay loop | eLo running — base movement implemented |
| Co-op / multiplayer | Not yet started — Phase 2 priority |
| Racing mode | Not yet started — Phase 3 priority |

### 19.2 Priority Build Order

The build follows a **skeleton-first** approach — establish a working traversal prototype with a placeholder object before introducing rigged character models. This keeps iteration fast and avoids blocking on animation completion.

**Step 1 — Skeleton prototype (placeholder object)**
- Get a primitive object (cube or capsule) moving through the stage
- Lock camera angles — establish the side-scrolling camera rig and depth plane camera blends
- Implement basic movement: left/right, jump, land
- Test depth plane shifting with the placeholder
- Confirm stage geometry, collision, and camera feel with zero animation dependency

**Step 2 — Swap in eLo rigged model**
- Replace placeholder object with eLo's rigged model
- Attach animations as they are completed — run, jump, idle first
- Remaining animation slots use placeholder poses until finished
- Core loop (move, collect, shoot) becomes testable as each animation lands

**Step 3 — Full Phase 1 animation completion (all three characters)**
- Complete full Phase 1 animation set per the animation priority chart
- eLo, K-7, and Chunk all moving correctly in the same stage
- Controller switching (DKC2 model) tested with real models

**Step 4 — First full invasion stage**
- Gummy Orchard Corrupted built to completion
- All Phase 1 systems live: movement, shooting, crates, Liquid Guu, enemies
- World restoration visual plays on stage clear

**Step 5 — Systems layer**
- Crystallised Guu and upgrade station
- Randomised crate drop system
- K-7 sniff hidden plane detection
- Chunk size-shift

**Step 6 — Expand stages + prologue**
- Remaining invasion stages built out
- Prologue cutscene/playable mix
- Lab hub fully functional

### 19.3 Key Technical Systems

| System | Implementation Notes |
|--------|---------------------|
| Depth plane shifting | Layered Z-position groups with `DepthPlaneManager`. Camera blend via Cinemachine virtual cameras per plane. |
| Guu resource system | Two separate resource pools — Liquid Guu (ammo counter) and Crystallised Guu (upgrade currency). Scriptable Object driven. |
| Crate randomisation | Weighted random loot table per crate type. Dark crates have trap probability. Seed per stage for consistency on replay. |
| Companion AI | State machine — Follow / Combat Assist / Idle / Active (player controlled). Switch triggers swap of player input receiver. |
| World restoration | Shader-based corruption filter per stage. Restoration triggers progressive shader blend from corrupted to natural palette. |
| Character switching | Single `PlayerController` input receiver reassigned on switch. Non-active characters revert to companion AI state machine. |
| K-7 sniff detection | Trigger volumes on hidden plane entrances. K-7 enters `Sniff` animation state within radius, camera nudge coroutine fires. |
| Chunk size shift | `Transform.localScale` lerp with collider recalculation. Interior access triggers camera blend to inside-Chunk scene camera. |

### 19.4 Platform Considerations

| Platform | Notes |
|----------|-------|
| PC (Steam) | Full feature set, highest visual fidelity |
| PS5 / Xbox Series X | DualSense haptic feedback for depth shifts, weapon fire, and world restoration sequences |
| Nintendo Switch | Docked and handheld modes — performance-scaled assets |
| Mobile | Touch controls with virtual joystick — simplified depth shift; visual LOD reductions |

---

## 20. Development Roadmap

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| Core Loop | Now — Month 2 | eLo animations complete, SuperGuu Pistol live, crates working, first invasion stage playable |
| Companion AI | Month 2–3 | K-7 Tails-style follow, character switching, Chunk basic follow |
| Prologue Arc | Month 3–4 | Cutscenes + light playable stages, full prologue to invasion moment |
| Full Invasion Stages | Month 4–6 | All 8 invasion stages built, world restoration system live |
| Upgrade System | Month 5–6 | Crystallised Guu, upgrade stations, weapon unlocks |
| Co-op | Month 6–8 | 2-player local co-op (eLo + K-7 or Chunk) |
| Polish + Test | Month 7–9 | Full Acts I–IV playable, UX pass, audio integrated |
| Racing Mode | Month 8–10 | First 3 race tracks, doughnut vehicles, basic race loop |
| Launch Prep | Month 10–12 | Platform submissions, trailer, book-game cross-promotion |
| Post-Launch | Month 12+ | Expansion worlds, online multiplayer, animation pitch bible |

---

*"Growth doesn't end — it changes shape."*

---

**Document Owner:** eLo's Planet Development  
**Based On:** eLo Book First Draft, ChatGPT Mind Dump Sessions, Design Sessions  
**Spec Version:** 2.0 — Updated Draft  
**Last Updated:** 2026
