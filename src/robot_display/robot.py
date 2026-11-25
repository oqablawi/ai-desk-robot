"""Simple mode controller the AI (or a laptop demo) uses to drive the screen.

Safe to call set_mode() and say() from a background thread. Those calls
are queued, and the Tk display loop applies them with apply_pending().
"""
from __future__ import annotations

import queue
import time
from typing import Callable

from .ai import decide_mode
from .models import FACE_MODES, RobotState, normalize_mode

# Scripted laptop demo: what a short conversation will look like later.
# Each step is (seconds from start, mode, optional say-text, start playback).
DEMO_STEPS = (
    (0.0, "listening", None, False),
    (2.5, "thinking", None, False),
    (4.5, "speaking", "Here is a little desk music.", False),
    (7.5, "happy", None, False),
    (9.0, "music", None, True),
)
DEMO_END_SECONDS = 9.0


class Robot:
    """The object later AI code should hold and call."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.mode = "idle"
        self.spoken_text = ""
        # True when music appeared because a track started, not because
        # the AI or a keyboard shortcut chose the music screen.
        self.auto_music = False
        # True when Grok asked to stay on the face instead of auto-showing music.
        self.hold_mode = False
        self._commands: queue.Queue[tuple[str, str]] = queue.Queue()
        self._demo_started: float | None = None
        # Once the Tk window is up, only the display loop applies commands.
        self.use_queue_only = False

    @property
    def state(self) -> RobotState:
        return FACE_MODES.get(self.mode, RobotState.IDLE)

    @property
    def demo_running(self) -> bool:
        return self._demo_started is not None

    def attach_display(self) -> None:
        """Call this after the Tk window exists."""
        self.use_queue_only = True

    def set_mode(self, mode: str) -> None:
        """Show a face expression or the music screen.

        Safe to call from the AI thread or the Tk thread.
        """
        self._commands.put(("set_mode", normalize_mode(mode)))
        if not self.use_queue_only:
            self.apply_pending()

    def say(self, text: str) -> None:
        """Remember text and switch to the speaking face.

        The voice loop speaks these words out loud. The face design
        stays the same; the words are not drawn on the screen.
        """
        self._commands.put(("say", text))
        if not self.use_queue_only:
            self.apply_pending()

    def start_demo(self) -> None:
        """Run the scripted mode sequence on the laptop."""
        # Drop any leftover AI or keyboard commands so they cannot
        # immediately cancel the demo we are about to start.
        self._drain_queue()
        self._demo_started = self.clock()
        self.spoken_text = ""
        self._apply_mode("listening", from_demo=True)

    def cancel_demo(self) -> None:
        self._demo_started = None

    def apply_pending(self) -> None:
        """Apply queued set_mode/say calls. Run this from the Tk loop."""
        while True:
            try:
                action, value = self._commands.get_nowait()
            except queue.Empty:
                return
            # A live command from the AI or keyboard stops the demo.
            self.cancel_demo()
            if action == "say":
                self.spoken_text = value
                self._apply_mode("speaking")
            elif action == "set_mode":
                self._apply_mode(value)

    def update(self, playback=None, play: Callable[[], None] | None = None) -> None:
        """Apply commands, advance the scripted demo, then auto-show music."""
        self.apply_pending()
        self._advance_demo(play)
        if self.demo_running:
            return
        event = {
            "type": "playback",
            "is_playing": bool(playback and playback.is_playing),
            "has_track": playback is not None,
            "title": getattr(playback, "title", None),
            "current_mode": self.mode,
            "auto_music": self.auto_music,
            "hold_mode": self.hold_mode,
            "demo_running": False,
        }
        suggested = decide_mode(event)
        if suggested:
            if suggested == "music":
                self.auto_music = True
            self._apply_mode(suggested)

    def _advance_demo(self, play: Callable[[], None] | None) -> None:
        if self._demo_started is None:
            return
        elapsed = self.clock() - self._demo_started
        chosen = DEMO_STEPS[0]
        for step in DEMO_STEPS:
            if elapsed >= step[0]:
                chosen = step
        _start, mode, text, start_playback = chosen
        if text is not None:
            self.spoken_text = text
        self._apply_mode(mode, from_demo=True)
        if elapsed >= DEMO_END_SECONDS:
            self._demo_started = None
            if start_playback and play is not None:
                play()

    def _apply_mode(self, mode: str, from_demo: bool = False) -> None:
        self.mode = normalize_mode(mode)
        if self.mode == "music":
            self.hold_mode = False
            if not from_demo and not self.auto_music:
                # An explicit AI or keyboard request should stay on music
                # even if the track is later paused.
                self.auto_music = False
        else:
            self.auto_music = False

    def _drain_queue(self) -> None:
        while True:
            try:
                self._commands.get_nowait()
            except queue.Empty:
                return
