# AI Desk Robot

A compact, stationary desktop robot companion with expressive screen eyes, push-to-talk voice, Spotify Now Playing, and a Grok AI assistant.

## Current status

**In progress — display software, mode controller, Grok voice loop, and enclosure CAD.**

The face from the November 20, 2026 redesign is the screen UI. There are no on-screen mode buttons. Grok (or a small set of automatic music rules) chooses the face expression or the music screen.

A dependency-free Python display simulator runs at 480 × 320. It includes animated eye states and a demo music screen. The Raspberry Pi Zero 2 W has been purchased. Screen retention, Raspberry Pi mounts, ports, ventilation, neck connection, and rear-cover fasteners remain in progress.

## Current software

- Animated blinking eyes (idle, listening, thinking, speaking, happy, sleeping, and error)
- A simple `Robot.set_mode()` / `Robot.say()` controller the AI thread can call
- Push-to-talk voice on the Pi: GPIO button (hold V on a laptop), USB mic, Grok reply, USB speaker
- Automatic music screen when Spotify reports a track and the robot is idle
- Demo playlist that works without Spotify credentials
- Scripted laptop demo (`--demo` or the T key) that walks through the modes
- Unit tests for playback, mode changes, and Grok reply parsing

## How the AI hook works

The voice loop records your words, transcribes them, and sends them to Grok. Grok returns a small JSON object, and the robot applies it:

```python
from robot_display import Robot, ask_grok

robot = Robot()
robot.set_mode("listening")
# ... record from the mic, convert speech to text ...
robot.set_mode("thinking")
reply = ask_grok("Play something mellow.", api_key)
# reply is like: {"mode": "happy", "show_music": True, "say": "Sure.", "music_action": "play"}
robot.say(reply.say)
if reply.show_music:
    robot.set_mode("music")
else:
    robot.set_mode(reply.mode)
```

`set_mode` and `say` are safe to call from a background thread. The display loop applies them.

Without an `XAI_API_KEY` or a microphone, the robot stays in demo mode: the face still runs, T plays the visual sequence, and a talk attempt gets a short canned reply.

## Run it on a laptop

Python 3.10 or later with Tkinter is required. No pip packages are needed.

```bash
python3 run_simulator.py
python3 run_simulator.py --demo
```

On Windows you can also double-click **Start Robot Simulator.cmd**. Hold V to talk if a mic and API key are available. Press H for the developer keyboard list.

## Raspberry Pi setup

```bash
cp .env.example .env
nano .env          # add XAI_API_KEY, and Spotify values if you use them
bash scripts/install_pi.sh
sudo reboot
```

The face starts with the desktop after login (auto-login is the Raspberry Pi OS default). Create a key at [https://console.x.ai](https://console.x.ai). Never commit the real `.env` file.

## Update an existing Pi

After this branch is on the Pi (or after it is merged to main):

```bash
cd ~/ai-desk-robot
git pull
bash scripts/install_pi.sh
# If .env.example gained new lines, copy those into your .env
sudo reboot
```

If you have not switched to this branch yet:

```bash
cd ~/ai-desk-robot
git fetch
git checkout ai-driven-modes
git pull
bash scripts/install_pi.sh
sudo reboot
```

## Voice and speech choices

The Pi Zero 2 W has limited memory, so speech runs in the cloud with the same `XAI_API_KEY`:

- Chat: `POST https://api.x.ai/v1/chat/completions` with model `grok-4.7` (change with `XAI_MODEL`)
- Speech-to-text: `POST https://api.x.ai/v1/stt`
- Text-to-speech: `POST https://api.x.ai/v1/tts` (voice `eve` by default)

Recording uses `arecord`. Playback uses `aplay`. If the xAI TTS call fails, `espeak-ng` is an offline backup. No extra pip packages are required.

## Planned capabilities

- Animated screen eyes and expressions
- Push-to-talk voice interaction
- Speech-to-text and text-to-speech
- Grok-generated responses that also pick the screen mode
- Spotify Now Playing display
- Status lights and basic controls
- 3D-printed enclosure

## Repository map

- [ROADMAP.md](ROADMAP.md) — phased build plan
- [DEVELOPMENT.md](DEVELOPMENT.md) — run, test, and install details
- [docs/hardware.md](docs/hardware.md) — parts, mini-HDMI, and button wiring
- [docs/architecture.md](docs/architecture.md) — software and hardware architecture
- [cad/Robot_Head_Main.SLDPRT](cad/Robot_Head_Main.SLDPRT) — current SolidWorks head-shell model
- [cad/Robot_Head_Back_Cover.SLDPRT](cad/Robot_Head_Back_Cover.SLDPRT) — rear cover draft
- [src/robot_display/](src/robot_display/) — display, voice, and Grok code
- [tests/](tests/) — automated tests

## Current CAD dimensions

- Head exterior: **120 × 90 × 52 mm**
- Wall thickness: **3 mm**
- Display opening: **74 × 49 mm**
- Display-opening corner radius: **2 mm**
- Rear cover part exists; mounts and fasteners are still being refined

These are prototype dimensions. Measure the physical screen and Pi before printing.

## Safety and privacy

Never commit API keys, passwords, Spotify tokens, private recordings, or local configuration files. Use environment variables and a local `.env` file ignored by Git.
