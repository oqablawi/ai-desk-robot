# Project Roadmap

## Phase 0 — Plan and prepare
- [x] Create repository
- [x] Define scope
- [x] Choose Raspberry Pi as primary computer
- [x] Purchase Phase 1 hardware
- [x] Start CAD enclosure development
- [ ] Start a project journal

## Phase 1 — Development setup
- [ ] Install Raspberry Pi OS
- [ ] Configure Wi-Fi and SSH
- [x] Create a Python virtual environment script
- [x] Add tests and safe configuration for secrets
- [ ] Add formatting and linting
- [ ] Flash and boot the Pi

## Phase 2 — Screen eyes
- [ ] Connect the display
- [x] Render the face in the laptop simulator
- [x] Add blinking and expressions
- [x] Add listening, thinking, talking, sleeping, and error states
- [ ] Confirm the face on the physical 480 × 320 screen

## Phase 3 — Hardware I/O
- [x] Add push-to-talk button code (GPIO 17, with a keyboard fallback)
- [ ] Connect the physical button and confirm it
- [ ] Add a status LED
- [ ] Test microphone input on the Pi
- [ ] Test speaker output on the Pi
- [x] Document wiring and pin assignments

## Phase 4 — Voice pipeline
- [x] Record audio (arecord, 16 kHz mono WAV)
- [x] Convert speech to text (xAI `/v1/stt`)
- [x] Generate a Grok response (`/v1/chat/completions`)
- [x] Convert text to speech (xAI `/v1/tts`, espeak-ng backup)
- [x] Add timeouts and useful error messages
- [ ] Validate the loop on the assembled Pi with a live key

## Phase 5 — Robot behavior
- [x] Add a mode controller (`Robot.set_mode` / `Robot.say`)
- [x] Synchronize eye animations with listening and speaking
- [x] Add idle and automatic music-screen behavior
- [x] Recover gracefully from missing Wi-Fi, key, or microphone

## Phase 6 — Physical build
- [x] Create basic head-shell CAD foundation
- [x] Draft a removable rear cover
- [ ] Measure screen thickness, rear components, mounting holes, and connectors
- [ ] Add screen retention features
- [ ] Add Raspberry Pi mounts, ports, ventilation, and neck connection
- [ ] Finish rear-cover fasteners
- [ ] Print and test-fit the enclosure
- [ ] Assemble the prototype

## Phase 7 — Portfolio release
- [ ] Add photos and a demonstration video
- [ ] Add a wiring diagram
- [ ] Write a technical project summary
- [ ] Record design decisions and lessons learned
- [ ] Prepare a resume-ready description
