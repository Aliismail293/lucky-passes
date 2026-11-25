"""Build paper/overleaf.zip: everything Overleaf needs to compile paper/main.tex, and nothing else.

Refuses to build if scripts/check_numbers.py fails, so a zip with an unverified number can't be made.
Upload: Overleaf -> New Project -> Upload Project -> paper/overleaf.zip. Compiler: pdfLaTeX.

Usage: uv run python scripts/build_overleaf.py
"""

import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAPER = REPO / "paper"
FILES = ["main.tex", "acl.sty", "acl_natbib.bst", "references.bib"]
FOLDERS = ["sections", "figures", "tables"]
SKIP_SUFFIXES = {".png"}
"""Figures go in as PDF (vector); the PNG copies are for the README and reports."""


def main() -> int:
    check = subprocess.run([sys.executable, str(REPO / "scripts" / "check_numbers.py")], cwd=REPO)
    if check.returncode != 0:
        print("check_numbers failed; not building the zip", file=sys.stderr)
        return 1
    out = PAPER / "overleaf.zip"
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(PAPER / name, name)
            count += 1
        for folder in FOLDERS:
            for path in sorted((PAPER / folder).rglob("*")):
                if path.is_file() and path.suffix not in SKIP_SUFFIXES:
                    archive.write(path, path.relative_to(PAPER).as_posix())
                    count += 1
    print(f"wrote {count} files to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
