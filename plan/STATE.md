# Project state

> Living document. Overwritten every session. If it disagrees with the code, the
> code wins -- then fix this file in the same PR (`AGT-27`).
> Last updated: 2026-11-07, session 003 (repository restructured around the game),
> tagged `v0.1.1-m1`.

## Phase

**M3 complete: the triangle and debug lines draw through a command buffer, a
reference rasteriser and an OpenGL 4.6 backend driven by an injected entry point
table. Next is M4 (scene graph, chunk batcher, camera).**

The repository root is the game: `src/`, `tests/`, `tools/` (the gate), `.github/`.
The voxel art set is a sub-project under `assets/` with its own tooling, README and
CI job. `plan/` sits alongside as documentation.

## Green

```
cd <repo root>
bash tools/verify.sh
  conventions          53 files, 0 findings
  layering             41 files, 0 findings
  gate self-test        4/4 ok (planted violations rejected)
  build (g++ fallback) 55 test cases, 0 failures
  verify: OK

python3 assets/tools/validate.py   -> 36 assets, 109636 triangles, 0 problems
g++ -Isrc tests/manual/merge_station_demo.cpp && ./merge_demo -> all checks passed
```

## Red

none

## Now

- Nothing in flight.

## Next

1. **M4**: scene graph, chunk batcher and a real camera, so the triangle becomes
   world geometry instead of a clip-space constant.
2. First CI run on a machine with SDL3: `src/platform/gl_context_sdl.cpp` is the
   only file in the tree that has never been compiled. A failure there is isolated
   to that one file.
3. Wire `src/game/merge_station.h` into the sim's machine step (it is written and
   harness-verified but nothing calls it yet).
4. Replace `tests/harness.h` with doctest once vendoring lands (`MOD-05` record
   needed first); the macros already match doctest's shape.

## Blocked

- Decisions D-001 ... D-009 are on defaults; nothing is blocked yet. D-006 (macOS)
  becomes blocking at the first RHI PR if macOS is wanted.

## Module map (use this to decide what to read)

| Module | Entry header | Owner role | Status |
|---|---|---|---|
| `core` | `src/core/log.h`, `fixed.h`, `hash.h`, `version.h`, `fixed_step.h` | `core` | M1 done |
| `sim` | `src/sim/world.h` | `sim` | M0 stub (clock + hash) |
| `platform` | `src/platform/platform.h` | `core` | window, input, time, GL context; SDL3 or stub |
| `game` | `src/game/merge_station.h` | `game` | merge station controller (harness only, not wired) |
| `rhi` | `src/rhi/rhi.h` | `gfx` | device, swap chain, command buffer, capture, GL backend |
| `render` | `src/render/render.h` | `gfx` | reference rasteriser, framebuffer, PPM writer; scene graph at M4 |
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
- Swap chain bookkeeping (size checks, clear/present counts, frame digest) lives in
  `src/rhi/swap_chain_state.h` and every backend drives it, so loop behaviour is
  testable with no GPU. `rhi::create_device` never returns null: a machine without
  GL gets the headless backend and a log line saying so.
- Drawing is a `rhi::CommandBuffer` replayed by a backend. The software
  `render::Rasterizer` is the reference executor and the pixel tests' oracle; it is
  not a shipping renderer. No depth buffer and no frustum clipping until the
  milestone that can test them.
- The GL backend is driven by an injected `fct::gl::GlApi` table, so it compiles
  and is unit-tested with no driver; a fake table exercises the real upload, draw
  and readback code. Only `src/platform/gl_context_sdl.cpp` needs SDL3, and it is
  the only file here that has never been compiled -- CI is its first compiler.
- `--screenshot <path>` writes binary PPM from `try_capture` (GL readback, flipped
  to top-down once at the boundary) or from the reference rasteriser when no
  surface exists.
- **The repository is the game.** `assets/` is a sub-project with its own gate
  (`python3 assets/tools/validate.py`) and its own CI job; the engine never links
  against asset tooling.
- Verification is `tools/verify.sh` at the root; CI runs the same script on 3 jobs
  plus an assets job. `tests/manual/` is exempt from `LAY-06` only.
- CI workflows only run from the root `.github/workflows/` -- which is why the
  restructure mattered.

## Releases

| Tag | Milestone | Contents |
|---|---|---|
| `v0.1.0-m1` | M1 | engine seed: fixed-step clock, platform layer, log sinks, 31 tests, gates, asset set |
| `v0.1.1-m1` | M1 layout | game-first tree, `assets/` as a sub-project, CI live at the root; no gameplay or API change |

Both are annotated and pushed with the branch. `kVersion` in `src/core/version.h`
moves with the tag, so a log line, a save header and a release name the same state.
A pushed tag is never moved; if a tagged state turns out to be broken, publish a
new tag rather than retagging it. The archives in `dist/` are built from the tagged
commit, not the working tree, so a download equals the release.

## Session log index

| # | Date | Milestone | Result |
|---|---|---|---|
| 000 | 2026-11-07 | planning | plan, style guide, protocol, decisions drafted |
| 001 | 2026-11-07 | M0 | repository seed, gates, tests; `verify: OK` |
| 002 | 2026-11-07 | M1 | platform + fixed-step clock + log sinks; 31 tests green |
| 003 | 2026-11-07 | restructure | game at the root, assets sub-project, CI live |
| 004 | 2026-11-07 | M2 (headless) | RHI contract, swap chain, headless backend, 8 tests |
| 005 | 2026-11-07 | M3 (software) | command buffer, rasteriser, triangle + debug lines, 9 tests |
| 006 | 2026-11-07 | M3b (GL) | GL backend behind an injected API table, PPM screenshots, 8 tests |

## Handoff -- (template, copy for each session)

```
Now:      <one sentence>
Green:    <command + summary line>
Red:      <failing command + first error, or "none">
Next:     <single next issue with number>
Blocked:  <decisions needed, else "none">
Files:    <<= 10 files to open first>
```
