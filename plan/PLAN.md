# Factory Engine — master plan

**Project:** a custom C++ engine and heavy automation game: sprawling factories,
real rigid-body physics, deep progression, co-op.

**This document is the contract.** It is written to survive the agent losing its
entire context overnight. If reality disagrees with a number in here, the number
changes through a decision record (see `DECISIONS.md`) — not silently in code.

Companion files, read in this order:

| File | Purpose | Changes |
|---|---|---|
| `STATE.md` | where the project is right now, what is next | every session, overwritten |
| `DECISIONS.md` | ratified architectural choices, with reasons | append-only |
| `STYLE_GUIDE.md` | numbered C++ rules, cited in reviews | human sign-off only |
| `AGENT_PROTOCOL.md` | how agents branch, commit, review, hand off | human sign-off only |
| `PLAN.md` | this file: vision, architecture, milestones | via decision record |

### An honest statement about "no mistakes"

Nobody — human or model — writes 300 hours of engine code without defects. What
this plan does instead is make mistakes *cheap*: small commits, one-command
verification, golden-hash determinism tests, per-module budgets, and a review
process that cites rule IDs. The goal is that no defect survives a session
boundary, not that none is ever written. Any agent that claims otherwise about
its own output is lying to you; treat such a claim as a review red flag
(`AGT-21`).

---

## 1. Vision

You build a factory that starts as one belt into one furnace and ends as a
continent-spanning organism of trains, pipes, power grids and robots. It is easy
to learn because every machine has one obvious input and one obvious output. It
is hard to master because throughput, power, heat, fluid pressure, layout and
item physics all interact, and the last 5 % of efficiency takes real design.

### Design pillars

1. **The factory is a machine you debug.** Every blockage is visible, named and
   traceable. Nothing stalls silently.
2. **Physics is a gameplay system, not a decoration.** Oversized parts on
   undersized belts, crowded merges, and dumped bulk loads cause real jams.
3. **Always a next unlock.** The tech tree never runs dry before the world does.
4. **Deterministic truth.** The same save and the same inputs produce the same
   world, on any machine, forever.
5. **Legible at every scale.** 12 machines or 120 000: the map reads the same.

### What "heavy automation" means here

- 3 belt tiers (1/16 m lattice, 2/4/8 items per second per lane), pipes, pumps,
  fluid and gas networks, power generation and distribution, heat.
- ~60 machine types across 8 categories, 4 research pack types, ~120 tech nodes.
- Modules and beacons, overclocking, byproducts, quality/durability, trains and
  logistics drones (post-v0.3).
- Co-op for up to 8 players, server-authoritative, no rollback of factory state.

---

## 2. Technical constitution

Twelve rules that outrank every other consideration. Breaking one requires a
decision record and human approval.

1. **One tick order, never reordered.** `sim` runs game rules in a fixed
   sequence; anything that changes it changes every save.
2. **`sim/` contains no floating point.** Fixed-point `Q16.16` only; enforced by
   `tools/lint_layers.py` + clang-tidy.
3. **Determinism is tested, not assumed.** Golden world-hash tests run on every
   push against two compilers and two optimisation levels.
4. **The renderer cannot see game state.** It draws what it is handed.
5. **No allocation in the tick.** All tick-time memory comes from pre-sized
   arenas and pools; growth happens between ticks or at load.
6. **No dependency enters without a decision record.** Version pinned by commit.
7. **Every public header is a contract.** Changing one requires a review by a
   different agent and, for `sim/` and `core/`, a human.
8. **Numbers are named.** Magic numbers become `constexpr` with units in the name.
9. **Fail loud in development, degrade in release.** `FCT_ASSERT` in debug,
   logged error + safe default in release; never silent corruption.
10. **Measure, then optimise.** No performance change without a bench delta in
    the PR description.
11. **One concern per commit.** A commit that formats and refactors and fixes is
    rejected (`AGT-14`).
12. **Docs move with code.** A PR that changes behaviour updates `STATE.md`; a PR
    that changes a contract updates `PLAN.md`/`DECISIONS.md`.

---

## 3. Architecture and module law

Strict layering. `tools/lint_layers.py` parses includes and fails CI on any
upward or sideways-forbidden edge.

```
            app            (main loop, game states, save, net glue)
          /  |  \
      game  net  ui       (build mode, machines, tech, players, IMGUI, HUD)
        \   |   /
         sim | render      (deterministic rules) (scene, culling, materials)
           \ |  /
        physics | rhi      (Jolt wrapper)       (device API; gl backend)
              \ | /
            platform       (window, input, files, time, threads)
                 |
               core        (math, fixed-point, containers, log, hash, alloc)
```

**Allowed edges** (the only ones):

| From | May include |
|---|---|
| `core` | standard library only |
| `platform` | `core`, SDL3, miniaudio |
| `rhi` | `core` |
| `render` | `core`, `rhi` |
| `physics` | `core`, Jolt |
| `sim` | `core` **only** |
| `game` | `core`, `sim`, `physics`, `render`, `rhi` |
| `ui` | `core`, `render`, `rhi`, `game` (read-only handles) |
| `net` | `core`, `sim` (serialisation only) |
| `app` | everything |

Rationale: `sim` must be testable in a headless harness with zero engine
dependencies, and `render` must never depend on game types — that is what makes
both the determinism gate and the golden-frame tests possible.

### Repository layout

The repository root is the game. The art set is a sub-project: it has its own
tooling, its own README and its own CI gate, and the engine never links against
it.

```
<repo root>       <- the game
  CMakeLists.txt  CMakePresets.json
  src/core/       math, fixed, containers, log, hash, arena, assert
  src/platform/   window, input, filesystem, timing, threads, audio device
  src/rhi/        device.h (API), gl/ (OpenGL 4.6 backend)
  src/render/     scene, camera, culling, chunk batcher, debug draw, font
  src/physics/    world, bodies, belts, jam detection
  src/sim/        world, grid, lanes, machines, power, fluids, recipes, tick order
  src/game/       player, build mode, machines registry, tech tree, alerts
  src/ui/         immediate-mode widgets, panels, HUD
  src/net/        transport, protocol, snapshots, replication
  src/app/        main, states, save/load, settings
  tools/          the gate: verify.sh, lint_layers, lint_conventions, bench, replay,
                  and (from M4) cook_assets
  tests/          unit/, golden/, fuzz/, bench/, manual/ (hand-run harnesses)
  data/           recipes, machines, tech, balance (JSON + schema)
  assets/         SUB-PROJECT: glb/, obj/, preview/, rigs/, manifest.json and its
                  own tools/ (the voxel generator). Cooked output lands in data/.
  plan/           plan, style guide, agent protocol, decisions, state, sessions
```

Target sizes, chosen so a single agent can hold a file in context:
**≤ 400 lines per file, ≤ 60 lines per function, one public type per header.**

---

## 4. Subsystem design

### 4.1 Core (`src/core`)

- `fct::f32/f64/i32/u32/u64`, `Vec2/Vec3`, `Mat3/Mat4`, `Aabb`, `Ray`, quaternion.
- Fixed-point `Fix` (Q16.16): `add/sub/mul/div`, `from_f32`, `to_f32`,
  `from_grid(i32,int)` — the only numeric type allowed in `sim/`.
- Deterministic hash: `xxh3`-style 64-bit, seeded per subsystem; **never**
  `std::hash` for anything that touches sim state.
- Arena allocator (`Arena`, bump + reset), pool allocator for fixed-size nodes.
- Logging: categories, levels, ring buffer, structured fields; no `printf`.
- `FCT_ASSERT` / `FCT_VERIFY` with file:line, compiled out of release.
- Containers: `Span<T>`, `Slice<T>`, `StaticVector<N>`, `SmallMap<K,V>`; STL is
  allowed in tools and non-hot paths only.

### 4.2 Platform (`src/platform`)

SDL3 for window, input, gamepad, clipboard, message boxes. File IO with explicit
root sandbox (saves, mods, logs). Monotonic clock, sleep, thread pool (only for
asset load, audio decode, and later sim parallelism — never inside a tick).

### 4.3 RHI + renderer

OpenGL 4.6 core with DSA, one `Device` interface (buffers, textures, pipelines,
fences). No GL symbols outside `rhi/gl/`. Vulkan becomes possible at M14 without
touching `render/`.

Pipeline: forward+ (clustered lights, 1 024 clusters), 8×8 shadow atlas with
CSM, one material family (vertex colour, no textures), instanced chunk batches.
Chunks are **32 × 32 m**: each holds merged static geometry, split by material
colour bucket, with an AABB and a per-chunk instance list. Culling: frustum →
octree → per-chunk. Draw budget enforced by the chunk sorter.

Statics bake into chunk meshes (walls, foundations, machine bodies); items and
moving parts are instanced (`glDrawElementsInstanced`), which is what makes a
million items survivable.

### 4.4 Physics (`src/physics`)

**Jolt** (MIT) as the rigid-body backend: player capsule, loose items, vehicles,
debris. Our layer adds:

- **Belt surfaces** as kinematic box bodies moving at belt velocity; items are
  carried by friction, not teleported.
- **Item shapes** from the cooked asset AABB (boxes, capsules for barrels, convex
  hulls for crates ≤ 32 verts).
- **Jam detection** with three independent signals, any of which raises a jam:
  1. contact impulse against flow > `kJamImpulse` for > 100 ms;
  2. item speed < 10 % of surface speed for > 150 ms with a downstream blocker;
  3. lane-level deadlock: occupancy graph contains a cycle with no progress for
     400 ms (this catches jams the bodies cannot see).
- **Hybrid fidelity**: only items within 24 m of an observer get full rigid
  bodies (cap 4 096 active). Everything else advances as deterministic lane slots.
  The lane model is authoritative; physics is a fidelity layer whose outputs are
  quantised back into it as events (`Slip`, `Jam`, `Topple`, `Scatter`). This is
  the single most important performance decision in the plan.
- Determinism scope: **physics results are not part of the replay hash.** Saves
  store lane state plus jam flags; replays force `physics.deterministic = false`
  and compare lane hashes only. Documented in `DECISIONS.md` D-004.

### 4.5 Sim (`src/sim`) — the heart

Deterministic, dependency-free, fixed-point.

- **Grid**: 1 m cells for placement, 1/16 m lattice for belt items. Infinite 2D.
- **Tick order** (frozen, versioned as `kTickOrderVersion`):
  1. input intents apply (build/demolish/connect)
  2. research progress
  3. power generation → distribution → brownout resolution
  4. fluid/gas network solve (iterative, bounded 8 passes)
  5. machines: consume → craft → produce (recipe state machines)
  6. logistics: belts, splitters, mergers, inserters (lane slots advance)
  7. trains/drones (post-v0.3)
  8. alerts, statistics, chunk dirty flags
- **Tick rate 30 Hz**, fixed step, catch-up cap 4 ticks per frame.
- **Lane slots**: each belt tile has 2 lanes × 4 slots of 1/4 tile; items occupy
  a slot with an id, a shape class and a progress fraction. Moves are integer
  increments — no floats, no drift, cheap to serialise.
- **Power**: per-network production/consumption, satisfaction ratio applied to
  machine speed; accumulators as a two-pass update.
- **Fluids**: pressure/volume per segment, 8-pass relaxation on junctions,
  documented as approximate but deterministic.
- **Snapshot**: `sim_hash()` walks chunks and entities in index order (never
  pointer order) — used by golden tests and by net baselines.

### 4.6 Game (`src/game`)

Machines registry (data-driven from `data/machines/*.json`), build mode with
ghosts and drag-place, blueprints (copy/paste as compressed binary), tech tree,
objectives/onboarding, alert manager, statistics.

### 4.7 UI (`src/ui`)

Own immediate-mode widget set (~1 500 lines) on top of `render::DebugDraw` and a
bitmap font atlas. Dear ImGui is a **debug-only** developer tool compiled behind
`FCT_DEBUG_UI`; it never ships in the player HUD (`STYLE-UI-03`).

### 4.8 Net (`src/net`)

- UDP, own reliability layer: 8-byte header, sequence + ack bitfield, fragment
  reassembly (MTU 1 200), CRC32C, replay window 1 024.
- 30 Hz snapshots, delta against a 32-baseline ring, quantised fields, RLE for
  belt lanes; target ≤ 30 KB/s per client at 256 visible entities.
- Server authoritative. Client predicts only the avatar (rollback over 8 ticks).
  Factory state is never predicted — it is interpolated 2 ticks behind.
- Protocol version hash includes `kTickOrderVersion` + data schema hash; mismatch
  refuses the connection with a readable message.
- Headless soak harness in `tests/net/`: 8 bots, simulated 120 ms RTT, 2 % loss,
  30 min, asserts no divergence between client shadow-sim and server.

### 4.9 Save / load

Binary, chunked, versioned (magic `FCTW`, version, tick-order version, data
schema hash, chunk index, zstd-compressed payloads). Atomic write
(`.tmp` → fsync → rename). Migration chain `v1→v2→…`; a save that cannot migrate
loads read-only with a warning. Autosave every 5 min to a separate slot.

### 4.10 Data and content

All gameplay numbers in JSON with a JSON-Schema checker run by CI
(`tools/datacheck`). Balance spreadsheets in `data/balance/*.csv` drive a headless
throughput bench that prints per-tier production curves; balance changes must
include the bench table in the PR.

### 4.11 Asset pipeline

`tools/cook_assets` reads the existing voxel-generator GLBs and writes
`.fmesh` blobs: chunked vertex data (pos/normal/colour), cooked collision shapes,
LOD chain (3 levels by voxel decimation), and `assets.idx` (path, AABB, triangle
count, hash). Runtime never parses glTF; startup reads one index file. Cooker is
deterministic: same inputs → byte-identical output (checked in CI).

---

## 5. Performance budgets

Measured by `tools/bench` on the CI reference runner; recorded per commit.

| Scenario | Budget |
|---|---|
| Sim tick, 100 k machines + 1 M items | ≤ 8.0 ms single core |
| Render frame, 1440p, 5 k chunks, 20 k item instances | ≤ 11.0 ms |
| Physics step, 4 096 active bodies | ≤ 4.0 ms |
| Frame total at target scene | ≤ 16.6 ms (60 fps) |
| RAM at target scene | ≤ 2.0 GB |
| Load 100 k-machine save | ≤ 5 s |
| Net per client, 256 visible entities | ≤ 30 KB/s, ≤ 60 ms p95 tick-to-photon |
| Cook all assets | ≤ 60 s |
| Full CI (build + tests + bench) | ≤ 12 min |

A regression > 20 % over the recorded baseline fails the PR unless a decision
record accepts the trade.

---

## 6. Testing and verification

1. **Unit** (doctest): fixed-point math, lane movement, power solve, fluid pass,
   snapshot hashing, delta compression, RLE, fragment reassembly.
2. **Golden determinism**: `tests/golden/*.scn` (seed + scripted intents) run 900
   ticks; world hash must match `*.hash` exactly. Matrix: clang-18 `-O0`,
   clang-18 `-O2`, gcc-13 `-O2`. Any diff is a stop-the-line failure.
3. **Replay regression**: recorded session input logs replayed for 10 minutes,
   hashes compared; covers ticket-scale integration.
4. **Fuzz** (libFuzzer): save loader, packet decoder, blueprint decoder. Corpus in
   repo, 60 s per target in CI.
5. **Net soak**: 8 headless clients, 30 simulated minutes, asserts convergence.
6. **Golden frames**: 8 reference camera poses rendered at 640×360 via llvmpipe,
   perceptual diff (≤ 2 % pixels) to catch renderer regressions without a GPU.
7. **Bench gates**: table above, printed into the PR.
8. **One command**: `./tools/verify.sh` runs format check → layers → conventions →
   build (all presets) → tests → goldens → bench; it is the only definition of
   "green" that matters.

---

## 7. Progression design

### Machine parts and unlocks

Parts are the *only* way power grows: a machine has sockets; unlocking a part
makes it craftable; crafting consumes research packs and materials. 8 categories
× ~7 tiers. Parts include faster belts, larger furnaces, better inserters,
modules (speed/productivity/efficiency), beacons, pumps, turbines.

### Skill tree

- DAG, 5 tiers, ~120 nodes, 4 pack types (logistics / production / energy /
  physics). Each node is data: `id, tier, cost{pack:count}, requires[], unlocks[]`.
- Mastery layer: nodes that only change *numbers* (module slots, overclock caps,
  belt saturation efficiency), so the tree keeps giving after the machine set is
  complete.
- Onboarding: the first 12 nodes are linear and hand-authored; objectives teach
  ratios, then the tree opens.

### Difficulty curve

| Phase | Hours | Player learns |
|---|---|---|
| Bootstrap | 0–2 | one belt, one furnace, hand-feeding |
| Automation | 2–6 | ratios, splitters, power |
| Logistics | 6–15 | merges, buffers, trains, jams |
| Scaling | 15–30 | modules, beacons, fluid balance |
| Mastery | 30+ | perfect ratios, throughput walls, city blocks |

---

## 8. Milestones

Hours are *agent-hours* (1-hour sessions). Each milestone ends with a demo and a
green `verify.sh`.

| ID | Milestone | Hrs | Acceptance |
|---|---|---|---|
| M0 | Foundations: repo, CMake presets, CI, style/lint tooling, docs | 8 | CI green on empty engine; lint layers detects a planted violation |
| M1 | Frame loop: SDL3 window, fixed-step clock, log, assert | 4 | 60 fps empty frame; clock drift < 1 ms/min |
| M2 | Core: math, fixed-point, hash, arena, containers | 10 | unit tests ≥ 90 % of `core`; fixed-point properties fuzz-tested |
| M3 | RHI + triangle + debug draw | 8 | textured-free triangle, debug lines, capture screenshot |
| M4 | Asset cooker + chunk renderer | 16 | 5 k chunk scene at budget; cooker byte-identical rerun |
| M5 | Camera, player capsule, Jolt integration | 12 | walk/jump on a 100 k-triangle floor at 60 fps |
| M6 | Sim core: grid, lanes, belts, items, tick order v1 | 24 | 1 M items on 10 k belts update in ≤ 8 ms; golden hash stable |
| M7 | Machines, recipes, inserter, power | 28 | smelter→assembler line runs 30 min with no drift |
| M8 | Fluids and gases | 18 | pipe network benchmarks; pressure visualisation |
| M9 | Physics fidelity layer + jams | 20 | three scripted jam scenarios reproduce, alert fires, unjam works |
| M10 | Build mode UI, ghosts, drag place, blueprints | 22 | place/demolish 10 k entities without dropping below 60 fps |
| M11 | Save/load, migrations, autosave | 12 | 100 k save loads in ≤ 5 s; fuzz finds no crash in 60 s |
| M12 | Tech tree, parts, objectives | 20 | full first playthrough script completes headlessly |
| M13 | Audio, polish, settings, accessibility | 14 | audio buses, sliders, remap, colour-blind palettes |
| M14 | Co-op netcode | 30 | 8 players, 30 min soak, no divergence |
| M15 | Optimisation: culling, batching, multithreaded render prep | 20 | 2× chunk count at same frame time |
| M16 | Content scale + modding API | 24 | 60 machines, 120 tech nodes, one external mod loads |

**v0.1 demo = M0–M13.** Estimated 220 hours ≈ 220 sessions ≈ 5–6 weeks at 8 h/day
of agent time, assuming the review overhead in `AGENT_PROTOCOL.md` holds.

---

## 9. Session operating model (1 hour)

Every session runs the same loop. It is mandatory; deviation is `AGT-05`.

| Minutes | Phase | Output |
|---|---|---|
| 0–8 | Orient: read `STATE.md`, the open issue, the files in scope only | a 5-line plan in the session log |
| 8–40 | Build: one issue, one concern, commits ≤ 200 lines | working tree progress |
| 40–52 | Verify: `verify.sh`, fix, re-run affected checks only | green or documented red |
| 52–58 | Record: append session log, update `STATE.md`, `DECISIONS.md` if needed | handoff block |
| 58–60 | Commit + push branch, open/update PR | PR link in `STATE.md` |

Rules that make hours-of-autonomy safe:

- Never start work that cannot plausibly reach green inside the session.
- If a session must end red, the branch is marked `WIP` and `STATE.md` starts with
  `⚠ BROKEN:` plus the exact failing command and its output.
- A session may take *one* new issue beyond its plan, never two.

---

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Context loss between sessions | wrong assumptions, duplicated work | `STATE.md` contract, small files, session logs, index of module owners |
| Determinism drift on new compilers | broken saves, broken co-op | fixed-point sim, 3-config golden matrix, hash includes data schema |
| Physics cost at scale | frame time blowout | fidelity layer with 24 m radius and 4 096 body cap |
| Scope creep (trains, drones, 3D) | never ships | milestones are fixed; new features need a decision record |
| Agent rewrites others' code | merge conflicts, lost work | ownership labels, `AGT-09`, PR size limits |
| Netcode complexity | months lost | co-op after v0.1 is playable; protocol frozen at v1 with version hash |
| Art pipeline drift | broken assets | cooker determinism test, asset hash in manifest |

---

## 11. Definition of done (v0.1)

- 60 fps at 1440p with 20 k placed machines and 100 k items on the reference scene.
- Deterministic: 10-minute replay reproduces the world hash on 3 build configs.
- 60 machines, 120 tech nodes, 3 belt tiers, power and one fluid network.
- Save/load with migration, autosave, and a 100 k-machine save under 5 s.
- Three physics jam types occur naturally, all detectable and unjammable.
- Co-op disabled but protocol skeleton present and soak-tested with bots.
- `verify.sh` green on Windows and Linux from a clean clone in under 12 minutes.
