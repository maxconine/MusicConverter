import unittest

from musicconverter.match import choose_match
from musicconverter.models import Track, TidalTrack
from musicconverter.sources import PlaylistError, detect_source


APPLE_HTML = """
<script type="application/json" id="serialized-server-data">{"data":[{"data":{"sections":[
  {"items":[{"title":"Balancing Club","trackCount":1}]},
  {"items":[{"title":"Voodoo Child (Slight Return)","artistName":"The Jimi Hendrix Experience","duration":312427,
    "contentDescriptor":{"kind":"song","url":"https://music.apple.com/us/album/voodoo"},
    "tertiaryLinks":[{"title":"Experience Hendrix"}]}]}
]}}]}</script>
"""

SPOTIFY_HTML = """
<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"state":{"data":{"entity":{"name":"Demo","trackList":[{"title":"Bass Persuades","subtitle":"Miley Cyrus","duration":202460,"uri":"spotify:track:abc"}]}}}}}}</script>
"""


class ParseTests(unittest.TestCase):
    def test_detects_apple_and_spotify(self):
        self.assertEqual(
            detect_source("https://music.apple.com/us/playlist/balancing-club/pl.u-WabZ14Acd98pZog"),
            "apple",
        )
        self.assertEqual(
            detect_source("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc"),
            "spotify",
        )
        with self.assertRaises(PlaylistError):
            detect_source("https://example.com/playlist/1")

    def test_parses_apple_playlist(self):
        playlist = fetch_apple_playlist_from_html()
        self.assertEqual(playlist.name, "Balancing Club")
        self.assertEqual(len(playlist.tracks), 1)
        self.assertEqual(playlist.tracks[0].artist, "The Jimi Hendrix Experience")
        self.assertEqual(playlist.tracks[0].album, "Experience Hendrix")
        self.assertEqual(playlist.tracks[0].duration_ms, 312427)

    def test_parses_spotify_playlist(self):
        playlist = fetch_spotify_playlist_from_html()
        self.assertEqual(playlist.name, "Demo")
        self.assertEqual(playlist.tracks[0].title, "Bass Persuades")
        self.assertEqual(playlist.tracks[0].url, "https://open.spotify.com/track/abc")

    def test_rejects_partial_apple_playlist(self):
        html = APPLE_HTML.replace('"trackCount":1', '"trackCount":4')
        with self.assertRaisesRegex(PlaylistError, "only included"):
            parse_apple(html)


class MatchTests(unittest.TestCase):
    def test_prefers_same_artist_over_a_cover(self):
        source = Track(
            title="Voodoo Child (Slight Return)",
            artist="The Jimi Hendrix Experience",
            album="Experience Hendrix",
            duration_ms=312_000,
        )
        cover = TidalTrack(
            id="1",
            title="Voodoo Child (Slight Return)",
            artist="Angus & Julia Stone",
            album="Covers",
            duration_ms=280_000,
        )
        original = TidalTrack(
            id="2",
            title="Voodoo Child (Slight Return)",
            artist="Jimi Hendrix",
            album="Electric Ladyland",
            duration_ms=312_400,
        )
        chosen, score = choose_match(source, [cover, original])
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.id, "2")
        self.assertGreater(score, 0.78)

    def test_rejects_a_weak_title(self):
        source = Track(title="Balancing Club", artist="Max Conine", duration_ms=180_000)
        other = TidalTrack(id="9", title="Club", artist="Someone Else", duration_ms=180_000)
        chosen, _score = choose_match(source, [other])
        self.assertIsNone(chosen)


def parse_apple(html: str):
    from musicconverter import sources

    original = sources._get
    sources._get = lambda url: html
    try:
        return sources.fetch_apple_playlist(
            "https://music.apple.com/us/playlist/balancing-club/pl.u-abc"
        )
    finally:
        sources._get = original


def fetch_apple_playlist_from_html():
    return parse_apple(APPLE_HTML)


def fetch_spotify_playlist_from_html():
    from musicconverter import sources

    original = sources._get
    sources._get = lambda url: SPOTIFY_HTML
    try:
        return sources.fetch_spotify_playlist("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")
    finally:
        sources._get = original


if __name__ == "__main__":
    unittest.main()
