# AI Desk Robot

A compact, stationary desktop robot companion with expressive screen eyes, voice interaction, and an AI assistant.

## Current status

**In progress — enclosure and hardware integration.**

The current prototype is focused on the robot head: a small SolidWorks-designed enclosure for a 3.5-inch display, microphone, speaker, and Raspberry Pi-based controller. The Raspberry Pi Zero 2 W is not yet installed, so the software and electronics integration are being developed incrementally.

## Goals

- Build a reliable desk robot instead of a walking robot.
- Learn practical robotics, electronics, Python, audio, networking, and AI integration.
- Document the work for a portfolio and resume.

## Planned capabilities

- Animated screen eyes and expressions
- Push-to-talk voice interaction
- Speech-to-text and text-to-speech
- AI-generated responses
- Status lights and basic controls
- 3D-printed enclosure

## Repository map

- [ROADMAP.md](ROADMAP.md) — phased build plan
- [docs/hardware.md](docs/hardware.md) — parts and purchasing guidance
- [docs/architecture.md](docs/architecture.md) — software and hardware architecture
- [src/](src/) — robot software

## Design notes

The first enclosure concept uses a removable rear cover so the electronics remain serviceable. The front head shell is designed around a 100 x 78 x 30 mm envelope with a centered 82 x 54 mm display opening. Dimensions will be revised after the physical display and electronics are test-fitted.

## Safety and privacy

Never commit API keys, passwords, private recordings, or local configuration files. Use environment variables and a local environment file ignored by Git.
