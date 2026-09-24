# Copy a playlist to Tidal

This creates a playlist in a Tidal account from a public Apple Music or Spotify playlist. It searches Tidal for the same songs and adds the ones it finds. It does not download music.

You need:

- A Tidal account
- Python 3, from [python.org/downloads](https://www.python.org/downloads/)
- A playlist link

On Mac, Python may already be installed. On Windows, during the Python install, turn on **Add python.exe to PATH**.

## Mac

1. Unzip this folder if it arrived as a zip file.
2. Open **Terminal**.
3. Type `cd ` with a space after it, drag the MusicConverter folder onto the Terminal window, and press Return.
4. Run:

```bash
bash convert
```

5. Paste the playlist link and press Return.
6. A browser window opens. Log in to the Tidal account that should receive the playlist and allow access. Do this within 5 minutes, and leave Terminal open.
7. Wait while each song is matched. At the end, Terminal prints a Tidal link. Open it. The playlist is also in that Tidal account's library.

## Windows

1. Unzip this folder if it arrived as a zip file.
2. Open **Command Prompt**.
3. Type `cd ` with a space after it, drag the MusicConverter folder onto the Command Prompt window, and press Enter.
4. Run:

```bat
convert.bat
```

5. Paste the playlist link and press Enter.
6. A browser window opens. Log in to the Tidal account that should receive the playlist and allow access. Do this within 5 minutes, and leave Command Prompt open.
7. Wait while each song is matched. At the end, the window prints a Tidal link. Open it. The playlist is also in that Tidal account's library.

You can also double-click `convert.bat`. The window stays open when it finishes.

## Playlist link

Copy the link from the browser while the playlist is open.

- Apple Music looks like `https://music.apple.com/.../playlist/...`
- Spotify looks like `https://open.spotify.com/playlist/...`

The playlist has to be public. A private Apple Music playlist will not include its songs. A very long Spotify playlist sometimes comes through with only the songs Spotify shows on its public page.

Example:

```text
https://music.apple.com/us/playlist/balancing-club/pl.u-WabZ14Acd98pZog
```

## What you should see

The window lists each song as it searches. When it finishes, it prints how many songs were added. Songs Tidal does not have are listed under **Not added**.

The first run asks you to log in. Later runs reuse that login.

## If something goes wrong

**The login link expired.** Run `bash convert` (Mac) or `convert.bat` (Windows) again, and allow access within 5 minutes.

**Python 3 is not installed.** Install it from [python.org/downloads](https://www.python.org/downloads/), then run the command again. On Windows, turn on **Add python.exe to PATH** in the installer.

**No songs were found.** Check that the link is a playlist, not an album or a song, and that the playlist is public.

**A song was skipped.** Tidal may not carry that recording. The list at the end shows which ones were left out.
# MusicConverter
