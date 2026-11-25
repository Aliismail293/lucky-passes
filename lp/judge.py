"""Is an answer correct? Two signals:

1. normalised contains-match: the normalised gold answer appears, as whole words, in the normalised prediction.
   Cheap, deterministic, and right when it fires.
2. an LLM judge from a different model family than the generator, used where contains-match can't decide
   (no match does not prove the answer is wrong: "JFK" vs "John F. Kennedy").

A sample of contains-matched answers also goes to the LLM judge, so the agreement between the two can be reported.

Judge v2 (2026-11-24, after the pilot): non-answers ("None", "unknown", "not specified", ...) are wrong by rule,
without asking the LLM, and the LLM prompt is stricter, with four short worked examples. The v1 prompt is kept so
the first pilot can be reproduced (`judge_prompt: v1` in a config).
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


# Whole-answer refusals. Matched against the normalised prediction, so case and punctuation don't matter.
# "N/A" normalises to "n" (the article "a" is dropped), and "don't" to "don t".
NON_ANSWERS = {
    "none", "unknown", "n", "na", "nothing", "no answer", "not known", "not sure", "unsure", "unclear",
    "i don t know", "i do not know", "don t know", "idk", "cannot answer", "cannot be determined",
    "not enough information", "no information", "insufficient information", "information not available",
}  # fmt: skip
NON_ANSWER_RE = re.compile(
    r"^(it is |this is |that is |answer is )?"
    r"(not (specified|mentioned|provided|applicable|available|stated|given|known|found|clear|determinable)"
    r"|(the )?(passages?|context|text|documents?) (do|does) not (say|mention|specify|state|provide|contain)"
    r"|(i )?(cannot|can ?t|could not|am unable to|unable to) (answer|determine|tell|say|find))\b"
)


def is_non_answer(prediction: str) -> bool:
    """True for an empty answer or a refusal like "None", "Not specified" or "I don't know"."""
    text = normalize(prediction)
    return not text or text in NON_ANSWERS or bool(NON_ANSWER_RE.match(text))


# Worked examples for the v2 prompt. They are invented, not taken from any dataset or from the labelled pilot items,
# so the judge check on those items isn't contaminated.
V2_EXAMPLES = [
    ("Which author wrote both novels?", "John Ronald Reuel Tolkien", "J. R. R. Tolkien", True),
    ("Which actor starred in both films?", "Robert De Niro", "Al Pacino", False),
    ("In which city was the band formed?", "Manchester", "Liverpool", False),
    ("Where was the poet born?", "Lyon, France", "French", False),
]


def judge_prompt(question: str, golds: list[str], prediction: str, version: str = "v2") -> str:
    if version == "v1":
        return judge_prompt_v1(question, golds, prediction)
    if version != "v2":
        raise ValueError(f"unknown judge prompt version {version!r}")
    examples = "\n\n".join(
        f"Question: {q}\n{REFERENCE_LABEL} {g}\n{PREDICTED_LABEL} {p}\n"
        + ('{"correct": true}' if ok else '{"correct": false}')
        for q, g, p, ok in V2_EXAMPLES
    )
    return (
        "Grade the predicted answer against the reference answer(s). Be strict.\n"
        "- Correct: it names the same person, place, thing, number or date as a reference. A short form, nickname, "
        "different format or extra correct detail is fine.\n"
        "- Incorrect: a different person, place or thing, even a related one (a co-star, a nearby city, "
        "another work by the same author).\n"
        "- Incorrect: a vaguer answer that doesn't name the reference (a nationality instead of a city, "
        "a category instead of a title).\n"
        '- Incorrect: a refusal or non-answer such as "None" or "Not specified".\n\n'
        f"Examples:\n\n{examples}\n\nNow grade this one. "
        'Reply exactly {"correct": true} or {"correct": false}.\n\n'
        f"Question: {question}\n"
        f"{REFERENCE_LABEL} {' | '.join(golds)}\n"
        f"{PREDICTED_LABEL} {prediction}\n"
    )


def judge_prompt_v1(question: str, golds: list[str], prediction: str) -> str:
    """The prompt used in the first pilot (too lenient: see audit/pilot_review_notes.md)."""
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


def _rule_says_non_answer(prediction: str, golds: list[str], prompt_version: str) -> bool:
    # A refusal is wrong without asking the LLM, unless it really is the gold answer (a gold of "None" exists).
    return prompt_version != "v1" and is_non_answer(prediction) and not exact_match(prediction, golds)


def needs_llm(golds: list[str], prediction: str, item_id: str, sample_rate: float, prompt_version: str = "v2") -> bool:
    """Whether judge() will call the LLM for this answer. Used by the time estimate, so it must match judge()."""
    if not prediction.strip() or _rule_says_non_answer(prediction, golds, prompt_version):
        return False
    return (not contains_match(prediction, golds)) or in_agreement_sample(item_id, sample_rate)


def judge(
    question: str,
    golds: list[str],
    prediction: str,
    judge_client,
    item_id: str,
    sample_rate: float,
    prompt_version: str = "v2",
) -> dict:
    """Returns {correct, method, contains, llm}.

    method is 'contains', 'llm', 'empty', 'non_answer' (v2 only) or 'llm_unparseable'.
    """
    contains = contains_match(prediction, golds)
    if not prediction.strip():
        return {"correct": False, "method": "empty", "contains": False, "llm": None}
    if _rule_says_non_answer(prediction, golds, prompt_version):
        return {"correct": False, "method": "non_answer", "contains": False, "llm": None}
    llm_verdict = None
    if needs_llm(golds, prediction, item_id, sample_rate, prompt_version):
        prompt = judge_prompt(question, golds, prediction, prompt_version)
        llm_verdict = parse_judge(judge_client.complete(JUDGE_SYSTEM_PROMPT, prompt))
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
