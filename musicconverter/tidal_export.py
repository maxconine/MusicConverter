import webbrowser
from pathlib import Path

import tidalapi

from musicconverter.match import choose_match
from musicconverter.models import Match, SourcePlaylist, TidalTrack
from musicconverter.sources import PlaylistError


def connect(session_path: Path) -> tidalapi.Session:
    session = tidalapi.Session()
    if session_path.exists() and session.load_session_from_file(session_path):
        try:
            if session.check_login():
                return session
        except Exception:
            pass
    print()
    print("Tidal needs you to approve this on the account that should get the playlist.")
    login, future = session.login_oauth()
    url = login.verification_uri_complete
    if not url.startswith("http"):
        url = f"https://{url}"
    minutes = max(1, round(login.expires_in / 60))
    print(f"A browser window should open. If it does not, copy this link into your browser:")
    print(url)
    print(f"Log in and allow access within {minutes} minutes. Leave this window open.")
    print()
    webbrowser.open(url)
    try:
        future.result()
    except TimeoutError as exc:
        raise PlaylistError(
            "The Tidal login link expired before it was approved. "
            "Run convert again and allow access within 5 minutes."
        ) from exc
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session.save_session_to_file(session_path)
    session_path.chmod(0o600)
    return session


def tidal_track(track) -> TidalTrack:
    artists = []
    if getattr(track, "artists", None):
        artists = [artist.name for artist in track.artists if getattr(artist, "name", None)]
    if not artists and getattr(track, "artist", None) and getattr(track.artist, "name", None):
        artists = [track.artist.name]
    album = None
    if getattr(track, "album", None) and getattr(track.album, "name", None):
        album = track.album.name
    duration_ms = None
    if track.duration is not None:
        duration_ms = int(round(track.duration * 1000))
    url = getattr(track, "listen_url", None) or getattr(track, "share_url", None)
    return TidalTrack(
        id=str(track.id),
        title=track.name,
        artist=", ".join(artists),
        album=album,
        duration_ms=duration_ms,
        url=url,
    )


def search_tracks(session: tidalapi.Session, query: str) -> list[TidalTrack]:
    results = session.search(query, models=[tidalapi.Track], limit=15)
    return [tidal_track(track) for track in results.get("tracks") or []]


def match_playlist(session: tidalapi.Session, playlist: SourcePlaylist) -> list[Match]:
    matches: list[Match] = []
    total = len(playlist.tracks)
    for index, track in enumerate(playlist.tracks, start=1):
        query = f"{track.artist} {track.title}"
        print(f"Searching {index}/{total}: {track.artist} — {track.title}")
        try:
            candidates = search_tracks(session, query)
        except Exception as exc:
            print(f"  Search failed: {exc}")
            matches.append(Match(source=track, tidal=None, score=0.0))
            continue
        chosen, score = choose_match(track, candidates)
        if chosen:
            print(f"  Matched {chosen.artist} — {chosen.title}")
        else:
            print("  No confident Tidal match")
        matches.append(Match(source=track, tidal=chosen, score=score))
    return matches


def create_tidal_playlist(
    session: tidalapi.Session,
    playlist: SourcePlaylist,
    matches: list[Match],
    name: str | None = None,
) -> str:
    chosen = [match.tidal for match in matches if match.tidal]
    if not chosen:
        raise PlaylistError("No tracks matched on Tidal, so a playlist was not created.")
    title = name or playlist.name
    description = f"Converted from {playlist.source}: {playlist.url}"
    created = session.user.create_playlist(title, description)
    ids = [track.id for track in chosen]
    for start in range(0, len(ids), 100):
        created.add(ids[start : start + 100], allow_duplicates=True)
    return created.listen_url or created.share_url or f"https://tidal.com/playlist/{created.id}"
