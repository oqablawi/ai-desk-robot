from __future__ import annotations

import math
import random
import time
import tkinter as tk

from .models import PlaybackInfo, RobotState
from .spotify import DemoSpotifyProvider, PlaybackProvider


WIDTH = 480
HEIGHT = 320
BACKGROUND = "#071018"
CYAN = "#41F6FF"
MUTED = "#66808C"
WHITE = "#ECF7FA"


class RobotDisplayApp:
    def __init__(self, provider: PlaybackProvider | None = None) -> None:
        self.root = tk.Tk()
        self.root.title("AI Desk Robot Display Simulator")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=BACKGROUND)
        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.provider = provider or DemoSpotifyProvider()
        self.mode = "eyes"
        self.state = RobotState.IDLE
        self.started = time.monotonic()
        self.last_blink = self.started
        self.next_blink = random.uniform(2.5, 5.0)
        self.blink_started: float | None = None
        self.playback: PlaybackInfo | None = None
        self.last_playback_update = 0.0

        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("e", lambda _event: self.set_mode("eyes"))
        self.root.bind("s", lambda _event: self.set_mode("spotify"))
        self.root.bind("<space>", self.toggle_demo_playback)
        self.root.bind("1", lambda _event: self.set_state(RobotState.IDLE))
        self.root.bind("2", lambda _event: self.set_state(RobotState.LISTENING))
        self.root.bind("3", lambda _event: self.set_state(RobotState.THINKING))
        self.root.bind("4", lambda _event: self.set_state(RobotState.SPEAKING))
        self.root.bind("5", lambda _event: self.set_state(RobotState.HAPPY))
        self.root.bind("6", lambda _event: self.set_state(RobotState.SLEEPING))
        self.root.bind("7", lambda _event: self.set_state(RobotState.ERROR))

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def set_state(self, state: RobotState) -> None:
        self.state = state

    def toggle_demo_playback(self, _event: tk.Event | None = None) -> None:
        toggle = getattr(self.provider, "toggle_playback", None)
        if toggle:
            toggle()

    def run(self) -> None:
        self._frame()
        self.root.mainloop()

    def _frame(self) -> None:
        now = time.monotonic()
        self.canvas.delete("all")
        if self.mode == "spotify":
            self._draw_spotify(now)
        else:
            self._draw_eyes(now)
        self._draw_mode_hint()
        self.root.after(33, self._frame)

    def _blink_amount(self, now: float) -> float:
        if self.state == RobotState.SLEEPING:
            return 1.0
        if self.blink_started is None and now - self.last_blink >= self.next_blink:
            self.blink_started = now
        if self.blink_started is None:
            return 0.0
        elapsed = now - self.blink_started
        if elapsed >= 0.22:
            self.last_blink = now
            self.next_blink = random.uniform(2.5, 5.0)
            self.blink_started = None
            return 0.0
        return math.sin((elapsed / 0.22) * math.pi)

    def _draw_eyes(self, now: float) -> None:
        blink = self._blink_amount(now)
        pulse = (math.sin((now - self.started) * 2.0) + 1.0) / 2.0
        colors = {
            RobotState.ERROR: "#FF5364",
            RobotState.THINKING: "#B68CFF",
            RobotState.LISTENING: "#54FFB5",
        }
        color = colors.get(self.state, CYAN)

        for cx in (155, 325):
            width = 92 + (8 * pulse if self.state == RobotState.LISTENING else 0)
            height = max(5, 82 * (1.0 - blink))
            top = 160 - height / 2
            bottom = 160 + height / 2
            self.canvas.create_oval(
                cx - width / 2,
                top,
                cx + width / 2,
                bottom,
                fill=color,
                outline="",
            )
            pupil = 30 if self.state != RobotState.HAPPY else 18
            self.canvas.create_oval(
                cx - pupil / 2,
                160 - max(2, pupil * (1.0 - blink)) / 2,
                cx + pupil / 2,
                160 + max(2, pupil * (1.0 - blink)) / 2,
                fill=BACKGROUND,
                outline="",
            )

        label = self.state.value.upper()
        self.canvas.create_text(240, 265, text=label, fill=MUTED, font=("Segoe UI", 10, "bold"))

    def _draw_spotify(self, now: float) -> None:
        if now - self.last_playback_update >= 1.0 or self.playback is None:
            self.playback = self.provider.current()
            self.last_playback_update = now

        track = self.playback
        if track is None:
            self.canvas.create_text(240, 142, text="Nothing playing", fill=WHITE, font=("Segoe UI", 22, "bold"))
            self.canvas.create_text(240, 181, text="Start Spotify on one of your devices", fill=MUTED, font=("Segoe UI", 11))
            return

        # Album-art placeholder. Real downloaded artwork is added with OAuth integration.
        self.canvas.create_rectangle(28, 36, 204, 212, fill="#17394A", outline="#2B657B", width=2)
        self.canvas.create_oval(63, 71, 169, 177, fill="#0A202B", outline=CYAN, width=5)
        self.canvas.create_oval(102, 110, 130, 138, fill=CYAN, outline="")

        self.canvas.create_text(228, 54, text=track.title, anchor="nw", width=225, fill=WHITE, font=("Segoe UI", 18, "bold"))
        self.canvas.create_text(228, 105, text=track.artist, anchor="nw", width=225, fill=MUTED, font=("Segoe UI", 11))
        self.canvas.create_text(340, 164, text="Ⅱ" if track.is_playing else "▶", fill=WHITE, font=("Segoe UI Symbol", 25, "bold"))

        left, right, y = 28, 452, 251
        self.canvas.create_rectangle(left, y, right, y + 8, fill="#17303B", outline="")
        self.canvas.create_rectangle(left, y, left + ((right - left) * track.progress_fraction), y + 8, fill=CYAN, outline="")
        self.canvas.create_text(left, 274, text=track.format_time(track.progress_ms), anchor="nw", fill=MUTED, font=("Consolas", 10))
        self.canvas.create_text(right, 274, text=track.format_time(track.duration_ms), anchor="ne", fill=MUTED, font=("Consolas", 10))

    def _draw_mode_hint(self) -> None:
        self.canvas.create_text(
            470,
            310,
            text="E eyes  •  S Spotify  •  Space play/pause  •  Esc exit",
            anchor="se",
            fill="#35505B",
            font=("Segoe UI", 8),
        )

