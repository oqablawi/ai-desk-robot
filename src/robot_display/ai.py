"""Grok AI helpers and automatic music-screen rules.

ask_grok() talks to the xAI Chat Completions API. decide_mode() only
handles automatic Spotify screen changes while the robot is idle.
The voice loop calls ask_grok(), then robot.set_mode() and robot.say().
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from .models import normalize_mode

DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.7"
DEFAULT_STT_MODEL = "grok-voice-transcribe-2.0"
DEFAULT_TTS_VOICE = "eve"

MUSIC_ACTIONS = ("none", "play", "pause", "skip_next", "skip_prev")

SYSTEM_PROMPT = """You are a compact desk robot companion. Speak in short, friendly sentences (one or two).

Always reply with ONLY a JSON object, no markdown and no extra text:
{"mode":"idle","show_music":false,"say":"your spoken words","music_action":"none"}

Rules:
- "say" is the exact sentence you will speak out loud. Keep it short.
- "mode" is the face to show after you finish speaking. Use one of: idle, listening, thinking, speaking, happy, sleeping, error, music. Use happy for a normal reply, error if something is wrong, sleeping only if asked to rest or sleep.
- Set show_music to true only when the user wants to see or change music, or asks what is playing.
- music_action must be one of: none, play, pause, skip_next, skip_prev. Use none unless they asked to play, pause, or skip.
"""


@dataclass
class GrokReply:
    mode: str = "happy"
    show_music: bool = False
    say: str = ""
    music_action: str = "none"


def decide_mode(event: dict) -> str | None:
    """Return a mode name, or None to leave the current mode alone.

    event is a plain dictionary. Typical keys:

        type          "playback", "speech", "button", ...
        current_mode  the mode on screen right now
        is_playing    True if Spotify or the demo track is playing
        has_track     True if there is a current track at all
        auto_music    True if the music screen was shown automatically
        hold_mode     True if Grok asked to stay off the music screen
        demo_running  True during the laptop scripted demo
        text          spoken words, when type is "speech"
    """
    kind = event.get("type")
    current = event.get("current_mode")

    # A live conversation or the scripted demo owns the screen.
    if event.get("demo_running"):
        return None

    if kind == "playback":
        if event.get("hold_mode"):
            if current == "music" and event.get("auto_music") and not event.get("is_playing"):
                return "idle"
            return None
        if event.get("is_playing") and current == "idle":
            return "music"
        if current == "music" and event.get("auto_music") and not event.get("is_playing"):
            return "idle"

    return None


def parse_reply(text: str) -> GrokReply:
    """Turn Grok's text into a GrokReply. Also accepts a bare sentence."""
    if not text or not text.strip():
        return GrokReply(say="I am not sure what to say.")
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return GrokReply(say=_shorten(cleaned), mode="happy")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return GrokReply(say=_shorten(cleaned), mode="happy")
    if not isinstance(data, dict):
        return GrokReply(say=_shorten(cleaned), mode="happy")

    raw_mode = str(data.get("mode") or "happy")
    try:
        mode = normalize_mode(raw_mode)
    except ValueError:
        mode = "happy"

    action = str(data.get("music_action") or "none").strip().lower()
    if action not in MUSIC_ACTIONS:
        action = "none"

    say = data.get("say")
    if say is None:
        say = data.get("text") or ""
    say = _shorten(str(say).strip()) or "Okay."

    show_music = bool(data.get("show_music")) or mode == "music" or action in {
        "play", "pause", "skip_next", "skip_prev",
    }
    return GrokReply(mode=mode, show_music=show_music, say=say, music_action=action)


def demo_reply(user_text: str) -> GrokReply:
    """Used when no XAI_API_KEY is set, so the laptop still has a voice path."""
    text = (user_text or "").lower()
    if any(word in text for word in ("music", "song", "spotify", "play", "track")):
        return GrokReply(
            mode="music",
            show_music=True,
            say="Here is a little desk music.",
            music_action="play",
        )
    return GrokReply(
        mode="happy",
        show_music=False,
        say="I am in demo mode. Add an XAI API key in the .env file so I can really talk.",
        music_action="none",
    )


def ask_grok(
    user_text: str,
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    playback=None,
    history: list[tuple[str, str]] | None = None,
) -> GrokReply:
    """Send the user's words to Grok and parse a GrokReply.

    If there is no API key, return a demo reply instead of failing.
    """
    if not api_key:
        return demo_reply(user_text)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for asked, answered in (history or [])[-4:]:
        messages.append({"role": "user", "content": asked})
        messages.append({"role": "assistant", "content": answered})
    messages.append({"role": "user", "content": _user_payload(user_text, playback)})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.6,
    }).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return GrokReply(
            mode="error",
            say="I had trouble reaching Grok. Check the Wi-Fi and API key.",
        )

    try:
        content = payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return GrokReply(mode="error", say="I got a reply I could not read.")
    return parse_reply(content)


def transcribe_audio(
    path,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_STT_MODEL,
) -> str:
    """Send a WAV recording to the xAI speech-to-text API. Returns text."""
    import secrets
    from pathlib import Path

    wav_path = Path(path)
    data = wav_path.read_bytes()
    boundary = "----RobotBoundary" + secrets.token_hex(8)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"{model}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{wav_path.name}"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/stt",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return str(payload.get("text") or "").strip()


def synthesize_speech(
    text: str,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    voice: str = DEFAULT_TTS_VOICE,
) -> bytes:
    """Return WAV (or MP3) bytes from the xAI text-to-speech API."""
    body = json.dumps({
        "text": text,
        "voice_id": voice,
        "language": "en",
        "output_format": {"codec": "wav", "sample_rate": 24000},
    }).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/tts",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _user_payload(user_text: str, playback) -> str:
    lines = [f"User said: {user_text.strip()}"]
    if playback is not None:
        status = "playing" if getattr(playback, "is_playing", False) else "paused"
        title = getattr(playback, "title", "Unknown")
        artist = getattr(playback, "artist", "Unknown")
        lines.insert(0, f"Now playing: {title} by {artist} ({status})")
    return "\n".join(lines)


def _shorten(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "."
