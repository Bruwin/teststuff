# Factory engine

A C++20 factory-automation game: a deterministic fixed-point simulation at 30 Hz,
an OpenGL 4.6 renderer behind a thin RHI, and a voxel art set built to the engine's
grid. Currently at **M1** — window, input, fixed-step clock and log routing are in;
the renderer is next.

The repository *is* the game. The art pipeline is a sub-project in
[`assets/`](assets/README.md); it has its own README, its own generator and its own
CI gate, and it can be regenerated without touching engine code.

## Verify

```
./tools/verify.sh
```

One command, and it is the definition of green: convention lint, layering and
determinism lint, a self-test that plants violations and proves the linters reject
them, format check, build, unit tests, and the app's headless modes. CI runs this
exact script on Linux (gcc and clang) and Windows (MSVC). It prints `verify: OK`
or `verify: FAILED`.

```bash
# individual gates
python3 tools/lint_layers.py --root . --floats    # module graph + no floats in sim/
python3 tools/lint_conventions.py --root .        # the machine-checkable style rules
bash tools/selftest_linters.sh                    # proves the gates fail on bad input

# with CMake instead of the fallback compile
cmake --preset dev-ninja && cmake --build --preset dev-ninja && ctest --preset dev-ninja
```

## Run

```bash
./build/fct_app --ticks 30                        # headless: ticks, then state hash
./build/fct_app --frames 600 --frame-ns 16666667  # 10 s of synthetic 60 Hz frames
./build/fct_app --window                          # real window, needs SDL3 at build time
```

`--ticks` and `--frames` need no display and no SDL3, which is what keeps CI and
containers green. `--window` falls back to the synthetic loop with a warning when
the binary was built headless.

## Layout

| Path | Contents |
|---|---|
| `src/core/` | Q16.16 `Fix`, hashing, logging + sinks, fixed-step clock, version |
| `src/sim/` | deterministic world: tick order v1, state hash, no floats allowed |
| `src/platform/` | window, input, monotonic time; SDL3 backend or headless stub |
| `src/app/` | entry point and the frame loop |
| `src/game/` | gameplay systems (`merge_station.h` at present) |
| `tests/` | unit tests; `tests/manual/` holds harnesses run by hand |
| `tools/` | the gate: `verify.sh`, both linters, the planted-violation self-test |
| `assets/` | **sub-project**: 36 voxel models, glTF + OBJ, and their generator |
| `plan/` | plan, style guide, agent protocol, decisions, living state, session logs |

Dependency law (`plan/PLAN.md` §3) is enforced, not advisory: `sim/` includes
`core/` only and contains no floating point, nothing outside `rhi/` may mention
OpenGL, nothing outside `platform/` may mention SDL.

## Game systems

### Conveyor merge station

`src/game/merge_station.h` sequences a gate → diverter → merge line using the
linear joints the asset set exports (`blade`, `pusher`, `transfer`) and the four
photo-eyes those modules carry. Header-only, allocation-free, no engine types, so
it is testable without a window.

- **States** idle, hold, merge, reject, fault; every actuator is slew-limited, so a
  pose never jumps.
- **Interlocks** the chain never rises under a main-line item, a side item never
  enters the throat with a main item, and no item passes a closed blade.
- **Clearance** falling edges start dead-reckoned timers that bridge the gaps
  between beams; while one runs, a side item cannot claim the merge. The beam
  geometry and timer sizes are documented in
  [`assets/README.md` §7](assets/README.md).

The 120 s line harness asserts all of the above — accumulation behind the blade,
one rejected item, two side merges — and prints a state trace:

```bash
g++ -std=c++17 -O2 -Wall -Wextra -Isrc tests/manual/merge_station_demo.cpp -o merge_demo
./merge_demo                 # exits non-zero if any interlock is violated
MERGE_TRACE=1 ./merge_demo   # one-second samples of poses and item positions
```

## Asset sub-project

`assets/` holds 36 low-poly voxel modules — conveyors, machines, tanks, pipes,
robots, racking, plant services — as **glTF 2.0 (.glb)** with an **OBJ/MTL**
fallback, per-vertex colours and no textures at all. Every asset is one draw call
with zero texture memory.

```bash
python3 assets/tools/validate.py            # structural checks on every GLB/OBJ
python3 assets/tools/build.py               # regenerate everything (Python 3 + numpy)
python3 assets/tools/scene.py               # diorama render
```

The asset gate runs separately in CI, so a broken model cannot reach the engine
even though the engine does not need it to build. Details, art spec, rig format
and the full asset table: [`assets/README.md`](assets/README.md).

## Where to read first

`plan/STATE.md` is the living state — phase, green/red, next action, and the facts
worth not re-deriving. `plan/PLAN.md` is the design, `plan/STYLE_GUIDE.md` the
enforced rules, `plan/AGENT_PROTOCOL.md` the working agreement for agents and
humans, and `plan/sessions/` the per-session log that makes a context reset
survivable.
