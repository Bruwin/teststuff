# Factory engine

The game repository seed (milestone **M1**). The plans, rules and decisions live in
[`../plan/`](../plan/PLAN.md); read `../plan/STATE.md` first, always (`AGT-01`).

This directory becomes the repository root on GitHub: move its contents up, keep
the planning docs in `plan/`.

## Verify

```
./tools/verify.sh
```

Runs, in order: convention lint, layering + determinism lint, gate self-test
(planted violations must be rejected), format check, build, unit tests, and the
app's headless modes. It prints `verify: OK` or `verify: FAILED`, and CI runs
exactly this command.

Individual tools:

```
python3 tools/lint_layers.py --root . --floats   # MOD-*, SIM-01
python3 tools/lint_conventions.py --root .       # machine-checkable STYLE rules
bash tools/selftest_linters.sh                   # proves the gates fail on bad input
cmake --preset dev-ninja && cmake --build --preset dev-ninja && ctest --preset dev-ninja
```

## Run

```
./build/fct_app --ticks 30                  # headless: run 30 sim ticks, print hash
./build/fct_app --frames 600 --frame-ns 16666667   # 10 s of synthetic 60 Hz frames
./build/fct_app --window                    # real window (needs a build with SDL3)
```

`--ticks` and `--frames` need no display and no SDL3, which is what keeps CI and
containers green; `--window` falls back to the synthetic frame loop with a warning
when the binary was built headless.

## Layout

```
src/core/      math (Q16.16 Fix), hashing, logging + sinks, fixed-step clock, version
src/sim/       deterministic world: tick order v1, state hash
src/platform/  window + input + monotonic time (SDL3 backend, headless stub)
src/app/       entry point: --ticks, --frames, --window
tests/         harness + unit tests (doctest swap once vendoring is decided)
tools/         linters, verify.sh, gate self-test
```

Module law and the full allowlist: `../plan/PLAN.md` §3. Nothing outside
`src/rhi/` may mention GL; nothing outside `src/platform/` may mention SDL;
nothing inside `src/sim/` may use floating point. The linters enforce all three.

SDL3 is optional at configure time: CMake defines `FCT_HAVE_SDL3` and picks
`src/platform/window_sdl.cpp` or `src/platform/window_stub.cpp`. Both backends
must keep compiling — the headless one is what CI has.

## Status

M1: fixed-step clock, platform window/input behind SDL3 with a headless stub, log
routing, 31 unit tests. No renderer, physics or gameplay yet. See
`../plan/STATE.md` for what is next.
