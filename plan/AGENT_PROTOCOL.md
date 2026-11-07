# Agent protocol

Rules for every agent (and human) working on this repository. Rules are cited by
ID when rejecting a change. Violating a `MUST` rule blocks merge; violating a
`SHOULD` rule needs a written reason in the PR.

`STYLE_GUIDE.md` covers code shape. This file covers *process*.

---

## 1. Non-negotiables

- **AGT-01 MUST** — Read `STATE.md` before doing anything. It is the only
  authoritative statement of where the project is.
- **AGT-02 MUST** — `MUST` files (`STYLE_GUIDE.md`, `AGENT_PROTOCOL.md`,
  `PLAN.md`, `DECISIONS.md`) change only with human approval in the PR thread.
- **AGT-03 MUST** — One issue per branch. No opportunistic work in the same PR:
  file a new issue instead, `STATE.md` records it under "Next".
- **AGT-04 MUST** — Every PR is green on `tools/verify.sh` before review, and the
  PR body contains the command's summary line.
- **AGT-05 MUST** — Follow the session loop in `PLAN.md` §9, including the
  handoff block.
- **AGT-06 MUST** — Never change the tick order, save format version, or wire
  protocol without a decision record and human approval.
- **AGT-07 MUST** — Never delete or rewrite another author's test to make code
  pass. If a test is wrong, fix the test in its own PR with evidence.
- **AGT-08 MUST** — Never disable a lint rule, warning, or CI check locally.
  Suppressions require an inline justification, a rule ID, and reviewer approval.
- **AGT-09 MUST** — Respect ownership (`CODEOWNERS`). Touching a file you do not
  own requires a comment on the issue and review from its owner.
- **AGT-10 MUST** — Keep the diff honest: no unrelated reformatting, no mass
  renames, no dependency bumps in a feature PR.

## 2. Work sizing

- **AGT-11** PR ≤ 400 changed lines, ≤ 12 files. Larger work is split; a stack of
  small PRs is always preferred to one large one.
- **AGT-12** A PR does one of: add capability, fix a defect, improve performance,
  or add tests/docs. Never two.
- **AGT-13** Every PR states: what changed, why, how it was verified, what it does
  *not* do (known gaps).
- **AGT-14** Commits are atomic and buildable in order (`git bisect` must work).

## 3. Branch, commit, merge

```
main            protected; requires 1 review + green CI
  feat/...      one issue
  fix/...       one defect
  wip/...       allowed to be red; never merged; named in STATE.md
```

- **AGT-15** Commit format per `STYLE-GIT-01`; body ends with `Refs: #123`.
- **AGT-16** Rebase on `main` before requesting review; merge commits are
  forbidden on feature branches.
- **AGT-17** A red `main` is a stop-the-line event: whoever broke it fixes it or
  reverts first, before any new work. `STATE.md` must record the incident.
- **AGT-18** Release branches are cut, never patched in place.

## 4. Review

- **AGT-19** Reviewers must check, in order: layering (`MOD-01`), determinism
  (`SIM-*`), allocation discipline (`MEM-*`), tests (`TEST-*`), style.
- **AGT-20** A rejection names the rule ID and the line. "I don't like it" is not
  a review (`[HUMAN]` reviewers included).
- **AGT-21** Claims of correctness without evidence ("this is definitely
  correct", "no bugs") are rejected; require a test, a bench number, or a hash.
- **AGT-22** Two approvals are required for `sim/`, `net/`, save format, and
  anything in `MUST` files; one of them human.
- **AGT-23** Review the diff, not the author. Agents must not approve their own
  work under any account.

## 5. Context loss

The single biggest failure mode for an agent-driven repo. The contract:

- **AGT-24 MUST** — At session start, read `STATE.md` only. Open further files
  only when the current issue needs them, and record what you read in the session
  log.
- **AGT-25 MUST** — At session end, write a handoff block (template below) and
  overwrite `STATE.md`'s "Now / Next / Blocked" sections. A session without a
  handoff is an incomplete session.
- **AGT-26 MUST** — Sessions are logged in `plan/sessions/YYYY-MM-DD-HH.md`:
  plan, what actually happened, commands run, surprises, commit hashes, next
  action. Append-only.
- **AGT-27** Assume nothing about code you have not read this session. If
  `STATE.md` and the code disagree, the code wins — then fix `STATE.md` in the
  same PR.
- **AGT-28** Never carry a mental model of a subsystem across sessions without
  re-reading its public header. The header is the contract (`API-01`).

### Handoff block (paste into `STATE.md`)

```
## Handoff — <date> <session n>
Now:      <one sentence: current state of the world>
Green:    <command + summary line that passes right now>
Red:      <failing command + first error, or "none">
Next:     <the single next issue, with its issue number>
Blocked:  <decisions needed from the human, else "none">
Files:    <the ≤ 10 files the next session should open first>
```

## 6. Ownership and roles

`CODEOWNERS` assigns each path. Recommended agent roles (a single agent may hold
several, never the review of its own work):

| Role | Paths | Responsibility |
|---|---|---|
| `arch` | `PLAN.md`, `DECISIONS.md`, cross-module headers | contracts, tick order |
| `core` | `src/core`, `src/platform` | math, fixed-point, allocators |
| `gfx` | `src/rhi`, `src/render` | device, chunks, culling |
| `sim` | `src/sim`, `tests/golden` | determinism, lanes, power, fluids |
| `phys` | `src/physics` | Jolt wrapper, belts, jams |
| `game` | `src/game`, `data/` | machines, tech, build mode |
| `ui` | `src/ui` | HUD, panels, input focus |
| `net` | `src/net`, `tests/net` | transport, snapshots, soak |
| `tools` | `tools/`, `.github/` | cooker, lint, CI, bench |

- **AGT-29** Cross-role changes are split into per-role PRs that land in order.
- **AGT-30** A role may not merge its own PR; `arch` reviews contract changes.

## 7. Definition of done for a task

All of the following, or the task is not done:

1. Code follows `STYLE_GUIDE.md`; `lint_conventions` and `lint_layers` pass.
2. Tests exist per `TEST-01/02`; goldens regenerated if `SIM-06` applies.
3. `verify.sh` green locally and in CI; PR body carries the summary.
4. Docs updated: header block, `STATE.md` handoff, decision record if a contract
   moved.
5. Bench table included if performance is claimed (`PERF-03`).
6. Known gaps stated explicitly in the PR ("does not do X yet").

## 8. Escalate to the human

Stop and ask (via the issue thread, not by guessing) when:

- a new dependency, platform, or tool would enter the build;
- the tick order, save format, or protocol must change;
- a performance budget must be raised;
- a milestone's acceptance criteria look unachievable in the time budget;
- two `MUST` rules conflict;
- a task would exceed 400 lines and cannot be split cleanly.

Everything else: use judgement, document the assumption in the PR body, and keep
going. **Assumptions written down are cheap; assumptions held silently are the
expensive kind.**
