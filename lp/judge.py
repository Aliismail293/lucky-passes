"""Is an answer correct? Two signals:

1. normalised contains-match: the normalised gold answer appears, as whole words, in the normalised prediction.
   Cheap, deterministic, and right when it fires.
2. an LLM judge from a different model family than the generator, used where contains-match can't decide
   (no match does not prove the answer is wrong: "JFK" vs "John F. Kennedy").

A sample of contains-matched answers also goes to the LLM judge, so the agreement between the two can be reported.
"""

import hashlib
import json
import re
import string

JUDGE_SYSTEM_PROMPT = "You grade answers to quiz questions. Reply with JSON only."
REFERENCE_LABEL = "Reference answer(s):"
PREDICTED_LABEL = "Predicted answer:"

ARTICLES = re.compile(r"\b(a|an|the)\b")


def normalize(text: str) -> str:
    """SQuAD-style: lowercase, drop punctuation and articles, squash spaces."""
    text = text.lower()
    text = "".join(" " if ch in string.punctuation else ch for ch in text)
    text = ARTICLES.sub(" ", text)
    return " ".join(text.split())


def exact_match(prediction: str, golds: list[str]) -> bool:
    return any(normalize(prediction) == normalize(g) for g in golds)


def contains_match(prediction: str, golds: list[str]) -> bool:
    """True if any normalised gold appears as whole words inside the normalised prediction."""
    pred = f" {normalize(prediction)} "
    return any(normalize(g) and f" {normalize(g)} " in pred for g in golds)


def judge_prompt(question: str, golds: list[str], prediction: str) -> str:
    return (
        f"Question: {question}\n"
        f"{REFERENCE_LABEL} {' | '.join(golds)}\n"
        f"{PREDICTED_LABEL} {prediction}\n\n"
        "Does the predicted answer mean the same thing as one of the reference answers? "
        "Different wording, a different format for the same value, or extra detail that is still correct "
        'all count as correct. Reply exactly {"correct": true} or {"correct": false}.'
    )


def parse_judge(raw: str) -> bool | None:
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if match:
        try:
            value = json.loads(match.group(0)).get("correct")
            if isinstance(value, bool):
                return value
        except (json.JSONDecodeError, AttributeError):
            pass
    lowered = raw.lower()
    if "true" in lowered and "false" not in lowered:
        return True
    if "false" in lowered and "true" not in lowered:
        return False
    return None


def in_agreement_sample(item_id: str, rate: float) -> bool:
    """Deterministic: the same item is always in or out of the sample."""
    bucket = int(hashlib.sha256(item_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return bucket < rate


def judge(question: str, golds: list[str], prediction: str, judge_client, item_id: str, sample_rate: float) -> dict:
    """Returns {correct, method, contains, llm}. method is 'contains', 'llm', 'empty' or 'llm_unparseable'."""
    contains = contains_match(prediction, golds)
    if not prediction.strip():
        return {"correct": False, "method": "empty", "contains": False, "llm": None}
    run_llm = (not contains) or in_agreement_sample(item_id, sample_rate)
    llm_verdict = None
    if run_llm:
        llm_verdict = parse_judge(judge_client.complete(JUDGE_SYSTEM_PROMPT, judge_prompt(question, golds, prediction)))
    if contains:
        return {"correct": True, "method": "contains", "contains": True, "llm": llm_verdict}
    if llm_verdict is None:
        return {"correct": False, "method": "llm_unparseable", "contains": False, "llm": None}
    return {"correct": llm_verdict, "method": "llm", "contains": False, "llm": llm_verdict}


def agreement(verdicts: list[dict]) -> dict:
    """Agreement between contains-match and the LLM judge, over every item where the LLM judge ran."""
    pairs = [(v["contains"], v["llm"]) for v in verdicts if v.get("llm") is not None]
    table = {"both_correct": 0, "both_wrong": 0, "contains_only": 0, "llm_only": 0}
    for contains, llm in pairs:
        if contains and llm:
            table["both_correct"] += 1
        elif not contains and not llm:
            table["both_wrong"] += 1
        elif contains:
            table["contains_only"] += 1
        else:
            table["llm_only"] += 1
    n = len(pairs)
    agree = table["both_correct"] + table["both_wrong"]
    return {"n": n, "agree": agree, "rate": agree / n if n else None, "table": table}
