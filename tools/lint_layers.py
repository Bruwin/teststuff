#!/usr/bin/env python3
"""Layering gate: STYLE-MOD-01..06 and STYLE-SIM-01.

Checks the project include graph in src/ against the allowed edges declared in
plan/PLAN.md section 3, plus the two rules the graph cannot express:

  MOD-03  no GL symbols above rhi/, no SDL symbols above platform/
  SIM-01  no floating point inside sim/

Exit codes: 0 clean, 1 findings, 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MODULES = ("core", "platform", "rhi", "render", "physics", "sim", "game", "ui", "net", "app")

ALLOWED: dict[str, set[str]] = {
    "core": {"core"},
    "platform": {"core", "platform"},
    "rhi": {"core", "rhi"},
    "render": {"core", "rhi", "render"},
    "physics": {"core", "physics"},
    "sim": {"core", "sim"},
    "game": {"core", "sim", "physics", "render", "rhi", "game"},
    "ui": {"core", "render", "rhi", "game", "ui"},
    "net": {"core", "sim", "net"},
    "app": set(MODULES),
}

INCLUDE_LINE = re.compile(r'^\s*#\s*include\s*"([^"]+)"')
GL_SYMBOL = re.compile(r"\b(GLuint|GLint|GLenum|GLfloat|GLsizei|GLboolean|glGen\w*|glBind\w*|glDraw\w*)")
SDL_SYMBOL = re.compile(r"\b(SDL_[A-Za-z_]+)")
FLOAT_TOKEN = re.compile(r"\b(float|double|long double)\b")
FLOAT_INCLUDE = re.compile(r"^\s*#\s*include\s*<(cmath|math\.h)>")
FLOAT_CALL = re.compile(r"\b(std::sqrt|std::fabs|std::fmod|std::pow|std::round|std::floor|std::ceil)\s*\(")

SOURCE_SUFFIXES = (".h", ".cpp")


def strip_comments(text: str) -> str:
    """Remove comments but keep string literals, preserving line numbers.

    Include directives live inside string literals, so the include scan must use
    this variant; the symbol scans use strip_noise so that a mention of GLuint in
    a string or comment cannot trip MOD-03.
    """
    out = []
    i = 0
    size = len(text)
    while i < size:
        two = text[i : i + 2]
        if two == "//":
            while i < size and text[i] != "\n":
                i += 1
        elif two == "/*":
            i += 2
            while i + 1 < size and text[i : i + 2] != "*/":
                if text[i] == "\n":
                    out.append("\n")
                i += 1
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def strip_noise(text: str) -> str:
    """Remove comments and string literals, preserving line numbers."""
    out = []
    i = 0
    size = len(text)
    while i < size:
        two = text[i : i + 2]
        if two == "//":
            while i < size and text[i] != "\n":
                i += 1
        elif two == "/*":
            i += 2
            while i + 1 < size and text[i : i + 2] != "*/":
                if text[i] == "\n":
                    out.append("\n")
                i += 1
            i += 2
        elif text[i] == '"':
            out.append('""')
            i += 1
            while i < size and text[i] != '"':
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def module_of(path: Path, root: Path) -> str | None:
    try:
        parts = path.relative_to(root / "src").parts
    except ValueError:
        return None
    if len(parts) < 2:
        return None
    module = parts[0]
    return module if module in MODULES else None


def check_file(path: Path, root: Path, check_floats: bool) -> list[str]:
    findings: list[str] = []
    module = module_of(path, root)
    if module is None:
        return findings

    raw = path.read_text(encoding="utf-8", errors="replace")
    clean = strip_noise(raw)
    uncommented = strip_comments(raw)
    rel = path.relative_to(root)

    for number, line in enumerate(uncommented.splitlines(), start=1):
        match = INCLUDE_LINE.match(line)
        if match:
            target = match.group(1).split("/")[0]
            if target in MODULES and target not in ALLOWED[module]:
                findings.append(
                    f"{rel}:{number}: LAY-01 {module}/ may not include {target}/ "
                    f"(allowed: {', '.join(sorted(ALLOWED[module]))})"
                )

    for number, line in enumerate(clean.splitlines(), start=1):
        if module != "rhi" and GL_SYMBOL.search(line):
            findings.append(f"{rel}:{number}: MOD-03 GL symbol outside rhi/")
        if module != "platform" and SDL_SYMBOL.search(line):
            findings.append(f"{rel}:{number}: MOD-03 SDL symbol outside platform/")

        if check_floats and module == "sim":
            if FLOAT_INCLUDE.match(line):
                findings.append(f"{rel}:{number}: SIM-01 <cmath> in sim/")
            if FLOAT_TOKEN.search(line):
                findings.append(f"{rel}:{number}: SIM-01 floating point type in sim/")
            if FLOAT_CALL.search(line):
                findings.append(f"{rel}:{number}: SIM-01 floating point call in sim/")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Layering and determinism gate.")
    parser.add_argument("--root", default=".", help="repository root to check")
    parser.add_argument("--floats", action="store_true", help="enforce SIM-01 in sim/")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    source_root = root / "src"
    if not source_root.is_dir():
        print(f"lint_layers: no src/ under {root}", file=sys.stderr)
        return 2

    findings: list[str] = []
    files = sorted(p for p in source_root.rglob("*") if p.suffix in SOURCE_SUFFIXES)
    if not files:
        print("lint_layers: no source files found", file=sys.stderr)
        return 2

    for path in files:
        findings.extend(check_file(path, root, args.floats))

    for finding in findings:
        print(finding)
    print(f"lint_layers: {len(files)} file(s), {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
