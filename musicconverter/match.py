from musicconverter.models import Track, TidalTrack
from musicconverter.text import artist_similarity, title_similarity, version_penalty


def score_track(source: Track, candidate: TidalTrack) -> float:
    title = title_similarity(source.title, candidate.title)
    artist = artist_similarity(source.artist, candidate.artist)
    album = 0.0
    if source.album and candidate.album:
        album = title_similarity(source.album, candidate.album)
    score = (0.62 * title) + (0.30 * artist) + (0.08 * album)
    score -= version_penalty(source.title, candidate.title)
    if source.duration_ms and candidate.duration_ms:
        delta = abs(source.duration_ms - candidate.duration_ms)
        if delta <= 2_000:
            score += 0.08
        elif delta <= 5_000:
            score += 0.03
        elif delta > 15_000:
            score -= 0.18
    return score


def is_acceptable(source: Track, candidate: TidalTrack, score: float) -> bool:
    title = title_similarity(source.title, candidate.title)
    artist = artist_similarity(source.artist, candidate.artist)
    if title < 0.80 or artist < 0.55 or score < 0.78:
        return False
    if source.duration_ms and candidate.duration_ms:
        delta = abs(source.duration_ms - candidate.duration_ms)
        if delta > 20_000 and artist < 0.85:
            return False
    return True


def choose_match(source: Track, candidates: list[TidalTrack]) -> tuple[TidalTrack | None, float]:
    ranked = sorted(
        ((score_track(source, candidate), candidate) for candidate in candidates),
        key=lambda item: item[0],
        reverse=True,
    )
    accepted = [
        (score, candidate)
        for score, candidate in ranked
        if is_acceptable(source, candidate, score)
    ]
    if not accepted:
        best_score = ranked[0][0] if ranked else 0.0
        return None, best_score

    best_score, best = accepted[0]
    if len(accepted) > 1 and source.duration_ms:
        second_score, second = accepted[1]
        if best_score - second_score <= 0.03 and second.duration_ms and best.duration_ms:
            best_delta = abs(source.duration_ms - best.duration_ms)
            second_delta = abs(source.duration_ms - second.duration_ms)
            if second_delta + 1_000 < best_delta:
                return second, second_score
    return best, best_score
