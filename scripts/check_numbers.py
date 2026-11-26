"""Fail if the paper contains a number that doesn't appear in any results file (ground rule B2.3).

Checked files: paper/main.tex (ACL), paper/codex/main.tex (CODEX, if present) and paper/sections/*.tex.

Checked: every decimal number (62.3), every percentage (62%), and every integer of 11 or more that isn't a
year between 1900 and 2100. Small integers ("3 retrievers", "k = 5") and LaTeX commands, citations, labels and
comments are skipped. A results value of 0.623 counts as 62.3, 62 and 0.62, so rounding is accepted.
A line can opt out with the comment `% nocheck`, which reviewers will see.

Evidence is machine-written files only: .json, .csv and .tex under results/. Markdown is not evidence, because
some of it is prose written by people or Claude (FINDINGS.md); it would otherwise vouch for its own numbers.
"""

import json
import re
import sys
from pathlib import Path

from lp.config import REPO_ROOT

NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(\s*\\?%)?")
STRIP = [
    re.compile(r"(?<!\\)%.*$"),
    re.compile(
        r"\\(?:cite\w*|ref|label|eqref|url|href|includegraphics|input|usepackage|documentclass)(?:\[[^\]]*\])?\{[^}]*\}"
    ),
    re.compile(r"\\[a-zA-Z]+"),
]


def numbers_in_results(results_dir: Path) -> set[str]:
    allowed: set[str] = set()

    def add(value: float) -> None:
        for v in (value, value * 100):
            allowed.update({f"{v:.0f}", f"{v:.1f}", f"{v:.2f}", f"{v:.3f}"})
        if float(value).is_integer():
            allowed.add(str(int(value)))

    def walk(obj) -> None:
        if isinstance(obj, bool):
            return
        if isinstance(obj, (int, float)):
            add(float(obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for path in results_dir.rglob("*"):
        if path.suffix == ".json":
            walk(json.loads(path.read_text()))
        elif path.suffix in (".csv", ".tex"):
            for match in re.findall(r"\d+(?:\.\d+)?", path.read_text()):
                add(float(match))
    return allowed


def unverified_numbers(tex: str, allowed: set[str]) -> list[tuple[int, str]]:
    bad = []
    for lineno, line in enumerate(tex.splitlines(), start=1):
        if "% nocheck" in line:
            continue
        for pattern in STRIP:
            line = pattern.sub(" ", line)
        for match in NUMBER.finditer(line):
            number, percent = match.group(1), match.group(2)
            is_decimal = "." in number
            value = float(number)
            if not (is_decimal or percent or (value >= 11 and not (number.isdigit() and 1900 <= value <= 2100))):
                continue
            if number not in allowed:
                bad.append((lineno, number))
    return bad


def main() -> int:
    tex_path = REPO_ROOT / "paper" / "main.tex"
    if not tex_path.exists():
        print("paper/main.tex doesn't exist yet (Phase 6); nothing to check")
        return 0
    mains = [tex_path, *[p for p in [REPO_ROOT / "paper" / "codex" / "main.tex"] if p.exists()]]
    tex = "\n".join(p.read_text() for p in [*mains, *sorted((REPO_ROOT / "paper" / "sections").glob("*.tex"))])
    bad = unverified_numbers(tex, numbers_in_results(REPO_ROOT / "results"))
    for lineno, number in bad:
        print(f"line {lineno}: {number} is not in any results file")
    print("check_numbers:", "FAIL" if bad else "OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
