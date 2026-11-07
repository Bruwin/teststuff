## What and why

<!-- One paragraph: the capability added or defect fixed, and the reason. -->

Refs: #

## How it was verified

<!-- Paste the summary line from ./tools/verify.sh, plus any bench table. -->

```
verify: OK
```

## Checklist (reject the PR on any unchecked MUST rule)

- [ ] `AGT-04` — `./tools/verify.sh` green; summary line above
- [ ] `AGT-11` — PR is <= 400 changed lines and <= 12 files
- [ ] `AGT-12` — one concern only; no drive-by formatting (`AGT-10`, `GIT-03`)
- [ ] `MOD-01/02` — include graph respects the layer law (lint_layers passes)
- [ ] `SIM-01` — no floating point added to `sim/`
- [ ] `SIM-06` — tick-order version bumped and goldens regenerated *(if rules changed)*
- [ ] `MEM-01/02` — no allocation added to a tick or frame-critical loop
- [ ] `TEST-01/02` — new rules and fixed bugs ship tests in this PR
- [ ] `DOC-02/03` — public headers documented; TODOs reference issues
- [ ] `PERF-03` — bench numbers included *(if performance is claimed)*
- [ ] `AGT-13` — known gaps stated below

## Known gaps

<!-- What this does not do yet. "None" is an acceptable answer, silence is not. -->

## Decision records

<!-- DEC-IDs touched, or "none". Tick order, save format and protocol changes
     require a ratified record and human approval (AGT-06, AGT-22). -->
