# Session 002 — M1 platform, fixed-step clock, log routing

**Date:** 2026-11-07
**Milestone:** M1 (window, input, clock, log routing)
**Outcome:** `verify: OK` — 31 test cases, 0 failures, gate self-test 4/4.

## Plan for this session

1. `platform/` with a window + input + monotonic time API and an SDL3 backend.
2. A fixed-step clock that turns frame time into whole 30 Hz sim ticks, with a
   catch-up cap so a hitch never spirals.
3. Log routing (sinks) so output can be captured rather than only printed.
4. Keep the headless path green: `verify.sh` and CI run with no display.

## Decisions taken this session (agent judgement, reversible)

- **`platform/` has two interchangeable backends.** `window_sdl.cpp` when CMake
  finds SDL3, `window_stub.cpp` otherwise, selected in `CMakeLists.txt` and
  declaring `FCT_HAVE_SDL3` accordingly. Rationale: CI runners and cloud sandboxes
  have no display and often no SDL3; a missing window must degrade to "headless",
  not to "does not build". Both satisfy `platform/window.h`, so nothing above the
  module changes.
- **The clock is in `core/`, not `app/`.** It is integer-only, takes the timestamp
  as an argument and performs no OS calls, which makes it testable against
  synthetic time. `app/` only decides where time comes from.
- **`Window::present()` exists now, as a no-op.** M3 fills it in; call sites and
  the loop shape are already correct, so the renderer lands without rewriting the
  frame loop.
- **Input is a snapshot of named keys, not raw scancodes.** `Key` is an enum and
  `InputSnapshot` is a fixed array; gameplay code never sees SDL. Remapping and
  action binding stay for a later milestone.

## What was built

| File | Purpose |
|---|---|
| `src/core/fixed_step.h` | `FixedStepClock`: baseline, whole ticks, drop-backlog cap |
| `src/core/log.{h,cpp}` | `LogSink` + `log_set_sink`; stderr remains the default |
| `src/platform/time.{h,cpp}` | `monotonic_ns`, `sleep_for_ns` |
| `src/platform/window.h` | `Window`, `WindowDesc`, `InputSnapshot`, `Key` |
| `src/platform/window_stub.cpp` | headless backend |
| `src/platform/window_sdl.cpp` | SDL3 backend, opaque handle, no SDL above the module |
| `src/app/main.cpp` | `--ticks`, `--frames`, `--window` |
| 3 new test files | clock (8), log (4), platform (5) |

## Findings the gates caught

1. **`LAY-06` false positive.** The function-length heuristic closed a function on
   the first column-0 `}` — which, after comment stripping, is the namespace
   brace at the end of a header. A 12-line constructor inside a class was reported
   as 62 lines. Replaced with brace-depth tracking, which also measures member
   functions defined in headers, and added a planted 62-line function to the gate
   self-test so the rule cannot silently stop working.
2. **`Window::is_open()` returned headlessness, not openness** in the stub, so
   `close()` left the window "open". Caught by
   `platform_window_opens_and_reports_its_mode`. Added an explicit `open_` flag to
   both backends; "is it open" and "does it have a display" are different
   questions and were being conflated.

## Verified

```
bash tools/verify.sh
  conventions           24 files, 0 findings
  layering              16 files, 0 findings
  gate self-test        4/4 ok (now including LAY-06)
  tests                 31 cases, 0 failures
  ./fct_app --ticks 30          -> ticks=30 hash=61d0b61dbf56ae45
  ./fct_app --frames 600        -> ticks=299 dropped=0 alpha=0.500
  verify: OK
```

`--frames 600 --frame-ns 16666667` is 10.0 s of synthetic 60 Hz frames and
produces 299 ticks with alpha 0.500 — i.e. the loop paces 30 ticks per simulated
second and keeps the remainder for interpolation, exactly as designed.

## Not verified (stated plainly)

- **`window_sdl.cpp` was not compiled here**: this sandbox has no SDL3 headers and
  no network. It is ~110 lines against the SDL3 API and CI compiles it when
  `libsdl3-dev` is installable; the first job that has SDL3 is its first real
  compile. The stub path — the one that runs everywhere — is fully tested.
- **CMake was not run** (still absent); `CMakeLists.txt` changed substantially
  (SDL3 detection, new module) and is checked only by inspection and by the
  parallel g++ fallback, whose source lists are now globbed and therefore cannot
  drift from the file set.
- **Frame rate under a real window** is a desktop measurement, not something this
  environment can observe.

## Next action

M2: `rhi/` skeleton (device creation, swap chain, clear) and the first triangle,
OR the M1 gap if CI shows an SDL3 API mismatch. `PLAN.md` puts the renderer next,
and `present()` is the hook it needs.
