"""Download HotpotQA, BEIR nq and NQ-open into data/raw/. Skips files that are already there.

Run on your Mac: `uv run python scripts/download_data.py` (about 0.5 GB, mostly the BEIR nq zip).
Add `--only hotpotqa` to fetch just what the pilot needs.
"""

import argparse
import sys
import zipfile
from pathlib import Path

import httpx

from lp.config import Paths

SOURCES = {
    "hotpotqa": [
        ("hotpot_dev_distractor_v1.json", "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json")
    ],
    "nq": [
        ("nq.zip", "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nq.zip"),
        (
            "NQ-open.dev.jsonl",
            "https://raw.githubusercontent.com/google-research-datasets/natural-questions/master/nq_open/NQ-open.dev.jsonl",
        ),
    ],
}


def download(url: str, target: Path) -> None:
    partial = target.with_suffix(target.suffix + ".part")
    print(f"downloading {url}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        done = 0
        with partial.open("wb") as handle:
            for block in response.iter_bytes(1 << 20):
                handle.write(block)
                done += len(block)
                if total:
                    print(f"\r  {done / 1e6:.0f} / {total / 1e6:.0f} MB", end="", flush=True)
    print()
    partial.rename(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(SOURCES), default=None)
    args = parser.parse_args()
    raw = Paths().raw_data
    raw.mkdir(parents=True, exist_ok=True)
    for name, files in SOURCES.items():
        if args.only and name != args.only:
            continue
        for filename, url in files:
            target = raw / filename
            if target.exists():
                print(f"have {target.name}")
                continue
            try:
                download(url, target)
            except httpx.HTTPError as exc:
                print(f"FAILED {url}: {exc}\nDownload it in a browser and put it at {target}", file=sys.stderr)
                return 1
    zipped = raw / "nq.zip"
    if zipped.exists() and not (raw / "nq" / "corpus.jsonl").exists():
        print("unzipping nq.zip")
        with zipfile.ZipFile(zipped) as archive:
            archive.extractall(raw)
    print("data ready in", raw)
    return 0


if __name__ == "__main__":
    sys.exit(main())
