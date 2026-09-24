from dataclasses import dataclass


@dataclass
class Track:
    title: str
    artist: str
    album: str | None = None
    duration_ms: int | None = None
    url: str | None = None


@dataclass
class SourcePlaylist:
    name: str
    source: str
    url: str
    tracks: list[Track]
    expected_count: int | None = None


@dataclass
class TidalTrack:
    id: str
    title: str
    artist: str
    album: str | None = None
    duration_ms: int | None = None
    url: str | None = None


@dataclass
class Match:
    source: Track
    tidal: TidalTrack | None
    score: float
