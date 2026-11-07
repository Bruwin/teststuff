#!/usr/bin/env python3
"""Conventions gate: the machine-checkable half of plan/STYLE_GUIDE.md.

Rules enforced here (the rest live in clang-format / clang-tidy / review):

  LAY-01  line length <= 100, no tabs, no trailing whitespace, final newline
  LAY-03  headers start with #pragma once
  LAY-06  file <= 400 lines, function <= 60 lines (heuristic: brace depth)
  LAY-08  no `using namespace` in headers
  LAY-10  ASCII only in source
  ERR-06  no std::endl
  MEM-01  no new/delete in engine code
  MEM-03  no shared_ptr in engine code
  DOC-03  TODO must reference an issue: TODO(#123)
  LOG-01  no printf-family output in engine code (src/ only; tests may print)

Exit codes: 0 clean, 1 findings, 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_LINE = 100
MAX_FILE_LINES = 400
MAX_FUNCTION_LINES = 60

# Statement keywords that also look like `name(...) {` to a regex.
CONTROL_KEYWORDS = (
    "if ",
    "if(",
    "for ",
    "for(",
    "while ",
    "while(",
    "switch ",
    "switch(",
    "else",
    "do ",
    "catch ",
    "return ",
)

SOURCE_SUFFIXES = (".h", ".cpp")

PRINTF_CALL = re.compile(r"(?<![A-Za-z_.>])printf\s*\(")
NEW_OP = re.compile(r"(?<![A-Za-z_.>])new\s+(?!\[)[A-Za-z_<:(]")
DELETE_OP = re.compile(r"(?<![A-Za-z_.>])delete\s*(?:\[\s*\])?\s*[A-Za-z_(]")
TODO_REF = re.compile(r"TODO\((#[0-9]+|issue-[0-9]+)\)")
TODO_ANY = re.compile(r"TODO\b")
ENDL = re.compile(r"std::endl")
USING_NS = re.compile(r"\busing\s+namespace\b")
PRAGMA_ONCE = re.compile(r"^\s*#\s*pragma\s+once\s*$")

FUNCTION_START = re.compile(r"^[A-Za-z_~][\w:<>,&\*\s]*\([^;]*$")
TYPE_KEYWORDS = ("namespace", "struct", "class", "enum", "extern", "template", "using", "#")


def strip_comments(text: str) -> list[str]:
    """Remove // and /* */ comments, keeping line structure."""
    lines = []
    in_block = False
    for line in text.splitlines():
        result = []
        i = 0
        while i < len(line):
            if in_block:
                end = line.find("*/", i)
                if end == -1:
                    i = len(line)
                else:
                    in_block = False
                    i = end + 2
                continue
            if line.startswith("//", i):
                break
            if line.startswith("/*", i):
                in_block = True
                i += 2
                continue
            result.append(line[i])
            i += 1
        lines.append("".join(result))
    return lines


def check_file(path: Path, engine: bool) -> list[str]:
    findings: list[str] = []
    raw = path.read_text(encoding="utf-8", errors="replace")

    if not raw.endswith("\n"):
        findings.append(f"{path}: LAY-01 missing final newline")
    if not raw.isascii():
        findings.append(f"{path}: LAY-10 non-ASCII character in source")

    raw_lines = raw.splitlines()
    if len(raw_lines) > MAX_FILE_LINES:
        findings.append(f"{path}: LAY-06 file has {len(raw_lines)} lines (max {MAX_FILE_LINES})")

    if path.suffix == ".h":
        head = [line for line in raw_lines if line.strip() and not line.strip().startswith("//")]
        if not head or not PRAGMA_ONCE.match(head[0]):
            findings.append(f"{path}: LAY-03 header must start with #pragma once")

    clean = strip_comments(raw)

    for number, line in enumerate(raw_lines, start=1):
        if len(line) > MAX_LINE:
            findings.append(f"{path}:{number}: LAY-01 line is {len(line)} chars (max {MAX_LINE})")
        if "\t" in line:
            findings.append(f"{path}:{number}: LAY-01 tab character")
        if line != line.rstrip():
            findings.append(f"{path}:{number}: LAY-01 trailing whitespace")

    for number, line in enumerate(clean, start=1):
        if ENDL.search(line):
            findings.append(f"{path}:{number}: ERR-06 std::endl (use \\n)")
        if USING_NS.search(line) and path.suffix == ".h":
            findings.append(f"{path}:{number}: LAY-08 using namespace in a header")

    # Memory, output and TODO rules are about engine code and about comments:
    # TODO markers are stripped by strip_comments, so scan the raw lines for them.
    for number, line in enumerate(raw_lines, start=1):
        if TODO_ANY.search(line) and not TODO_REF.search(line):
            findings.append(f"{path}:{number}: DOC-03 TODO without an issue reference")

    if engine:
        for number, line in enumerate(clean, start=1):
            if NEW_OP.search(line):
                findings.append(f"{path}:{number}: MEM-01 new is banned in engine code")
            if DELETE_OP.search(line):
                findings.append(f"{path}:{number}: MEM-01 delete is banned in engine code")
            if "shared_ptr" in line:
                findings.append(f"{path}:{number}: MEM-03 shared_ptr is banned in engine code")
            if PRINTF_CALL.search(line):
                findings.append(f"{path}:{number}: LOG-01 printf-family output (use core/log.h)")

    # Function length, measured by brace depth rather than by indentation: a
    # member function defined inside a class or namespace must be measured too,
    # and a body must not be closed early by a brace in a nested block. Braces in
    # strings or comments could still confuse this; a heuristic is acceptable here
    # because LAY-06 is about gross size, not exact counting.
    depth = 0
    index = 0
    total = len(clean)
    while index < total:
        stripped = clean[index].strip()
        looks_like_function = (
            stripped.endswith("{")
            and "(" in stripped
            and not stripped.startswith(TYPE_KEYWORDS)
            and not stripped.startswith(CONTROL_KEYWORDS)
            and FUNCTION_START.match(stripped[:-1].strip() + "x")
        )
        if not looks_like_function:
            depth += stripped.count("{") - stripped.count("}")
            index += 1
            continue

        start_line = index + 1
        current = depth
        cursor = index
        while cursor < total:
            current += clean[cursor].count("{") - clean[cursor].count("}")
            cursor += 1
            if current <= depth:
                break
        length = cursor - index
        if length > MAX_FUNCTION_LINES:
            findings.append(
                f"{path}:{start_line}: LAY-06 function has {length} lines "
                f"(max {MAX_FUNCTION_LINES})"
            )
        depth = current
        index = cursor
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Conventions gate.")
    parser.add_argument("--root", default=".", help="repository root to check")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    candidates: list[Path] = []
    for directory in ("src", "tests"):
        base = root / directory
        if base.is_dir():
            candidates.extend(p for p in base.rglob("*") if p.suffix in SOURCE_SUFFIXES)
    if not candidates:
        print(f"lint_conventions: no sources under {root}/src or /tests", file=sys.stderr)
        return 2

    findings: list[str] = []
    for path in sorted(candidates):
        findings.extend(check_file(path, engine="src" in path.relative_to(root).parts))

    for finding in findings:
        print(finding)
    print(f"lint_conventions: {len(candidates)} file(s), {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
