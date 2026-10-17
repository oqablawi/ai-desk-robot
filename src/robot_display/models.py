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

