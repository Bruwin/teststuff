#!/usr/bin/env bash
# The single definition of "green" (AGENT_PROTOCOL.md). CI runs this exact
# script on every platform; if it passes locally it should pass there.
#
# Order matters: cheap static gates first, so a style violation never waits on a
# compile, and the planted-violation self-test before the real build, so a broken
# gate is caught before its verdict is trusted.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2

PY="${PYTHON:-python3}"
CXX_BIN="${CXX:-c++}"
build="build"
failures=0

step() { printf '\n== %s\n' "$1"; }
record() { if [ "$1" -ne 0 ]; then failures=$((failures + 1)); fi; }

step "conventions (STYLE-*)"
"$PY" tools/lint_conventions.py --root .
record $?

step "layering and determinism (MOD-*, SIM-01)"
"$PY" tools/lint_layers.py --root . --floats
record $?

step "gate self-test (planted violations must be rejected)"
bash tools/selftest_linters.sh
record $?

step "format (clang-format, when available)"
if command -v clang-format >/dev/null 2>&1; then
    mapfile -t format_files < <(find src tests -type f \( -name '*.h' -o -name '*.cpp' \))
    clang-format --dry-run --Werror "${format_files[@]}" 2>/dev/null
    record $?
else
    echo "  skipped: clang-format not installed (CI enforces it)"
fi

step "build and tests"
mkdir -p "$build"
if command -v cmake >/dev/null 2>&1; then
    cmake --preset dev >/dev/null
    record $?
    cmake --build --preset dev
    record $?
    ctest --preset dev --output-on-failure
    record $?
    ./build/dev/fct_app --ticks 30
    record $?
else
    echo "  cmake not installed: direct-compile fallback (CI uses CMake)"
    # Same flags as CMakeLists.txt. Source lists are globbed so a new module does
    # not silently drop out of the fallback build.
    mapfile -t lib_sources < <(find src -type f -name '*.cpp' ! -name '*_sdl.cpp' ! -path 'src/app/*' | sort)
    # tests/manual/ holds harnesses with their own main(); they are built by hand.
    mapfile -t test_sources < <(find tests -type f -name '*.cpp' ! -path 'tests/manual/*' | sort)
    cxx_flags=(-std=c++20 -O2 -g -Isrc -Itests
        -Wall -Wextra -Wpedantic -Wshadow -Wnon-virtual-dtor -Wold-style-cast
        -Wcast-align -Woverloaded-virtual -Wdouble-promotion -Wformat=2
        -Wmissing-declarations -Wundef -Werror -fno-exceptions -fno-rtti)

    "$CXX_BIN" "${cxx_flags[@]}" "${lib_sources[@]}" src/app/main.cpp -o "$build/fct_app"
    record $?

    "$CXX_BIN" "${cxx_flags[@]}" "${lib_sources[@]}" "${test_sources[@]}" -o "$build/fct_tests"
    record $?

    if [ -x "$build/fct_tests" ]; then
        "./$build/fct_tests"
        record $?
    fi
    if [ -x "$build/fct_app" ]; then
        "./$build/fct_app" --ticks 30
        record $?
        "./$build/fct_app" --frames 600 --frame-ns 16666667
        record $?
    fi
fi

if [ "$failures" -eq 0 ]; then
    echo ""
    echo "verify: OK"
    exit 0
fi
echo ""
echo "verify: FAILED ($failures step(s))"
exit 1
