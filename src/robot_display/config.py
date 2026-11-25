from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Load a tiny KEY=VALUE file without adding a runtime dependency."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RobotConfig:
    mode: str = "demo"
    fullscreen: bool = False
    scale: int = 2
    start_screen: str = "idle"
    spotify_client_id: str | None = None
    spotify_redirect_uri: str = "http://127.0.0.1:8765/callback"
    spotify_token_file: Path = Path(".spotify-token.json")
    xai_api_key: str | None = None
    xai_model: str = "grok-4.7"
    xai_base_url: str = "https://api.x.ai/v1"
    xai_tts_voice: str = "eve"
    ptt_pin: int = 17

    @classmethod
    def from_environment(cls) -> "RobotConfig":
        load_dotenv()
        mode = os.getenv("ROBOT_MODE", "demo").lower()
        screen = os.getenv("ROBOT_START_SCREEN", "idle").lower()
        # Older names from earlier builds.
        screen = {"eyes": "idle", "face": "idle", "spotify": "music", "talk": "idle"}.get(screen, screen)
        scale = int(os.getenv("ROBOT_SCALE", "2"))
        if mode not in {"demo", "spotify"}:
            raise ValueError("ROBOT_MODE must be demo or spotify")
        allowed_screens = {"idle", "listening", "thinking", "speaking", "happy", "sleeping", "error", "music"}
        if screen not in allowed_screens:
            raise ValueError("ROBOT_START_SCREEN must be a face mode or music")
        if scale not in {1, 2, 3}:
            raise ValueError("ROBOT_SCALE must be 1, 2 or 3")
        return cls(
            mode=mode,
            fullscreen=_boolean("ROBOT_FULLSCREEN", False),
            scale=scale,
            start_screen=screen,
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID") or None,
            spotify_redirect_uri=os.getenv(
                "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8765/callback"
            ),
            spotify_token_file=Path(os.getenv("SPOTIFY_TOKEN_FILE", ".spotify-token.json")),
            xai_api_key=os.getenv("XAI_API_KEY") or None,
            xai_model=os.getenv("XAI_MODEL", "grok-4.7"),
            xai_base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
            xai_tts_voice=os.getenv("XAI_TTS_VOICE", "eve"),
            ptt_pin=int(os.getenv("ROBOT_PTT_PIN", "17")),
        )
