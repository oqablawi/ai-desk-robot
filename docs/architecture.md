# System Architecture

## High-level flow

```
Hold GPIO button or V key
          |
          v
      USB microphone
          |
          v
  Speech-to-text (xAI /v1/stt)
          |
          v
  Grok chat (xAI /v1/chat/completions)
  returns JSON: mode, show_music, say
          |
          v
  Text-to-speech (xAI /v1/tts)
          |
          v
      USB speaker

Raspberry Pi display states:
idle -> listening -> thinking -> speaking -> happy or music
```

If a Spotify track starts while the robot is idle, the music screen appears on its own. A talking mode or a Grok reply with show_music set to false returns to the face.

## Modules

- `robot.py` — `Robot.set_mode()` and `Robot.say()`, safe to call from a background thread
- `ai.py` — `ask_grok()`, JSON parsing, and automatic music-screen rules
- `voice.py` — push-to-talk, recording, speech-to-text, speech out, GPIO
- `app.py` — Tkinter face and music screens
- `spotify.py` — demo playlist and live Spotify Web API adapter
- `config.py` — environment variables and the local `.env` file
- `hardware.py` is not used yet; GPIO lives in `voice.py` for the first version

## Design principles
- Keep hardware drivers separate from AI services.
- Give every external request a timeout.
- Never hard-code API keys.
- Make modules testable on a normal computer where possible.
- Prefer push-to-talk for the first version.
- Keep the robot useful when the AI service is unavailable (demo replies and the T-key visual demo).
