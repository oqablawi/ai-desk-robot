# Desk robot laptop simulator

Develop the robot's screen and voice flow while the remaining assembly supplies arrive. The interface uses a **480 × 320** coordinate grid and opens at **2× desktop zoom** (960 × 640) for easier viewing. The November 20 face redesign is the full-screen UI. There are no on-screen mode buttons.

## Launch

On Windows, double-click **Start Robot Simulator.cmd**, or run this from the project folder:

```powershell
py -3 run_simulator.py
py -3 run_simulator.py --demo
```

```bash
python3 run_simulator.py
python3 run_simulator.py --demo
python3 run_simulator.py --scale 1 --screen music
```

Python 3.10 or later with Tkinter is required. The standard python.org Windows installer includes Tcl/Tk. No pip packages are required. The demo playlist works without Spotify or an xAI key. Voice replies need `XAI_API_KEY` in a local `.env` file, plus a microphone.

`--screen` accepts a face mode (`idle`, `listening`, and so on) or `music`. `--demo` plays the scripted mode sequence on launch.

## Screens

- **Face:** seven animated expressions. Happy has open eyes and pink cheeks; other expressions have no blush. Thinking uses rotating dots. The AI (or a developer key) chooses the expression.
- **Music:** shown when Grok asks for it, when you press S, or automatically when a track is playing and the robot is idle. Demo mode has three fictional tracks with geometric covers. Live Spotify shows the real title and artist. Album art from JPEG images is not drawn yet (Tk cannot open JPEG without a new package).

The T key runs a scripted conversation on the face, then opens Music. Hold V (or the GPIO button on the Pi) for a real or demo voice turn. Press H for the developer key list. Esc exits.

## Keyboard controls (developer fallback)

| Key | Action |
| --- | --- |
| Hold V or P | Push-to-talk |
| E / S | Face / music screen |
| 1–7 | Idle, listening, thinking, speaking, happy, sleeping, error |
| Left / Right | Previous/next expression on the face; previous/next song on Music |
| Space | Pause or resume demo or Spotify playback |
| T | Run the scripted mode demo |
| H or ? | Open or close help |
| Esc | Close help if open; otherwise exit |

## Code map

- `src/robot_display/app.py`: Tkinter drawing, animation, desktop scaling, and key input.
- `src/robot_display/robot.py`: `Robot.set_mode()` and `Robot.say()`, plus the scripted demo timings.
- `src/robot_display/ai.py`: Grok chat, JSON parsing, and automatic music-screen rules.
- `src/robot_display/voice.py`: push-to-talk, GPIO, recording, speech-to-text, and speech out.
- `src/robot_display/spotify.py`: elapsed-time demo playlist and the live API adapter.
- `run_simulator.py`: launcher that finds `src` relative to its own location.

## Verification

```powershell
$env:PYTHONPATH = "src"
py -3 -m unittest discover -s tests -v
```

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Non-Tk tests cover playback timing, mode switching, automatic music rules, Grok JSON parsing, and demo replies. Tk rendering tests skip on systems without a usable display.

## Raspberry Pi installation

After Raspberry Pi OS with Desktop is flashed and the repository is copied to the Pi:

```bash
cp .env.example .env
nano .env
bash scripts/install_pi.sh
sudo reboot
```

The default `.env.example` launches fullscreen at the screen's native 480 × 320 resolution. The install script adds a desktop autostart entry so the face starts after login. It also installs `python3-gpiozero`, `alsa-utils`, and `espeak-ng`.

To update a Pi that already has the project:

```bash
cd ~/ai-desk-robot
git pull
bash scripts/install_pi.sh
sudo reboot
```

### Voice setup

1. Create an API key at [https://console.x.ai](https://console.x.ai).
2. Put it in `.env` as `XAI_API_KEY`. Never commit that file.
3. Plug in the USB microphone and speaker, ideally through a powered hub.
4. Wire a momentary button between BCM GPIO 17 (physical pin 11) and ground, or hold V on a keyboard.
5. The same key is used for chat, speech-to-text, and text-to-speech. The default chat model is `grok-4.7`. Change it with `XAI_MODEL` if you want a different Grok model.

If the key is missing, a talk attempt uses a short demo reply. If the microphone is missing, the robot says so and returns to an error or happy face. If cloud TTS fails, it tries `espeak-ng`.

### Spotify setup

1. Create a Spotify developer application.
2. Add `http://127.0.0.1:8765/callback` as its redirect URI (Spotify requires the explicit loopback IP, not `localhost`).
3. Put the Client ID in `.env`; no client secret is stored on the robot.
4. On a desktop session, run `PYTHONPATH=src .venv/bin/python -m robot_display --spotify-login`.
5. After approving access, change `ROBOT_MODE=spotify` and restart.

Tokens are stored in `.spotify-token.json`, which is ignored by Git. Requested permissions are limited to reading and controlling the current Spotify Connect playback. The Pi displays and controls playback on an existing Spotify device; it does not download or rebroadcast Spotify audio.

Useful service commands if you opt into the backup systemd unit:

```bash
systemctl --user restart desk-robot
journalctl --user -u desk-robot -f
```

## Work remaining on real hardware

The desktop simulator is not a hardware fit or performance test. The actual display driver, USB audio devices, power, mounting clearances, and startup behavior still need testing on the assembled Pi.

Spotify authorization, token refresh, metadata, seek, play/pause and skip are implemented in the adapter. Final validation still requires a Spotify developer app and an active Spotify Connect playback device. Album-art downloading is deferred until we can decode JPEG images without a new package.

The following need the physical parts: HDMI rotation or overscan, ALSA USB device names, speaker volume, microphone gain, enclosure thermals, and the GPIO button. Keep credentials and tokens out of Git.
