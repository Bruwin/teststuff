# Decisions

Append-only. Once ratified, a record is never edited — a later record supersedes
it. Each record: context, options, decision, consequences.

**Status values:** `OPEN` (needs the human), `RATIFIED`, `SUPERSEDED nnnn`.

The items marked **OPEN** are the ones the human should rule on. Every one has a
recommended default; if nobody answers, the agent proceeds on the default and the
record flips to `RATIFIED (default)` in the session that first relies on it.

---

## D-001 — Build the engine from scratch, with a small dependency allowlist

**Status:** OPEN → default `RATIFIED`
**Context:** "From scratch" could mean zero third-party code, which would cost
6+ months before a triangle appears.
**Options:**
1. Own engine, allowlisted low-level libraries (SDL3, GLM-equivalent of our own,
   Jolt, miniaudio, zstd, doctest).
2. Zero dependencies except the OS API.
**Decision (default):** option 1. "From scratch" means *our* architecture, tick
order, renderer, sim and netcode — not re-implementing a windowing layer.
**Consequences:** fast start; the allowlist is a `MUST` gate (`MOD-05`).

## D-002 — Physics backend: Jolt

**Status:** OPEN → default `RATIFIED`
**Context:** Items on belts, player movement, jams. A hand-written solver costs
months and delivers worse contacts.
**Options:** 1) Jolt (MIT). 2) Own impulse solver. 3) No rigid bodies, kinematic
items only.
**Decision (default):** Jolt, wrapped entirely inside `src/physics/` so it can be
swapped. Our own code adds belt surfaces, jam detection and the fidelity LOD.
**Consequences:** fast, stable physics; determinism is ours only in `sim/`.

## D-003 — Deterministic fixed-point simulation

**Status:** OPEN → default `RATIFIED`
**Context:** Saves, replays and co-op all need bit-identical results across
compilers and CPUs.
**Options:** 1) Q16.16 fixed-point in `sim/`. 2) Doubles with strict rules.
**Decision (default):** option 1.
**Consequences:** `SIM-01` (no floats in `sim/`), slightly less numeric range,
trivially serialisable, hashable.

## D-004 — Physics is a fidelity layer, not authoritative state

**Status:** OPEN → default `RATIFIED`
**Context:** Rigid bodies are not reproducible across platforms and are expensive
at a million items.
**Decision (default):** the lane model in `sim/` is authoritative; physics runs
within 24 m of an observer (cap 4096 bodies) and reports quantised events
(`Slip`, `Jam`, `Topple`, `Scatter`) back into it. `sim_hash()` excludes physics.
**Consequences:** saves are small and portable; jams are still *physical* near the
player and become discrete state when out of sight.

## D-005 — Renderer: OpenGL 4.6 core first, RHI in front

**Status:** OPEN → default `RATIFIED`
**Context:** Vulkan is more future-proof but 3–5× the boilerplate, which matters
when each session is one hour.
**Decision (default):** OpenGL 4.6 (DSA), one `Device` interface, GL isolated in
`rhi/gl`. Vulkan backend revisitable at M15 without touching `render/`.
**Consequences:** fastest path to pixels; some driver-variance risk; no compute
until we add it explicitly.

## D-006 — Platforms: Windows + Linux

**Status:** OPEN → default `RATIFIED`
**Context:** macOS adds Metal/GL compatibility and CI cost.
**Decision (default):** Windows 10+ and Linux x86-64; macOS deferred.
**Consequences:** SDL3 keeps the door open; CI has two presets.

## D-007 — World model: infinite 2D grid with stacked platforms

**Status:** OPEN → default `RATIFIED`
**Context:** Factorio-like infinite plane vs Satisfactory-like finite 3D terrain.
**Decision (default):** infinite 2D plane, 1 m placement grid, up to 4 stacked
platform levels (mezzanines) with explicit ramps — 3D enough for interesting
layout, 2D enough for tractable pathing and networking.
**Consequences:** no terrain generation in v0.1; world is flat with zones/biomes
painted as data later.

## D-008 — Scale target: 100 k machines, 1 M items

**Status:** OPEN → default `RATIFIED`
**Context:** The genre's selling point is sprawl; under-targeting kills the fantasy,
over-targeting kills the frame budget.
**Decision (default):** budgets in `PLAN.md` §5. Bench gates enforce them.
**Consequences:** data-oriented sim from day one; no per-item objects with
virtual functions (`PERF-04`).

## D-009 — Multiplayer is designed in, shipped after v0.1

**Status:** OPEN → default `RATIFIED`
**Context:** Co-op is expected but netcode is the highest-risk subsystem.
**Decision (default):** the sim is tick-deterministic and snapshot-serialisable
from M6, but the protocol lands at M14, after the single-player game is fun.
**Consequences:** no rewrite later; v0.1 ships single-player/co-op-LAN-disabled.

## D-010 — No monetisation, MIT licence for the engine, content CC-BY

**Status:** OPEN → default `RATIFIED`
**Context:** The repository will host many contributors.
**Decision (default):** MIT for code, CC-BY-4.0 for art/audio, DCO sign-off.
**Consequences:** no CLA friction; third-party licences checked in `NOTICE`.

---

## Ratified

*(nothing yet — records flip here as work begins)*
