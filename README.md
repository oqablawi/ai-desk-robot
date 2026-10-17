# AI Desk Robot

A compact, stationary desktop robot companion with expressive screen eyes, voice interaction, Spotify Now Playing information, and an AI assistant.

## Current status

**In progress — display software and enclosure integration.**

The first functional head-shell foundation is modeled in SolidWorks. It includes the rounded exterior, hollow 3 mm walls, open service rear, and centered display opening. Screen retention, Raspberry Pi mounts, ports, ventilation, neck connection, and rear-cover fasteners remain in progress.

A dependency-free Python display simulator now runs at the target screen resolution of 480 × 320. It includes animated eye states and a Spotify-style Now Playing demo. The Raspberry Pi Zero 2 W has been purchased and is awaiting delivery.

## Current software

- Animated blinking eyes
- Idle, listening, thinking, speaking, happy, sleeping, and error states
- Spotify-style song, artist, progress, and play/pause display
- Demo playback source that works without credentials
- Spotify Web API playback-state adapter ready for later PKCE authorization
- Unit tests for playback progress and time formatting

See [DEVELOPMENT.md](DEVELOPMENT.md) to run the simulator.

## Goals

- Build a reliable desk robot instead of a walking robot.
- Learn practical robotics, electronics, Python, audio, networking, CAD, and AI integration.
- Document the work for a portfolio and resume.

## Planned capabilities

- Animated screen eyes and expressions
- Push-to-talk voice interaction
- Speech-to-text and text-to-speech
- AI-generated responses
- Spotify Now Playing display
- Status lights and basic controls
- 3D-printed enclosure

## Repository map

- [ROADMAP.md](ROADMAP.md) — phased build plan
- [DEVELOPMENT.md](DEVELOPMENT.md) — run and test the display software
- [docs/hardware.md](docs/hardware.md) — parts and purchasing guidance
- [docs/architecture.md](docs/architecture.md) — software and hardware architecture
- [cad/Robot_Head_Main.SLDPRT](cad/Robot_Head_Main.SLDPRT) — current SolidWorks head-shell model
- [cad/head_rough_draft_1.SLDPRT](cad/head_rough_draft_1.SLDPRT) — original rough enclosure draft
- [src/robot_display/](src/robot_display/) — display application
- [tests/](tests/) — automated tests

## Current CAD dimensions

- Head exterior: **120 × 90 × 52 mm**
- Wall thickness: **3 mm**
- Display opening: **74 × 49 mm**
- Display-opening corner radius: **2 mm**
- Rear: open for a later removable service cover

These are prototype dimensions. Mounts and connector openings will be based on measurements of the physical hardware before printing.

## Safety and privacy

Never commit API keys, passwords, Spotify tokens, private recordings, or local configuration files. Use environment variables and a local environment file ignored by Git.
