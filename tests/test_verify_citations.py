"""Offline tests for scripts/verify_citations.py: meta-tag parsing and the exact-quote check. No network."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("verify_citations", REPO_ROOT / "scripts" / "verify_citations.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

PAGE = """<html><head>
<meta name="citation_title" content="A Paper   About Lucky Passes">
<meta name="citation_author" content="Doe, Jane">
<meta name="citation_author" content="Roe, Rick">
<meta name="citation_date" content="2026/05/09">
<meta name="citation_abstract" content="We find that answers are often right
 without the gold passage.">
<meta name="description" content="ignored">
</head><body><p>body text</p></body></html>"""


def test_parse_meta_keeps_repeated_authors_and_ignores_other_tags():
    tags = verify.parse_meta(PAGE)
    assert tags["citation_author"] == ["Doe, Jane", "Roe, Rick"]
    assert tags["citation_date"] == ["2026/05/09"]
    assert "description" not in tags


def test_check_quotes_finds_exact_quotes_and_flags_invented_ones(tmp_path):
    results = [
        {
            "title": "A Paper About Lucky Passes",
            "abstract": "We find that answers are often right without the gold passage.",
        }
    ]
    notes = tmp_path / "notes.md"
    notes.write_text(
        "## paper\n"
        '> "answers are often right without the gold passage."\n'
        "> answers are always right\n"
        "not a quote line\n"
    )
    assert verify.check_quotes(notes, results) == ["answers are always right"]


def test_visible_text_drops_tags_and_scripts():
    assert verify.visible_text("<p>Hello <b>world</b></p><script>var x = 1;</script>") == "Hello world"
