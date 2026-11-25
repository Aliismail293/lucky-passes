"""Offline tests for Phase 3b: judge v2, the full HotpotQA corpus, the exact time estimate and the judge comparison."""

import csv
import importlib.util
import json

import pytest

from lp import judge, runner
from lp.config import REPO_ROOT, load_config, validate
from lp.datasets import load_hotpotqa
from lp.mock import MockChat

PILOT = REPO_ROOT / "configs" / "pilot.yaml"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CountingJudge:
    model = "judge:1b"

    def __init__(self, reply='{"correct": true}'):
        self.reply, self.calls, self.prompts = reply, 0, []

    def complete(self, system, user):
        self.calls += 1
        self.prompts.append(user)
        return self.reply


# --- judge v2 ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text", ["None", "none.", "Not specified", "Not applicable", "Unknown", "I don't know", "N/A", "Not provided",
             "The passages do not mention it", "cannot be determined"],
)  # fmt: skip
def test_non_answers_are_wrong_without_llm(text):
    llm = CountingJudge()
    verdict = judge.judge("Who?", ["Sir Francis Nethersole"], text, llm, "item", sample_rate=1.0)
    assert verdict == {"correct": False, "method": "non_answer", "contains": False, "llm": None}
    assert llm.calls == 0


@pytest.mark.parametrize("text", ["Paris", "Unknown Pleasures", "Nonesuch Records", "none of the above"])
def test_real_answers_are_not_non_answers(text):
    assert not judge.is_non_answer(text)


def test_non_answer_that_is_the_gold_is_still_correct():
    verdict = judge.judge("How many?", ["None"], "None", CountingJudge(), "item", sample_rate=0.0)
    assert verdict["correct"] and verdict["method"] == "contains"


def test_v1_reproduces_the_first_pilot():
    """v1 sends refusals to the LLM and uses the old prompt text, so cached pilot calls still match."""
    llm = CountingJudge()
    verdict = judge.judge("Who?", ["X"], "None", llm, "item", 0.0, prompt_version="v1")
    assert verdict["method"] == "llm" and llm.calls == 1
    assert llm.prompts[0].startswith("Question: Who?") and "Be strict" not in llm.prompts[0]


def test_v2_prompt_has_examples_including_a_wrong_entity_and_puts_the_item_last():
    prompt = judge.judge_prompt("Which actor?", ["Christopher Pine"], "James Corden")
    assert prompt.count('{"correct": false}') >= 2 and "Al Pacino" in prompt
    last = prompt.rsplit(judge.REFERENCE_LABEL, 1)[1]
    assert "Christopher Pine" in last and "James Corden" in last
    with pytest.raises(ValueError):
        judge.judge_prompt("q", ["a"], "b", version="v9")


def test_mock_judge_grades_the_item_not_the_examples():
    mock = MockChat()
    assert mock.complete(judge.JUDGE_SYSTEM_PROMPT, judge.judge_prompt("q", ["Paris"], "paris")) == '{"correct": true}'
    assert mock.complete(judge.JUDGE_SYSTEM_PROMPT, judge.judge_prompt("q", ["Paris"], "Rome")) == '{"correct": false}'


@pytest.mark.parametrize("prediction", ["", "None", "Paris", "Rome", "Paris, France"])
@pytest.mark.parametrize("rate", [0.0, 1.0])
def test_needs_llm_matches_what_judge_does(prediction, rate):
    llm = CountingJudge()
    judge.judge("q", ["Paris"], prediction, llm, "item", rate)
    assert judge.needs_llm(["Paris"], prediction, "item", rate) == (llm.calls == 1)


def test_config_rejects_unknown_flags():
    config = load_config(PILOT)
    assert config.judge_prompt == "v2" and config.hotpotqa_corpus == "full"
    config.hotpotqa_corpus = "everything"
    with pytest.raises(ValueError, match="hotpotqa_corpus"):
        validate(config)


# --- full HotpotQA corpus ----------------------------------------------------------------------------


def hotpot_record(i, titles, gold, answer="Answer"):
    return {
        "_id": f"id{i:02d}",
        "question": f"Question {i}?",
        "answer": answer,
        "type": "bridge",
        "level": "easy",
        "supporting_facts": [[t, 0] for t in gold],
        "context": [[t, [f"{t} text."]] for t in titles],
    }


@pytest.fixture
def hotpot_file(tmp_path):
    records = [hotpot_record(i, [f"T{i}a", f"T{i}b", "Shared"], [f"T{i}a", "Shared"]) for i in range(6)]
    records.append(hotpot_record(6, ["T6a", "Shared"], ["T6a"], answer="yes"))
    path = tmp_path / "hotpot.json"
    path.write_text(json.dumps(records))
    return path


def test_full_corpus_pools_every_question_deduplicated_by_title(hotpot_file):
    full = load_hotpotqa(hotpot_file, n=2, seed=1, corpus="full")
    # 6 non-yes/no questions x 2 own titles + the yes/no question's own title + one shared title.
    assert len(full.passages) == 6 * 2 + 1 + 1 == full.info["corpus_passages"]
    assert full.info["corpus"] == "full" and len(full.questions) == 2
    for q in full.questions:
        assert len(q.gold_ids) == 2 and all(p in full.passages for p in q.gold_ids)


def test_sampled_corpus_has_only_the_sampled_questions_paragraphs(hotpot_file):
    sampled = load_hotpotqa(hotpot_file, n=2, seed=1, corpus="sampled")
    full = load_hotpotqa(hotpot_file, n=2, seed=1, corpus="full")
    assert len(sampled.passages) == 2 * 2 + 1
    assert set(sampled.passages) < set(full.passages)
    assert [q.qid for q in sampled.questions] == [q.qid for q in full.questions]
    assert [q.gold_ids for q in sampled.questions] == [q.gold_ids for q in full.questions]


def test_title_clash_keeps_the_sampled_questions_version(tmp_path):
    records = [hotpot_record(0, ["A", "B"], ["A"]), hotpot_record(1, ["A", "C"], ["A"])]
    records[1]["context"][0][1] = ["A, other version."]
    path = tmp_path / "hotpot.json"
    path.write_text(json.dumps(records))
    dataset = load_hotpotqa(path, n=1, seed=0, corpus="full")
    chosen = dataset.questions[0]
    own_text = next(r for r in records if "hp:" + r["_id"] == chosen.qid)["context"][0][1][0]
    assert dataset.passages[chosen.gold_ids[0]].text == own_text
    assert dataset.info["corpus_title_text_clashes"] == 1


# --- exact time estimate -------------------------------------------------------------------------------


def test_estimate_counts_cached_calls_exactly_after_a_mock_run(isolated_paths):
    config = load_config(PILOT)
    before = json.loads((runner.run(config, PILOT, mock=True, estimate_only=True, echo=lambda _: None)
                         / "estimate.json").read_text())  # fmt: skip
    assert before["answer_calls_cached"] == 0
    runner.run(load_config(PILOT), PILOT, mock=True, echo=lambda _: None)
    after = json.loads((runner.run(load_config(PILOT), PILOT, mock=True, estimate_only=True, echo=lambda _: None)
                        / "estimate.json").read_text())  # fmt: skip
    assert after["answer_calls_cached"] == after["answer_calls"]
    assert after["judge_calls_uncached_est"] == 0 and after["uncached_calls_est"] == 0
    assert after["embeddings_uncached"] == 0


def test_changing_the_judge_prompt_makes_judge_calls_uncached(isolated_paths):
    runner.run(load_config(PILOT), PILOT, mock=True, echo=lambda _: None)
    config = load_config(PILOT)
    config.judge_prompt = "v1"
    est = json.loads((runner.run(config, PILOT, mock=True, estimate_only=True, echo=lambda _: None)
                      / "estimate.json").read_text())  # fmt: skip
    assert est["answer_calls_cached"] == est["answer_calls"]
    assert est["judge_calls_cached"] == 0 and est["judge_calls_uncached_est"] > 0


# --- judge comparison script ---------------------------------------------------------------------------

evaluate = load_script("eval_judges")
FIELDS = ["dataset", "qid", "condition", "question", "gold_answers", "prediction", "llm_judge", "human_correct",
          "claude_label"]  # fmt: skip


def row(qid, prediction, label, human=""):
    values = ["toy", qid, "rag", "Which city?", "Paris", prediction, "correct", human, label]
    return dict(zip(FIELDS, values, strict=True))


def test_ali_edit_wins_over_claude_label():
    assert evaluate.reference_label(row("q", "x", "correct")) == "correct"
    assert evaluate.reference_label(row("q", "x", "correct", "edited by Ali: incorrect")) == "incorrect"
    with pytest.raises(ValueError):
        evaluate.reference_label(row("q", "x", "correct", "edited by Ali"))
    with pytest.raises(ValueError):
        evaluate.reference_label(row("q", "x", "maybe"))


def test_score_excludes_unclear_and_reports_false_accepts():
    items = [{**row(f"q{i}", "x", lab), "reference": lab} for i, lab in enumerate(
        ["correct", "correct", "incorrect", "incorrect", "unclear"])]  # fmt: skip
    result = evaluate.score(items, [True, False, True, False, True])
    assert result["n"] == 4 and result["agreement"]["value"] == 0.5
    assert result["false_accept_rate"]["value"] == 0.5 and result["false_reject_rate"]["value"] == 0.5


def test_choose_never_picks_the_generators_family():
    results = {
        "qwen2.5:7b": {"agreement": {"value": 0.99}, "false_accept_rate": {"value": 0.0}},
        "llama3.1:8b": {"agreement": {"value": 0.80}, "false_accept_rate": {"value": 0.3}},
        "gemma2:9b": {"agreement": {"value": 0.90}, "false_accept_rate": {"value": 0.1}},
    }
    assert evaluate.choose(results) == {"llama": "qwen2.5:7b", "qwen": "gemma2:9b"}


def test_eval_script_mock_end_to_end_leaves_labels_untouched(tmp_path):
    sheet = tmp_path / "check.csv"
    rows = [row("q1", "Paris", "correct"), row("q2", "Rome", "incorrect"), row("q3", "None", "incorrect"),
            row("q4", "Lyon", "unclear")]  # fmt: skip
    with sheet.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    before = sheet.read_bytes()
    out = tmp_path / "out"
    assert evaluate.main(["--csv", str(sheet), "--out", str(out), "--mock", "--judges", "gemma2:9b"]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["unclear_qids"] == ["q4"]
    assert summary["results"]["gemma2:9b"]["agreement"]["value"] == 1.0
    assert summary["results"]["gemma2:9b"]["methods"]["non_answer"] == 1
    assert "not human labels" in summary["reference_label_note"]
    assert sheet.read_bytes() == before


def test_export_refuses_to_overwrite_a_labelled_sheet(tmp_path, monkeypatch):
    export = load_script("export_judge_check")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "records.jsonl").write_text("")
    sheet = tmp_path / "sheet.csv"
    sheet.write_text("labels")
    monkeypatch.setattr("sys.argv", ["export", str(run_dir), str(sheet)])
    assert export.main() == 1 and sheet.read_text() == "labels"


def test_two_judges_must_both_accept():
    from lp.judge import all_accept

    assert all_accept([True, True]) is True
    assert all_accept([True, False]) is False
    assert all_accept([None, False]) is False
    assert all_accept([True, None]) is None


class _Fixed:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def complete(self, system: str, user: str) -> str:
        return self.reply


def test_judge_with_a_list_of_clients_records_each_verdict():
    from lp.judge import judge as run_judge

    lenient, strict = _Fixed('{"correct": true}'), _Fixed('{"correct": false}')
    v = run_judge("Q?", ["07:00 to 15:00"], "8 AM - 5 PM", [lenient, strict], "q|m|closed", 0.0)
    assert v["correct"] is False and v["method"] == "llm" and v["llm_each"] == [True, False]
    v = run_judge("Q?", ["07:00 to 15:00"], "8 AM - 5 PM", [lenient, lenient], "q|m|closed", 0.0)
    assert v["correct"] is True


def test_choose_accepts_pairs_only_when_every_judge_is_cross_family():
    def r(agree, fa):
        return {"agreement": {"value": agree}, "false_accept_rate": {"value": fa}}

    results = {
        "gemma2:9b": r(0.85, 0.27), "qwen2.5:7b": r(0.889, 0.053), "llama3.1:8b": r(0.82, 0.32),
        "llama3.1:8b+gemma2:9b": r(0.903, 0.16), "gemma2:9b+qwen2.5:7b": r(0.889, 0.053),
        "llama3.1:8b+qwen2.5:7b": r(0.95, 0.0),
    }
    chosen = evaluate.choose(results)
    assert chosen["qwen"] == "llama3.1:8b+gemma2:9b"
    assert chosen["llama"] == "qwen2.5:7b"


def test_v3_adds_rules_and_examples_and_keeps_v2_unchanged():
    v2 = judge.judge_prompt("When?", ["07:00 to 15:00"], "8 AM - 5 PM", version="v2")
    v3 = judge.judge_prompt("When?", ["07:00 to 15:00"], "8 AM - 5 PM", version="v3")
    assert "whatever the format" not in v2 and "09:30 to 16:00" not in v2
    assert "whatever the format" in v3 and "several required items" in v3
    assert v3.count('{"correct": false}') == v2.count('{"correct": false}') + 2
    assert v3.rsplit(judge.REFERENCE_LABEL, 1)[1] == v2.rsplit(judge.REFERENCE_LABEL, 1)[1]
