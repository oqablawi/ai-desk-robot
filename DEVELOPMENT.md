# Desk robot laptop simulator

Develop the robot's screen and interaction flow while the remaining assembly supplies arrive. The interface uses a **480 × 320** coordinate grid and opens at **2× desktop zoom** (960 × 640) for easier viewing.

## Launch

On Windows, double-click **Start Robot Simulator.cmd**, or run this from the project folder:

```powershell
py -3 run_simulator.py
```

Python 3.10 or later with Tkinter is required. The standard python.org Windows installer includes Tcl/Tk. No pip packages, account, internet connection, microphone, or Raspberry Pi are needed.

Optional launch settings:

```powershell
py -3 run_simulator.py --scale 1
py -3 run_simulator.py --scale 3 --screen spotify
py -3 run_simulator.py --screen talk
```

`--scale 1` shows the native 480 × 320 layout. `--screen` accepts `eyes`, `spotify`, or `talk`. The package entry point still works with `src` on `PYTHONPATH`.

## Screens

- **Face:** seven animated expressions. Happy has open eyes and pink cheeks; other expressions have no blush. Thinking uses rotating dots. Click the arrows to change expressions.
- **Music:** three fictional tracks with original geometric covers. Click previous/next, pause/play, or anywhere on the progress bar to seek. Playback follows elapsed time, including time spent on other screens, and advances automatically at the end of each track.
- **Talk:** click **Try conversation** for a scripted listening → thinking → speaking → happy sequence. It then opens Music and resumes the simulated playback. Stop it with **Stop demo**, or leave the Talk screen to cancel it.

The header shows the laptop's local time. **DEMO** remains visible throughout. Music controls simulate playback; **there is no audio, Spotify login, microphone recording, speech recognition, or AI response generation in this simulator**. The conversation text is scripted. Click **?** for help.

## Keyboard controls

| Key | Action |
| --- | --- |
| E | Face screen |
| S | Music screen |
| 1–7 | Idle, listening, thinking, speaking, happy, sleeping, error; switches to Face |
| Left / Right | Previous/next expression on Face; previous/next song on Music |
| Space | Pause/resume demo music; start/stop conversation on Talk |
| T | Start or restart the conversation demo |
| H or ? | Open/close help |
| Esc | Close help if open; otherwise exit |

## Code map

- `src/robot_display/app.py`: Tkinter drawing, animation, desktop scaling, mouse and keyboard input.
- `src/robot_display/simulator.py`: conversation timing, screen changes, and cancellation.
- `src/robot_display/spotify.py`: elapsed-time demo playlist and the earlier, unfinished live API adapter.
- `src/robot_display/models.py`: expression names and immutable playback data.
- `run_simulator.py`: launcher that finds `src` relative to its own location.

## Verification

```powershell
$env:PYTHONPATH = "src"
py -3 -m unittest discover -s tests -v
```

Tests cover playback timing, pause/resume, track boundaries, seeking, scripted transitions and cancellation, mouse scaling, help isolation, expression rules, and text staying within the screen at 1×, 2×, and 3× zoom. Tk rendering tests skip on systems without a usable display.

## Raspberry Pi installation

After Raspberry Pi OS with Desktop is flashed and the repository is copied to the Pi:

```bash
cp .env.example .env
nano .env
bash scripts/install_pi.sh
sudo reboot
```

The default `.env.example` launches fullscreen at the screen's native 480 × 320 resolution. Set `ROBOT_MODE=spotify` only after Spotify login is complete.

### Spotify setup

1. Create a Spotify developer application.
2. Add `http://127.0.0.1:8765/callback` as its redirect URI (Spotify requires the explicit loopback IP, not `localhost`).
3. Put the Client ID in `.env`; no client secret is stored on the robot.
4. On a desktop session, run `PYTHONPATH=src .venv/bin/python -m robot_display --spotify-login`.
5. After approving access, change `ROBOT_MODE=spotify` and restart the service.

Tokens are stored in `.spotify-token.json`, which is ignored by Git. Requested permissions are limited to reading and controlling the current Spotify Connect playback. The Pi displays and controls playback on an existing Spotify device; it does not download or rebroadcast Spotify audio.

Useful service commands:

```bash
systemctl --user restart desk-robot
journalctl --user -u desk-robot -f
```

## Work remaining on real hardware

The desktop simulator is not a hardware fit or performance test. The actual display driver/touch mapping, USB audio devices, power, mounting clearances, and startup behavior still need testing on the assembled Pi.

Spotify authorization, token refresh, metadata, seek, play/pause and skip are implemented. Final validation still requires a Spotify developer app and an active Spotify Connect playback device. Album-art downloading is deliberately deferred until performance is measured on the Pi Zero 2 W.

The following require the physical parts and cannot be responsibly finalized in advance: HDMI rotation/overscan, touchscreen calibration, ALSA/PipeWire USB device names, speaker volume, microphone gain/noise, enclosure thermals, and GPIO features. Keep credentials and tokens out of Git.
