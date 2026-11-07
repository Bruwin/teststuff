# Project state

> Living document. Overwritten every session. If it disagrees with the code, the
> code wins -- then fix this file in the same PR (`AGT-27`).
> Last updated: 2026-11-07, session 003 (repository restructured around the game),
> tagged `v0.1.1-m1`.

## Phase

**M1 complete, layout restructured. Next is M2 (RHI skeleton: device, swap chain,
clear).**

The repository root is the game: `src/`, `tests/`, `tools/` (the gate), `.github/`.
The voxel art set is a sub-project under `assets/` with its own tooling, README and
CI job. `plan/` sits alongside as documentation.

## Green

```
cd <repo root>
bash tools/verify.sh
  conventions          26 files, 0 findings
  layering             17 files, 0 findings
  gate self-test        4/4 ok (planted violations rejected)
  build (g++ fallback) 31 test cases, 0 failures
  verify: OK

python3 assets/tools/validate.py   -> 36 assets, 109636 triangles, 0 problems
g++ -Isrc tests/manual/merge_station_demo.cpp && ./merge_demo -> all checks passed
```

## Red

none

## Now

- Nothing in flight.

## Next

1. **M2**: `src/rhi/` device + swap chain + clear; `platform::Window::present()`
   becomes a real swap. Acceptance: cleared window at 60 fps, `verify.sh` green
   with a headless RHI stub.
2. Wire `src/game/merge_station.h` into the sim's machine step (it is written and
   harness-verified but nothing calls it yet).
3. Replace `tests/harness.h` with doctest once vendoring lands (`MOD-05` record
   needed first); the macros already match doctest's shape.

## Blocked

- Decisions D-001 ... D-009 are on defaults; nothing is blocked yet. D-006 (macOS)
  becomes blocking at the first RHI PR if macOS is wanted.

## Module map (use this to decide what to read)

| Module | Entry header | Owner role | Status |
|---|---|---|---|
| `core` | `src/core/log.h`, `fixed.h`, `hash.h`, `version.h`, `fixed_step.h` | `core` | M1 done |
| `sim` | `src/sim/world.h` | `sim` | M0 stub (clock + hash) |
| `platform` | `src/platform/platform.h` | `core` | M1 done (SDL3 + headless stub) |
| `game` | `src/game/merge_station.h` | `game` | merge station controller (harness only, not wired) |
| `rhi` | `src/rhi/device.h` | `gfx` | not started |
| `render` | `src/render/render.h` | `gfx` | not started |
| `physics` | `src/physics/world.h` | `phys` | not started |
| `ui` | `src/ui/ui.h` | `ui` | not started |
| `net` | `src/net/net.h` | `net` | not started |
| `app` | `src/app/main.cpp` | `arch` | M1: `--ticks`, `--frames`, `--window` |

## Facts worth not re-deriving

- Sim tick **30 Hz** (33,333,333 ns); physics **60 Hz**; snapshots **30 Hz**;
  interpolation **2 ticks**; max **4** catch-up ticks per frame.
- Time is a **fixed-step accumulator over integer nanoseconds**; a stall over
  250 ms is dropped, not replayed.
- `sim/` is fixed-point Q16.16, includes `core/` only, and may not contain floats.
- Item fidelity radius **24 m**, active body cap **4096** (physics layer only).
- Chunk size **32 x 32 m**; belt lattice **1/16 m**; placement grid **1 m**.
- Physics results never enter `sim_hash()` (`D-004`).
- `platform/` has two backends: `window_sdl.cpp` when CMake finds SDL3,
  `window_stub.cpp` otherwise (`FCT_HAVE_SDL3`). Both must keep compiling.
- **The repository is the game.** `assets/` is a sub-project with its own gate
  (`python3 assets/tools/validate.py`) and its own CI job; the engine never links
  against asset tooling.
- Verification is `tools/verify.sh` at the root; CI runs the same script on 3 jobs
  plus an assets job. `tests/manual/` is exempt from `LAY-06` only.
- CI workflows only run from the root `.github/workflows/` -- which is why the
  restructure mattered.

## Session log index

| # | Date | Milestone | Result |
|---|---|---|---|
| 000 | 2026-11-07 | planning | plan, style guide, protocol, decisions drafted |
| 001 | 2026-11-07 | M0 | repository seed, gates, tests; `verify: OK` |
| 002 | 2026-11-07 | M1 | platform + fixed-step clock + log sinks; 31 tests green |
| 003 | 2026-11-07 | restructure | game at the root, assets sub-project, CI live |

## Handoff -- (template, copy for each session)

```
Now:      <one sentence>
Green:    <command + summary line>
Red:      <failing command + first error, or "none">
Next:     <single next issue with number>
Blocked:  <decisions needed, else "none">
Files:    <<= 10 files to open first>
```
