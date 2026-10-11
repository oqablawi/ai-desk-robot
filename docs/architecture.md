# System Architecture

## High-level flow

```
Push button or voice trigger
          |
          v
      Audio input
          |
          v
    Speech-to-text
          |
          v
       AI service
          |
          v
    Text-to-speech
          |
          v
       Speaker

Raspberry Pi display states:
idle -> listening -> thinking -> speaking -> idle
```

## Proposed modules
- `display.py` — eyes, expressions, and animations
- `audio_input.py` — microphone recording
- `speech.py` — speech-to-text and text-to-speech adapters
- `assistant.py` — AI conversation interface
- `hardware.py` — buttons, LEDs, and GPIO
- `main.py` — application loop and coordination
- `config.py` — environment variables and safe configuration

## Design principles
- Keep hardware drivers separate from AI services.
- Give every external request a timeout.
- Never hard-code API keys.
- Make modules testable on a normal computer where possible.
- Prefer push-to-talk for the first version.
- Keep the robot useful when the AI service is unavailable.
