from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RobotState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    HAPPY = "happy"
    SLEEPING = "sleeping"
    ERROR = "error"


@dataclass(frozen=True)
class PlaybackInfo:
    title: str
    artist: str
    duration_ms: int
    progress_ms: int
    is_playing: bool
    album_art_url: str | None = None

    @property
    def progress_fraction(self) -> float:
        if self.duration_ms <= 0:
            return 0.0
        return min(1.0, max(0.0, self.progress_ms / self.duration_ms))

    @staticmethod
    def format_time(milliseconds: int) -> str:
        seconds = max(0, milliseconds // 1000)
        return f"{seconds // 60}:{seconds % 60:02d}"



# Face expressions, plus the music screen.
FACE_MODES = {
    "idle": RobotState.IDLE,
    "listening": RobotState.LISTENING,
    "thinking": RobotState.THINKING,
    "speaking": RobotState.SPEAKING,
    "happy": RobotState.HAPPY,
    "sleeping": RobotState.SLEEPING,
    "error": RobotState.ERROR,
}
MODES = (*FACE_MODES, "music")

# Older names still accepted so earlier scripts keep working.
MODE_ALIASES = {
    "eyes": "idle",
    "face": "idle",
    "spotify": "music",
}


def normalize_mode(mode: str) -> str:
    name = mode.strip().lower()
    name = MODE_ALIASES.get(name, name)
    if name not in MODES:
        allowed = ", ".join(MODES)
        raise ValueError(f"Unknown mode: {mode}. Use one of: {allowed}")
    return name
