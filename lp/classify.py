"""The paper's core table: each RAG answer falls into one of four outcome classes.

                    answer correct     answer wrong
gold retrieved      true pass          grounding failure
gold not retrieved  lucky pass         miss

"Gold retrieved" uses hit_any (at least one gold passage in the top k), matching the definition
"answer correct while no gold passage was retrieved". For multi-hop HotpotQA we also record hit_all,
and `outcome_all` repeats the table with "gold retrieved" meaning every gold passage was retrieved.
The hit_any version is conservative: it gives a lower bound on lucky passes.
"""

TRUE_PASS = "true_pass"
GROUNDING_FAILURE = "grounding_failure"
LUCKY_PASS = "lucky_pass"
MISS = "miss"
OUTCOMES = (TRUE_PASS, GROUNDING_FAILURE, LUCKY_PASS, MISS)

MEMORY_LUCKY = "memory_lucky"
GUESS_LUCKY = "guess_lucky"


def hits(retrieved_ids: list[str], gold_ids: list[str], k: int) -> tuple[bool, bool]:
    """(hit_any, hit_all) for the top k retrieved ids."""
    top = set(retrieved_ids[:k])
    gold = set(gold_ids)
    return bool(top & gold), bool(gold) and gold <= top


def outcome(gold_retrieved: bool, correct: bool) -> str:
    if gold_retrieved:
        return TRUE_PASS if correct else GROUNDING_FAILURE
    return LUCKY_PASS if correct else MISS


def lucky_kind(outcome_class: str, correct_closed: bool) -> str | None:
    """Memory lucky: the model also got it right closed-book. Guess lucky: it didn't."""
    if outcome_class != LUCKY_PASS:
        return None
    return MEMORY_LUCKY if correct_closed else GUESS_LUCKY
