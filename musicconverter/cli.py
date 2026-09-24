import argparse
import json
import sys
from pathlib import Path

from musicconverter.sources import PlaylistError, fetch_playlist
from musicconverter.tidal_export import connect, create_tidal_playlist, match_playlist


def default_session_path() -> Path:
    return Path.home() / ".config" / "musicconverter" / "tidal-session.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an Apple Music or Spotify playlist into a Tidal playlist."
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Apple Music or Spotify playlist URL. You will be asked for it if you leave this out.",
    )
    parser.add_argument("--name", help="Name for the new Tidal playlist")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read the source playlist and print its tracks without using Tidal",
    )
    parser.add_argument(
        "--session",
        type=Path,
        default=default_session_path(),
        help="Where to store the Tidal login session",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Write a JSON report of matches and misses",
    )
    return parser


def format_duration(duration_ms: int | None) -> str:
    if not duration_ms:
        return ""
    seconds = round(duration_ms / 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def print_source(playlist) -> None:
    print(f"{playlist.name} ({len(playlist.tracks)} songs from {playlist.source})")
    for index, track in enumerate(playlist.tracks, start=1):
        duration = format_duration(track.duration_ms)
        suffix = f" [{duration}]" if duration else ""
        album = f" — {track.album}" if track.album else ""
        print(f"{index:2}. {track.artist} — {track.title}{album}{suffix}")


def report_payload(playlist, matches, tidal_url: str | None) -> dict:
    rows = []
    for match in matches:
        row = {
            "title": match.source.title,
            "artist": match.source.artist,
            "album": match.source.album,
            "matched": match.tidal is not None,
            "score": round(match.score, 3),
        }
        if match.tidal:
            row["tidal"] = {
                "id": match.tidal.id,
                "title": match.tidal.title,
                "artist": match.tidal.artist,
                "album": match.tidal.album,
                "url": match.tidal.url,
            }
        rows.append(row)
    return {
        "name": playlist.name,
        "source": playlist.source,
        "url": playlist.url,
        "tidal_url": tidal_url,
        "matched": sum(1 for row in rows if row["matched"]),
        "total": len(rows),
        "tracks": rows,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    args = build_parser().parse_args(argv)
    if not args.url:
        print("Paste an Apple Music or Spotify playlist link, then press Return.")
        try:
            args.url = input("Playlist link: ").strip()
        except EOFError:
            args.url = ""
    if not args.url:
        print("No playlist link was entered.", file=sys.stderr)
        return 1
    try:
        playlist = fetch_playlist(args.url)
    except PlaylistError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.dry_run:
        print_source(playlist)
        return 0

    try:
        session = connect(args.session)
    except PlaylistError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Signed in. Matching {len(playlist.tracks)} songs on Tidal. This can take a minute.")
    print()
    matches = match_playlist(session, playlist)
    matched = [match for match in matches if match.tidal]
    missed = [match for match in matches if not match.tidal]
    tidal_url = None
    try:
        tidal_url = create_tidal_playlist(session, playlist, matches, name=args.name)
    except PlaylistError as exc:
        print(exc, file=sys.stderr)
        return 1

    print()
    print(f"Created Tidal playlist: {tidal_url}")
    print(f"Added {len(matched)} of {len(playlist.tracks)} songs.")
    if missed:
        print("Not added:")
        for match in missed:
            print(f"  {match.source.artist} — {match.source.title}")
    if args.report:
        args.report.write_text(json.dumps(report_payload(playlist, matches, tidal_url), indent=2))
        print(f"Report written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
