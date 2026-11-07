#!/usr/bin/env bash
# Proves the gates actually bite (M0 acceptance criterion).
#
# A linter that has never failed is a linter nobody should trust. This script
# builds a throwaway tree containing the violations the rules exist to catch,
# then asserts that each linter rejects it -- and that a clean tree passes, so a
# linter that always fails is caught too.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2
PY="${PYTHON:-python3}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

failures=0
pass() { printf '  ok   %s\n' "$1"; }
fail() { printf '  FAIL %s\n' "$1"; failures=$((failures + 1)); }

mkdir -p "$work/good/src/core" "$work/good/src/sim" "$work/good/tests"
cat > "$work/good/src/core/ok.h" <<'EOF'
// A clean header: the negative control for every gate below.
#pragma once

namespace fct {
inline constexpr int kAnswer = 42;
}  // namespace fct
EOF
cat > "$work/good/src/sim/ok.cpp" <<'EOF'
#include "core/fixed.h"

namespace fct::sim {
Fix advance(Fix clock) { return clock + Fix::from_ratio(1, 30); }
}  // namespace fct::sim
EOF
# tests/manual/ is exempt from LAY-06 only: a long harness must stay accepted,
# while the planted long function in src/sim/ above must still be rejected.
mkdir -p "$work/good/tests/manual"
{
    printf '%s\n' 'int main() {'
    for i in $(seq 1 70); do printf '    int v%d = %d;\n' "$i" "$i"; done
    printf '%s\n' '    return 0;' '}'
} > "$work/good/tests/manual/long_harness.cpp"

cat > "$work/good/tests/ok.cpp" <<'EOF'
#include "core/fixed.h"

int main() { return fct::Fix::from_int(1).to_int() == 1 ? 0 : 1; }
EOF

# --- planted violations ----------------------------------------------------
# LAY-01: sim/ including render/. SIM-01: floats and <cmath> inside sim/.
mkdir -p "$work/bad/src/sim" "$work/bad/src/render"
printf '%s\n' '#pragma once' > "$work/bad/src/render/render.h"
cat > "$work/bad/src/sim/bad_layers.cpp" <<'EOF'
#include <cmath>
#include "render/render.h"

namespace fct::sim {
double speed() { return std::sqrt(2.0); }
}  // namespace fct::sim
EOF

# LAY-01 tabs, LAY-08 namespace import: a header without #pragma once.
cat > "$work/bad/src/sim/bad_header.h" <<'EOF'
// Header without #pragma once on purpose.
namespace fct {
using namespace std;
}  // namespace fct
EOF

# LAY-01 tabs/length, ERR-06 endl, MEM-01 new, MEM-03 shared_ptr, LOG-01 printf,
# DOC-03 bare TODO.
printf '%s\n' \
    '// no pragma once on purpose' \
    'namespace fct {' \
    'void tabbed() {' \
    $'\tint x = 1;' \
    $'\tstd::cout << "x" << std::endl;' \
    $'\tint* p = new int(3);' \
    $'\tstd::shared_ptr<int> shared;' \
    $'\tprintf("%d", x);' \
    $'\t// TODO: remove this' \
    '}  // namespace fct' > "$work/bad/src/sim/bad_style.cpp"

# LAY-06: a function longer than 60 lines.
{
    printf '%s\n' 'namespace fct {' 'int overly_long(int x) {'
    for i in $(seq 1 62); do printf '    int v%d = x + %d;\n' "$i" "$i"; done
    printf '%s\n' '    return 0;' '}' '}  // namespace fct'
} > "$work/bad/src/sim/long_function.cpp"

echo "gate self-test"

"$PY" tools/lint_layers.py --root "$work/good" --floats >/dev/null 2>&1 \
    && pass "clean tree passes lint_layers" \
    || fail "clean tree rejected by lint_layers"

"$PY" tools/lint_layers.py --root "$work/bad" --floats > "$work/layers.txt" 2>&1
if [ $? -ne 0 ] && grep -q "LAY-01" "$work/layers.txt" && grep -q "SIM-01" "$work/layers.txt"; then
    pass "planted layering + float violations detected"
else
    fail "lint_layers did not detect the planted violation"
    sed 's/^/      /' "$work/layers.txt"
fi

"$PY" tools/lint_conventions.py --root "$work/good" >/dev/null 2>&1 \
    && pass "clean tree passes lint_conventions" \
    || fail "clean tree rejected by lint_conventions"

"$PY" tools/lint_conventions.py --root "$work/bad" > "$work/style.txt" 2>&1
if [ $? -ne 0 ] && grep -q "LAY-03" "$work/style.txt" && grep -q "LAY-08" "$work/style.txt" \
    && grep -q "ERR-06" "$work/style.txt" && grep -q "MEM-01" "$work/style.txt" \
    && grep -q "MEM-03" "$work/style.txt" && grep -q "DOC-03" "$work/style.txt" \
    && grep -q "LOG-01" "$work/style.txt" && grep -q "LAY-06" "$work/style.txt"; then
    pass "planted conventions violations detected"
else
    fail "lint_conventions did not detect the planted violations"
    sed 's/^/      /' "$work/style.txt"
fi

if [ "$failures" -eq 0 ]; then
    echo "gate self-test: OK"
    exit 0
fi
echo "gate self-test: $failures failure(s)"
exit 1
