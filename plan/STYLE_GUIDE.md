# Style guide

Every rule has an ID. **Reviews reject by ID** (`"STYLE-NAM-04: m_ prefix on a
POD member"`), and every rule is either machine-checked by
`tools/lint_conventions.py` / clang-format / clang-tidy, or explicitly marked
`[HUMAN]`. A rule that cannot be checked and is not marked `[HUMAN]` is a bug in
this guide: fix the guide.

Changing this file requires human approval (`AGT-02`).

---

## NAM — naming

- **NAM-01** Types are `PascalCase`: `ChunkBatch`, `BeltLane`. No `C`/`T` prefixes.
- **NAM-02** Functions and variables are `snake_case`: `advance_lane()`, `item_id`.
- **NAM-03** Private members end with `_`: `tick_count_`, `arena_`.
- **NAM-04** No Hungarian prefixes, no `m_` (we use the trailing underscore).
- **NAM-05** Compile-time constants are `kPascalCase`: `kMaxChunks`, `kTickHz`.
- **NAM-06** Macros are `FCT_UPPER_SNAKE`: `FCT_ASSERT`.
- **NAM-07** Booleans read as predicates: `is_valid`, `has_power`, `can_place`.
- **NAM-08** Units live in the name when a value has them:
  `speed_mps`, `length_m`, `ticks_per_second`, `bytes_used`. No bare `size`,
  `time`, `speed` unless the unit is genuinely dimensionless.
- **NAM-09** Enumerators are `PascalCase` inside `enum class`: `Kind::Belt`.
- **NAM-10** Files are `snake_case.cpp/.h`, one public type per header, header
  name matches the type (`chunk_batcher.h` → `ChunkBatcher`).
- **NAM-11** Namespaces: `fct` root, `fct::sim`, `fct::render`, `fct::gl`.
- **NAM-12** No abbreviations except an allowlist: `id`, `io`, `fs`, `gpu`, `aabb`,
  `aabb3`, `rhi`, `ui`, `fps`, `ms`, `px`, `min`, `max`, `ptr`, `idx`.

## LAY — layout and files

- **LAY-01** Four-space indentation, no tabs, 100-column limit.
- **LAY-02** Braces on the same line; always braces, even for one statement.
- **LAY-03** `#pragma once` only; no include guards.
- **LAY-04** Include order: own header, `core/`, other project, third-party,
  standard library; each block alphabetised, blank line between blocks.
- **LAY-05** Headers include what they use; no relying on transitive includes
  (`include-what-you-use` runs in CI on a subset).
- **LAY-06** Max 400 lines per file, 60 lines per function, 5 parameters.
  Exceeding requires a comment justifying it and reviewer approval.
- **LAY-07** One public type per header. Private helpers live in the `.cpp` in an
  anonymous namespace.
- **LAY-08** No `using namespace` in headers; `using` declarations are allowed in
  `.cpp` scope only.
- **LAY-09** Forward declarations are preferred over includes in headers when
  only a pointer/reference is needed.
- **LAY-10** ASCII only in code; non-ASCII allowed in docs/markdown only.

## MOD — modules and layering

- **MOD-01** The include graph must satisfy `PLAN.md` §3; `tools/lint_layers.py`
  enforces it and CI fails on violation.
- **MOD-02** `sim/` may include `core/` only.
- **MOD-03** No GL or SDL types may appear above `rhi/` and `platform/`
  respectively. If a header leaks `GLuint`, the review rejects it.
- **MOD-04** `render/` never includes `game/` or `sim/`.
- **MOD-05** New third-party dependency requires decision record `DEC-xx` and a
  pinned commit/tag in `third_party/`.
- **MOD-06** Public API of a module is one header per module (`sim/sim.h`), even
  if internals are many files.

## SIM — determinism

- **SIM-01** No `float`/`double` in `sim/`. Use `Fix` (Q16.16) or integers.
  clang-tidy check + grep gate (`tools/lint_layers.py --floats`).
- **SIM-02** No `std::` containers in `sim/` hot paths: use `StaticVector`,
  `Span`, arena-backed vectors.
- **SIM-03** Iteration order is by index, never by pointer or hash-map order.
  Hash maps must be `SmallMap` with sorted iteration or forbidden entirely.
- **SIM-04** No address-dependent behaviour: no `reinterpret_cast` of pointers to
  integers in hashing, no `std::hash`, no time, no RNG outside the seeded
  deterministic generator.
- **SIM-05** The RNG is `SplitMix64` seeded per subsystem from the world seed;
  never `rand()`, never `random_device`.
- **SIM-06** Every new rule that changes outcomes bumps `kTickOrderVersion` and
  regenerates goldens in the same PR, with the diff explained in the PR body.
- **SIM-07** Physics results never enter `sim_hash()` (see `DECISIONS.md` D-004).

## MEM — memory

- **MEM-01** No `new`/`delete` in engine code; use arenas, pools, `std::vector`
  reserved at load, or `Unique<T>`.
- **MEM-02** No allocation inside a tick (§2.5). Pre-size at load; assert on
  arena overflow in debug.
- **MEM-03** Ownership is explicit: `Unique<T>` single owner, `T*` non-owning,
  `Span<T>` view. `shared_ptr` is banned in engine code; allowed in tools.
- **MEM-04** Every arena has a named owner and a documented high-water mark in
  the bench output.
- **MEM-05** Buffers grown at runtime must be `reserve`d from a measured
  high-water mark; `push_back` in a loop without `reserve` is rejected.

## ERR — errors

- **ERR-01** Exceptions are disabled (`-fno-exceptions`). Errors are returned as
  `Status`/`Result<T,E>` or reported through the logger and a safe default.
- **ERR-02** `FCT_ASSERT` documents an invariant; it must not be used for input
  validation (use `Status`).
- **ERR-03** Every fallible function name says so: `try_`, `parse_`, `load_`
  returns `Result`.
- **ERR-04** No swallowed errors: every `Result` is checked or explicitly
  `[[maybe_unused]]` with a comment.
- **ERR-05** User-facing failures must be recoverable and logged with context
  (path, id, expected shape).
- **ERR-06** `std::endl` is banned; `\n` and explicit flush.

## PERF — performance

- **PERF-01** No allocation, file IO, logging above `Debug` level, or exception
  path inside tick or frame-critical loops.
- **PERF-02** Data-oriented by default: structs of arrays for per-item state,
  hot/cold splitting, ≤ 64-byte per-tick structs.
- **PERF-03** Every performance PR includes a `bench` table before/after from the
  same runner.
- **PERF-04** No virtual calls in per-item inner loops; use free functions or
  templates over type enums.
- **PERF-05** Prefer `Span<const T>` parameters over `const std::vector<T>&`.
- **PERF-06** Measure with the project profiler (`--profile`), not intuition; a
  claim without numbers is rejected.

## API — interfaces

- **API-01** Public headers document preconditions, postconditions and units.
- **API-02** No boolean parameters that change behaviour; use `enum class`
  (`DrawMode::kDepthOnly`). Two booleans at a call site is a review reject.
- **API-03** Defaults in interfaces must be safe: a zero-initialised struct must
  be a valid no-op.
- **API-04** Free functions over member functions when no state is needed.
- **API-05** `const` by default; mutating functions are named for the mutation
  (`apply_`, `advance_`, `consume_`).
- **API-06** No out-parameters except for multiple returns; prefer returning a
  small struct.
- **API-07** ABI: no STL types across module boundaries in public headers.

## DOC — comments and docs

- **DOC-01** Comments explain *why*, never *what*. `// increment i` is a reject.
- **DOC-02** Every public type and non-obvious function has a doc comment with
  units and ownership.
- **DOC-03** `TODO` must carry an issue reference: `// TODO(#142): ...`.
- **DOC-04** No commented-out code. Delete it; git remembers.
- **DOC-05** Every `.h` starts with a 3–10 line block explaining the invariant it
  protects.
- **DOC-06** Decision records are append-only and never edited after merge.

## TEST — testing

- **TEST-01** New sim rule ⇒ new unit test + golden scenario in the same PR.
- **TEST-02** Bug fixes ship a regression test that fails without the fix.
- **TEST-03** Tests are deterministic: no wall-clock, no sleeps, no network
  (except in `tests/net`), no unseeded randomness.
- **TEST-04** Test names state the behaviour: `belt_items_do_not_overlap()`.
- **TEST-05** Golden files are reviewed like code; a changed hash needs an
  explanation in the PR body.
- **TEST-06** No test may be skipped permanently; `DISABLED_` requires an issue.

## UI — user interface

- **UI-01** Simulation code never calls UI code; UI reads state through
  const views.
- **UI-02** All player-facing strings go through `tr("key")` (localisation table)
  even while only English exists.
- **UI-03** Dear ImGui is debug-only (`FCT_DEBUG_UI`); shipping HUD uses `ui/`.
- **UI-04** Interactive targets ≥ 24 px; keyboard and gamepad reachable.

## GIT — repository hygiene

- **GIT-01** Commits: `type(scope): imperative summary` ≤ 72 chars, body explains
  why, `Refs: #issue`. Types: `feat fix perf refactor test docs build ci chore`.
- **GIT-02** No binary blobs > 1 MB except cooked assets under `assets/` (via LFS
  if needed); generators and sources win over committed output.
- **GIT-03** No drive-by reformatting; formatting-only commits are labelled
  `style:` and contain nothing else.
- **GIT-04** Branch names: `feat/m06-lane-slots`, `fix/net-fragment-dup`.
- **GIT-05** Never commit secrets, keys, absolute local paths, or editor files.
- **GIT-06** Never rewrite pushed history; revert with a commit.
