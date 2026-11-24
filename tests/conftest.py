"""Point every path at a temp folder so tests never touch real results, caches or Ali's research files."""

import pytest


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("LP_RESULTS_DIR", str(tmp_path / "results"))
    monkeypatch.setenv("LP_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("LP_RESEARCH_DIR", str(tmp_path / "research"))
    monkeypatch.setenv("LP_DATA_DIR", str(tmp_path / "raw"))
    monkeypatch.delenv("LP_REAL", raising=False)
    return tmp_path
