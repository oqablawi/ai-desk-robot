# AI Desk Robot

A compact, stationary desktop robot companion with expressive screen eyes, voice interaction, and an AI assistant.

## Current status

**In progress — enclosure and hardware integration.**

The first functional head-shell foundation is now modeled in SolidWorks. It includes the rounded exterior, hollow 3 mm walls, an open service rear, and a centered display opening. Screen retention, Raspberry Pi mounts, ports, ventilation, neck connection, and rear-cover fasteners are still in progress.

The Raspberry Pi Zero 2 W has been purchased and is awaiting delivery. The remaining Phase 1 components, including the 3.5-inch display, are available for physical measurement and fit testing.

## Goals

- Build a reliable desk robot instead of a walking robot.
- Learn practical robotics, electronics, Python, audio, networking, CAD, and AI integration.
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
- [cad/Robot_Head_Main.SLDPRT](cad/Robot_Head_Main.SLDPRT) — current SolidWorks head-shell model
- [cad/head_rough_draft_1.SLDPRT](cad/head_rough_draft_1.SLDPRT) — original rough enclosure draft
- [src/](src/) — robot software

## Current CAD dimensions

- Head exterior: **120 × 90 × 52 mm**
- Wall thickness: **3 mm**
- Display opening: **74 × 49 mm**
- Display-opening corner radius: **2 mm**
- Rear: open for a later removable service cover

These are prototype dimensions. Mounts and connector openings will be based on measurements of the physical hardware before printing.

## Safety and privacy

Never commit API keys, passwords, private recordings, or local configuration files. Use environment variables and a local environment file ignored by Git.
