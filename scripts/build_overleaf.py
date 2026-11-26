"""Build the Overleaf upload for the paper: everything needed to compile it, and nothing else.

--venue acl (default) -> paper/overleaf.zip from paper/main.tex with the ACL style files.
  Upload: Overleaf -> New Project -> Upload Project -> paper/overleaf.zip. Compiler: pdfLaTeX.
--venue codex -> paper/codex_overleaf.zip from paper/codex/main.tex (as main.tex). It has no style files: the
  journal's pepadun.sty and pepadun.bib stay in the journal's own template project. Open the template
  (paper/codex/main.tex, top comment), Menu -> Copy Project, then upload these files into the copy, replacing main.tex.

Refuses to build if scripts/check_numbers.py fails, so a zip with an unverified number can't be made.

Usage: uv run python scripts/build_overleaf.py [--venue acl|codex]
"""

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAPER = REPO / "paper"
VENUES = {
    "acl": ("overleaf.zip", {"main.tex": "main.tex", "acl.sty": "acl.sty", "acl_natbib.bst": "acl_natbib.bst"}),
    "codex": ("codex_overleaf.zip", {"main.tex": "codex/main.tex"}),
}
"""Per venue: the zip's name, and its top-level files (name in the zip -> path under paper/)."""
FOLDERS = ["sections", "figures", "tables"]
SKIP_SUFFIXES = {".png"}
"""Figures go in as PDF (vector); the PNG copies are for the README and reports."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--venue", choices=sorted(VENUES), default="acl")
    args = parser.parse_args()
    zip_name, top_files = VENUES[args.venue]
    check = subprocess.run([sys.executable, str(REPO / "scripts" / "check_numbers.py")], cwd=REPO)
    if check.returncode != 0:
        print("check_numbers failed; not building the zip", file=sys.stderr)
        return 1
    out = PAPER / zip_name
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, source in {**top_files, "references.bib": "references.bib"}.items():
            archive.write(PAPER / source, name)
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
