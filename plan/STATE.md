# Project state

> Living document. Overwritten every session. If it disagrees with the code, the
> code wins — then fix this file in the same PR (`AGT-27`).
> Last updated: 2026-11-07, session 002 (M1 platform, clock, log routing), tagged
> `v0.1.0-m1`.

## Phase

**M1 complete. Next is M2 (RHI skeleton: device, swap chain, clear).**

The game repository seed lives in `game/` in this workspace; its contents become
the repository root on GitHub, with `plan/` alongside. The voxel asset generator
stays where it is and will feed `tools/cook_assets` from M4.

## Releases

| Tag | Milestone | Points at | Contents |
|---|---|---|---|
| `v0.1.0-m1` | M1 | `fabee5c` (first commit) | engine seed at version `0.1.0-m1`: clock, platform, log sinks, 31 tests, gates, assets |

The tag is annotated and local; nothing is pushed yet. Two rules that keep it
meaningful: `kVersion` in `src/core/version.h` and the tag move together, and a
tag is never moved after it is pushed. If a tagged state turns out to be broken,
publish a new tag rather than retagging.

## Green

```
cd game && bash tools/verify.sh
  conventions          24 files, 0 findings
  layering             16 files, 0 findings
  gate self-test        4/4 ok (planted violations rejected)
  build (g++ fallback) 31 test cases, 0 failures
  verify: OK
```

```
cd tools && python3 build.py      -> 36 assets, 109636 triangles, 0 problems
python3 validate.py               -> 0 problems
```

## Red

none

## Now

- Nothing in flight. Working tree uncommitted (no game remote exists yet).

## Next

1. **M2**: `src/rhi/` device + swap chain + clear; `platform::Window::present()`
   becomes a real swap. Acceptance: cleared window at 60 fps, `verify.sh` green
   with the headless RHI stub.
2. Create the GitHub repository: copy `game/` to the root, keep `plan/`, add the
   real handles to `CODEOWNERS`, protect `main`, enable CI.
3. Replace `tests/harness.h` with doctest once vendoring lands (`MOD-05` record
   needed first); the macros already match doctest's shape.

## Blocked

- Decisions D-001 … D-009 are on defaults; nothing is blocked yet. D-006 (macOS)
  becomes blocking at the first RHI PR if macOS is wanted.

## Module map (use this to decide what to read)

| Module | Entry header | Owner role | Status |
|---|---|---|---|
| `core` | `src/core/log.h`, `fixed.h`, `hash.h`, `version.h`, `fixed_step.h` | `core` | M1 done |
| `sim` | `src/sim/world.h` | `sim` | M0 stub (clock + hash) |
| `platform` | `src/platform/platform.h` | `core` | M1 done (SDL3 + headless stub) |
| `rhi` | `src/rhi/device.h` | `gfx` | not started |
| `render` | `src/render/render.h` | `gfx` | not started |
| `physics` | `src/physics/world.h` | `phys` | not started |
| `game` | `src/game/game.h` | `game` | not started |
| `ui` | `src/ui/ui.h` | `ui` | not started |
| `net` | `src/net/net.h` | `net` | not started |
| `app` | `src/app/main.cpp` | `arch` | M1: 3 modes (`--ticks`, `--frames`, `--window`) |

## Facts worth not re-deriving

- Sim tick **30 Hz** (33,333,333 ns); physics **60 Hz**; snapshots **30 Hz**;
  interpolation **2 ticks**; max **4** catch-up ticks per frame.
- The sim clock is a **fixed-step accumulator over integer nanoseconds**: time is
  never accumulated into the sim clock ratio (Q16.16 drift), and a stall longer
  than 250 ms is dropped rather than replayed.
- `sim/` is fixed-point Q16.16, includes `core/` only, and may not contain floats.
- Item fidelity radius **24 m**, active body cap **4096** (physics layer only).
- Chunk size **32 × 32 m**; belt lattice **1/16 m**; placement grid **1 m**.
- Physics results never enter `sim_hash()` (`D-004`).
- `platform/` has two backends: `window_sdl.cpp` when CMake finds SDL3,
  `window_stub.cpp` otherwise (`FCT_HAVE_SDL3`). Both must keep compiling.
- Logging goes through `core/log.h` only; `log_set_sink` is how tests and the
  future in-game console capture output.
- Verification is `game/tools/verify.sh`; CI runs the same script on 3 jobs.

## Session log index

| # | Date | Milestone | Result |
|---|---|---|---|
| 000 | 2026-11-07 | planning | plan, style guide, protocol, decisions drafted |
| 001 | 2026-11-07 | M0 | repository seed, gates, tests; `verify: OK` |
| 002 | 2026-11-07 | M1 | platform + fixed-step clock + log sinks; 31 tests green |

## Handoff — (template, copy for each session)

```
Now:      <one sentence>
Green:    <command + summary line>
Red:      <failing command + first error, or "none">
Next:     <single next issue with number>
Blocked:  <decisions needed, else "none">
Files:    <≤ 10 files to open first>
```
