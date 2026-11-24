"""End to end: the mock pilot produces records, summary, tables, figures and a report, and resumes from cache."""

import json

import pytest

from lp.config import REPO_ROOT, load_config
from lp.runner import NeedsApproval, run

PILOT = REPO_ROOT / "configs" / "pilot.yaml"


def test_mock_pilot_end_to_end(isolated_paths):
    run_dir = run(load_config(PILOT), PILOT, mock=True, echo=lambda _: None)
    summary = json.loads((run_dir / "summary.json").read_text())
    cells = {c["dataset"]: c for c in summary["cells"]}
    assert set(cells) == {"hotpotqa", "invented"}
    for cell in cells.values():
        assert cell["n"] == 100
        assert sum(cell["counts"].values()) == cell["n"]
        rates = cell["rates"]
        assert rates["accuracy"]["value"] == pytest.approx(rates["true_pass"]["value"] + rates["lucky_pass"]["value"])
    # The invented control has no memory to fall back on, so no lucky passes; the toy "public" set has some.
    assert cells["invented"]["counts"]["lucky_pass"] == 0
    assert cells["hotpotqa"]["counts"]["lucky_pass"] > 0
    assert (run_dir / "PILOT_REPORT.md").exists()
    assert (run_dir / "tables" / "main_table.tex").exists()
    assert (run_dir / "figures" / "lucky_by_dataset.pdf").exists()
    records = (run_dir / "records.jsonl").read_text().splitlines()
    assert len(records) == 200
    progress = (isolated_paths / "research" / "research-progress.md").read_text()
    assert "pilot (mock)" in progress

    again = run(load_config(PILOT), PILOT, mock=True, echo=lambda _: None)
    meta = json.loads((again / "summary.json").read_text())["meta"]
    assert meta["timing"]["uncached_calls"] == 0


def test_real_run_requires_flag():
    with pytest.raises(RuntimeError, match="LP_REAL=1"):
        run(load_config(PILOT), PILOT, mock=False)


def test_time_gate_writes_needs_ali(isolated_paths):
    config = load_config(PILOT)
    config.max_hours = 0.0
    config.default_seconds_per_call = 10.0
    from lp import runner

    est = {"uncached_calls_est": 5000, "seconds_per_call": 10.0, "hours_est": 13.9}
    with pytest.raises(NeedsApproval):
        runner.gate(config, est, None, runner.Progress(config, False, echo=lambda _: None))
    needs = (isolated_paths / "research" / "NEEDS_ALI.md").read_text()
    assert "Approve long run: pilot" in needs and "13.9 hours" in needs
    runner.gate(config, est, approve_hours=20, progress=runner.Progress(config, False, echo=lambda _: None))
