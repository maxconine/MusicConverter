import json
import re
from urllib.parse import urlparse

import requests

from musicconverter.models import SourcePlaylist, Track

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
APPLE_ID = re.compile(r"(pl\.[A-Za-z0-9.\-]+)")
SPOTIFY_ID = re.compile(
    r"(?:open\.spotify\.com/(?:embed/)?playlist/|spotify:playlist:)([A-Za-z0-9]+)"
)


class PlaylistError(RuntimeError):
    pass


def detect_source(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc.lower()
    if host.endswith("music.apple.com") and "/playlist/" in parsed.path:
        return "apple"
    if "spotify.com" in host or url.startswith("spotify:playlist:"):
        if SPOTIFY_ID.search(url):
            return "spotify"
    raise PlaylistError(
        "Use an Apple Music playlist URL (music.apple.com/.../playlist/...) "
        "or a Spotify playlist URL (open.spotify.com/playlist/...)."
    )


def fetch_playlist(url: str) -> SourcePlaylist:
    source = detect_source(url)
    if source == "apple":
        return fetch_apple_playlist(url)
    return fetch_spotify_playlist(url)


def fetch_apple_playlist(url: str) -> SourcePlaylist:
    if not APPLE_ID.search(url):
        raise PlaylistError("That Apple Music URL does not include a playlist id.")
    html = _get(url)
    match = re.search(
        r'<script type="application/json" id="serialized-server-data">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise PlaylistError(
            "Apple Music did not include a track list on this page. "
            "The playlist may be private."
        )
    payload = json.loads(match.group(1))
    try:
        sections = payload["data"][0]["data"]["sections"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PlaylistError("Apple Music returned a playlist page I could not read.") from exc

    name = "Apple Music playlist"
    expected = None
    tracks: list[Track] = []
    for section in sections:
        for item in section.get("items") or []:
            if item.get("trackCount") and not tracks:
                name = item.get("title") or name
                expected = item.get("trackCount")
            descriptor = item.get("contentDescriptor") or {}
            if descriptor.get("kind") != "song":
                continue
            artist = item.get("artistName") or _link_titles(item.get("subtitleLinks"))
            album = _link_titles(item.get("tertiaryLinks")) or None
            title = item.get("title")
            if not title or not artist:
                continue
            tracks.append(
                Track(
                    title=title,
                    artist=artist,
                    album=album,
                    duration_ms=item.get("duration"),
                    url=(descriptor.get("url")),
                )
            )

    if not tracks:
        raise PlaylistError("No songs were found in that Apple Music playlist.")
    if expected is not None and len(tracks) < expected:
        raise PlaylistError(
            f"Apple Music only included {len(tracks)} of {expected} songs. "
            "A partial playlist was not created."
        )
    return SourcePlaylist(
        name=name,
        source="apple",
        url=url,
        tracks=tracks,
        expected_count=expected,
    )


def fetch_spotify_playlist(url: str) -> SourcePlaylist:
    match = SPOTIFY_ID.search(url)
    if not match:
        raise PlaylistError("That Spotify URL does not include a playlist id.")
    playlist_id = match.group(1)
    embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
    html = _get(embed_url)
    data_match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not data_match:
        raise PlaylistError("Spotify did not include a track list for this playlist.")
    payload = json.loads(data_match.group(1))
    try:
        entity = payload["props"]["pageProps"]["state"]["data"]["entity"]
    except (KeyError, TypeError) as exc:
        raise PlaylistError("Spotify returned a playlist page I could not read.") from exc
    if not isinstance(entity, dict):
        raise PlaylistError("Spotify returned a playlist page I could not read.")

    tracks = []
    for item in entity.get("trackList") or []:
        title = item.get("title")
        artist = item.get("subtitle")
        if not title or not artist:
            continue
        uri = item.get("uri") or ""
        track_url = None
        if uri.startswith("spotify:track:"):
            track_url = f"https://open.spotify.com/track/{uri.split(':')[-1]}"
        tracks.append(
            Track(
                title=title,
                artist=artist,
                duration_ms=item.get("duration"),
                url=track_url,
            )
        )
    if not tracks:
        raise PlaylistError(
            "No songs were found. The playlist may be private, empty, or unavailable."
        )
    return SourcePlaylist(
        name=entity.get("name") or entity.get("title") or "Spotify playlist",
        source="spotify",
        url=f"https://open.spotify.com/playlist/{playlist_id}",
        tracks=tracks,
    )


def _get(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PlaylistError(f"Could not open {url}: {exc}") from exc
    response.encoding = "utf-8"
    return response.text


def _link_titles(links: list | None) -> str:
    if not links:
        return ""
    titles = [link.get("title") for link in links if link.get("title")]
    return ", ".join(titles)
