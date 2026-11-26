"""Fail if a fact sheet (paper/codex/factsheets/*.md) states a number that its source doesn't hold.

Every number in a fact sheet carries a source tag right after it, and this script resolves the tag and checks that
the text between the previous tag (or the start of the file) and this one contains the value:

    `[src: results/pilot/summary.json#meta/datasets/hotpotqa/corpus_passages]`  a JSON (or YAML) value
    `[src: results/pilot/summary.json#cells[dataset=hotpotqa,retriever=bm25]/rates/lucky_pass]`  list filter
    `[src: lp/retrieve.py#RRF_K]`  a constant or dataclass default in Python code (`NAME = value`, `name: T = value`)

Keys are separated by "/" (model names contain dots). A rate (a dict with value, lo, hi and n) must be written as
"V% [L, H]" in percent with one decimal, plus "n = N"; any other number may be written as is, as an integer, or as a
percentage with up to 3 decimals. The fact sheets are Ali's notes for writing the paper; check_numbers.py checks
the paper itself.

Usage: uv run python scripts/check_factsheets.py [files...]
"""

import ast
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
FACTSHEETS = REPO / "paper" / "codex" / "factsheets"
TAG = re.compile(r"`\[src: ([^#`]+)#([^`]+?)\]`")
STEP = re.compile(r"^([^\[\]]+)(?:\[([^\]]+)\])?$")


def load(path: Path):
    if path.suffix == ".json":
        return json.loads(path.read_text())
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(path.read_text())
    raise ValueError(f"unsupported source type: {path}")


def resolve(obj, key: str):
    for part in key.split("/"):
        match = STEP.match(part)
        if not match:
            raise KeyError(part)
        name, filters = match.groups()
        obj = obj[int(name)] if isinstance(obj, list) else obj[name]
        if filters:
            wanted = dict(f.split("=", 1) for f in filters.split(","))
            hits = [item for item in obj if all(str(item.get(k)) == v for k, v in wanted.items())]
            if len(hits) != 1:
                raise KeyError(f"{part}: {len(hits)} matches")
            obj = hits[0]
    return obj


def python_constant(path: Path, name: str):
    pattern = re.compile(rf"^\s*{re.escape(name)}\s*(?::[^=]+)?=\s*(.+?)\s*(?:#.*)?$")
    for line in path.read_text().splitlines():
        match = pattern.match(line)
        if match:
            return ast.literal_eval(match.group(1))
    raise KeyError(name)


def source_value(file: str, key: str):
    path = REPO / file.strip()
    if path.suffix == ".py":
        return python_constant(path, key)
    return resolve(load(path), key)


def spellings(value) -> list[str]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return [str(value)]
    out = {str(value)}
    for v in (value, value * 100):
        for digits in (0, 1, 2, 3):
            out.add(f"{v:.{digits}f}")
        out.add(f"{v:,.0f}")
    return sorted(out, key=len, reverse=True)


def contains(text: str, candidate: str) -> bool:
    return re.search(rf"(?<![\d.]){re.escape(candidate)}(?![\d])", text) is not None


def problems_in(text: str, name: str) -> list[str]:
    bad = []
    start = 0
    for tag in TAG.finditer(text):
        segment = text[start : tag.start()]
        start = tag.end()
        where = f"{name}:{text.count(chr(10), 0, tag.start()) + 1}"
        try:
            value = source_value(*tag.groups())
        except (KeyError, IndexError, ValueError, FileNotFoundError, SyntaxError) as error:
            bad.append(f"{where}: can't resolve {tag.group(0)} ({error})")
            continue
        if isinstance(value, dict) and {"value", "lo", "hi", "n"} <= value.keys():
            rate = f"{value['value'] * 100:.1f}% [{value['lo'] * 100:.1f}, {value['hi'] * 100:.1f}]"
            if rate not in segment or not contains(segment, f"n = {value['n']}"):
                bad.append(f"{where}: expected '{rate}' and 'n = {value['n']}' before {tag.group(0)}")
        elif isinstance(value, (dict, list)):
            bad.append(f"{where}: {tag.group(0)} points at a {type(value).__name__}, not a value")
        elif not any(contains(segment, s) for s in spellings(value)):
            bad.append(f"{where}: {value!r} not found before {tag.group(0)}")
    return bad


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or sorted(FACTSHEETS.glob("*.md"))
    bad, tags = [], 0
    for path in files:
        text = path.read_text()
        tags += len(TAG.findall(text))
        bad += problems_in(text, path.name)
    for problem in bad:
        print(problem)
    print(f"check_factsheets: {tags} sourced numbers in {len(files)} files:", "FAIL" if bad else "OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
