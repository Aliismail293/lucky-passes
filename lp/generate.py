"""The three ways each question is answered: closed-book, RAG (retrieved passages) and oracle (gold passages only).

RAG and oracle use the same prompt; only the passages differ. The prompt is a typical practitioner prompt:
it asks the model to use the passages but does not forbid answering from memory. That is deliberate,
because the point is to measure what a normal RAG app scores.
"""

from lp.datasets import Passage

SYSTEM_PROMPT = (
    "You answer questions with a short answer: a name, number, date or short phrase. "
    "Give only the answer, with no explanation."
)
PASSAGES_HEADER = "Passages:"
QUESTION_LABEL = "Question:"
ANSWER_LABEL = "Answer:"


def closed_book_prompt(question: str) -> str:
    return f"{QUESTION_LABEL} {question}\n{ANSWER_LABEL}"


def passages_prompt(question: str, passages: list[Passage]) -> str:
    blocks = [f"[{i}] {p.title}\n{p.text}" if p.title else f"[{i}] {p.text}" for i, p in enumerate(passages, start=1)]
    return (
        f"{PASSAGES_HEADER}\n" + "\n\n".join(blocks) + "\n\n"
        "Using the passages above, answer the question.\n"
        f"{QUESTION_LABEL} {question}\n{ANSWER_LABEL}"
    )


def clean_answer(raw: str) -> str:
    """First non-empty line, without a leading 'Answer:' and trailing full stop."""
    for line in raw.strip().splitlines():
        line = line.strip()
        if line:
            if line.lower().startswith("answer:"):
                line = line[len("answer:") :].strip()
            return line.rstrip(".")[:300]
    return ""


def answer(client, question: str, passages: list[Passage] | None) -> str:
    """Closed-book when passages is None, otherwise RAG/oracle with those passages."""
    user = closed_book_prompt(question) if passages is None else passages_prompt(question, passages)
    return clean_answer(client.complete(SYSTEM_PROMPT, user))


def prompt_for(question: str, passages: list[Passage] | None) -> tuple[str, str]:
    """The (system, user) pair, used by the estimator to check whether a call is already cached."""
    user = closed_book_prompt(question) if passages is None else passages_prompt(question, passages)
    return SYSTEM_PROMPT, user
