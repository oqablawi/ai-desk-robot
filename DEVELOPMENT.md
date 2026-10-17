# Local display development

The display simulator targets the Waveshare 480 × 320 screen but can be run on Windows before the Raspberry Pi arrives.

## Run it

From PowerShell in the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m robot_display
```

Controls:

- `E`: animated robot eyes
- `S`: Spotify-style Now Playing screen
- `Space`: toggle demo play/pause
- `1`–`7`: idle, listening, thinking, speaking, happy, sleeping, and error eye states
- `Esc`: close

## Spotify integration plan

The initial application uses a local demo provider, so no account or credentials are required. The production provider will use Spotify's Authorization Code with PKCE flow and the `user-read-playback-state` scope. Tokens and client configuration must remain local and must never be committed.

The `SpotifyWebApiProvider` already translates the official `/v1/me/player` response into the application's display model. PKCE authorization, refresh-token storage, album-art downloading, and rate-limit handling remain to be implemented.

## Run tests

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

