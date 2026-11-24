"""Fetch each reference's page and print what it says (title, authors, date, abstract), so citations can be checked.

Ground rule B2.3: a citation is only used if its page resolves and the title and authors match.
Phase 1 uses this to build paper/citations_verified.md; Phase 7 re-runs it on the final reference list.

Usage:
    uv run python scripts/verify_citations.py arxiv:2005.11401 doi:10.1162/tacl_a_00276 url:https://...
    uv run python scripts/verify_citations.py --file paper/references.txt --out paper/verified_pages.json

arXiv, ACL Anthology and most publisher pages carry `citation_*` meta tags (the Google Scholar convention);
for DOIs we ask Crossref, which returns the registered metadata as JSON.
"""

import argparse
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "lucky-passes-citation-check/0.1 (research script)"}


class MetaTags(HTMLParser):
    """Collects <meta name="citation_..." content="..."> tags. Authors repeat, so every value is a list."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: dict[str, list[str]] = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        attr = dict(attrs)
        name = attr.get("name") or attr.get("property") or ""
        if name.startswith("citation_") and attr.get("content"):
            self.tags.setdefault(name, []).append(attr["content"].strip())


def parse_meta(html: str) -> dict[str, list[str]]:
    parser = MetaTags()
    parser.feed(html)
    return parser.tags


def from_page(url: str) -> dict:
    response = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
    tags = parse_meta(response.text) if response.status_code == 200 else {}
    return {
        "url": str(response.url),
        "status": response.status_code,
        "title": " ".join(tags.get("citation_title", [""])[0].split()),
        "authors": tags.get("citation_author", []),
        "date": (tags.get("citation_date") or tags.get("citation_publication_date") or [""])[0],
        "venue": (tags.get("citation_conference_title") or tags.get("citation_journal_title") or [""])[0],
        "abstract": " ".join((tags.get("citation_abstract") or [""])[0].split()),
        "page_text": visible_text(response.text) if url_kind_keeps_text(url) else "",
    }


def url_kind_keeps_text(url: str) -> bool:
    """arXiv abstracts come from meta tags; other pages (e.g. ACL Anthology) keep their visible text for quotes."""
    return "arxiv.org" not in url


def visible_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def check_quotes(notes: Path, results: list[dict]) -> list[str]:
    """Returns every '> quote' line in the notes that does not appear word for word in a fetched page."""
    haystack = " ".join(" ".join([r.get("title", ""), r.get("abstract", ""), r.get("page_text", "")]) for r in results)
    missing = []
    for line in notes.read_text().splitlines():
        if line.startswith("> "):
            quote = line[2:].strip().strip('"')
            if " ".join(quote.split()) not in haystack:
                missing.append(quote)
    return missing


def from_crossref(doi: str) -> dict:
    url = f"https://api.crossref.org/works/{doi}"
    response = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
    if response.status_code != 200:
        return {"url": url, "status": response.status_code, "title": "", "authors": [], "date": "", "venue": ""}
    work = response.json()["message"]
    parts = (work.get("published") or work.get("issued") or {}).get("date-parts", [[None]])[0]
    return {
        "url": f"https://doi.org/{doi}",
        "status": response.status_code,
        "title": " ".join((work.get("title") or [""])[0].split()),
        "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in work.get("author", [])],
        "date": "-".join(str(p) for p in parts if p),
        "venue": (work.get("container-title") or [""])[0],
        "abstract": "",
    }


def lookup(ref: str) -> dict:
    kind, _, value = ref.partition(":")
    if kind == "arxiv":
        result = from_page(f"https://arxiv.org/abs/{value}")
    elif kind == "doi":
        result = from_crossref(value)
    elif kind == "url":
        result = from_page(value)
    else:
        raise ValueError(f"unknown reference kind in {ref!r}; use arxiv:, doi: or url:")
    result["ref"] = ref
    result["checked"] = date.today().isoformat()
    result["resolved"] = result["status"] == 200 and bool(result["title"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("refs", nargs="*", help="arxiv:ID, doi:DOI or url:URL")
    parser.add_argument("--file", type=Path, help="one reference per line; # starts a comment")
    parser.add_argument("--out", type=Path, help="write all results as JSON here")
    parser.add_argument("--check-quotes", type=Path, help="notes file whose '> quote' lines must appear in a page")
    args = parser.parse_args()
    refs = list(args.refs)
    if args.file:
        lines = [line.split("#")[0].strip() for line in args.file.read_text().splitlines()]
        refs += [line for line in lines if line]
    results = []
    for ref in refs:
        try:
            result = lookup(ref)
        except httpx.HTTPError as exc:
            result = {"ref": ref, "resolved": False, "status": None, "error": str(exc)}
        results.append(result)
        flag = "OK  " if result["resolved"] else "FAIL"
        authors = ", ".join(result.get("authors", [])[:3])
        print(f"{flag} {ref} | {result.get('title', '')} | {authors} | {result.get('date', '')}")
    if args.out:
        args.out.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    ok = all(r["resolved"] for r in results)
    if args.check_quotes:
        missing = check_quotes(args.check_quotes, results)
        for quote in missing:
            print(f"QUOTE NOT FOUND: {quote}")
        print(f"quotes checked in {args.check_quotes}: {len(missing)} not found")
        ok = ok and not missing
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
