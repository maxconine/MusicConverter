import re
from difflib import SequenceMatcher

_VERSION_WORDS = re.compile(
    r"\b(live|remix|mix|instrumental|acoustic|karaoke|demo|radio edit|extended)\b",
    re.IGNORECASE,
)
_STOP_WORDS = {"the", "a", "an", "and", "of", "feat", "ft", "featuring"}


def normalize(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower().replace("&", " and ")
    text = re.sub(r"\b(featuring|feat\.?|ft\.?)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_parens(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", text)


def similarity(left: str | None, right: str | None) -> float:
    a = normalize(left)
    b = normalize(right)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def title_similarity(left: str | None, right: str | None) -> float:
    return max(
        similarity(left, right),
        similarity(strip_parens(left), strip_parens(right)),
    )


def artist_similarity(left: str | None, right: str | None) -> float:
    a = normalize(left)
    b = normalize(right)
    if not a or not b:
        return 0.0
    score = SequenceMatcher(None, a, b).ratio()
    if a in b or b in a:
        score = max(score, 0.92)
    left_tokens = set(a.split()) - _STOP_WORDS
    right_tokens = set(b.split()) - _STOP_WORDS
    if left_tokens and right_tokens:
        overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        score = max(score, overlap)
    return score


def version_penalty(source_title: str, candidate_title: str) -> float:
    source_versions = set(m.group(1).lower() for m in _VERSION_WORDS.finditer(source_title or ""))
    candidate_versions = set(
        m.group(1).lower() for m in _VERSION_WORDS.finditer(candidate_title or "")
    )
    extra = candidate_versions - source_versions
    if not extra:
        return 0.0
    return 0.08 * len(extra)
