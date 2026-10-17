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

        # A softer face reads better than mechanical circles on the small screen.
        self.canvas.create_oval(58, 78, 422, 256, fill="#0B1D27", outline="#15333F", width=2)

        if self.state == RobotState.ERROR:
            self._draw_error_eyes(color)
        elif self.state == RobotState.THINKING:
            self._draw_thinking_eyes(now)
        elif self.state == RobotState.SLEEPING or blink > 0.82:
            self._draw_closed_eyes(color, sleeping=self.state == RobotState.SLEEPING)
        else:
            gaze_x = 8 * math.sin((now - self.started) * 0.55)
            eye_scale = 1.08 if self.state == RobotState.LISTENING else 1.0
            eye_height = max(8, 94 * eye_scale * (1.0 - blink))
            for cx in (157, 323):
                self._draw_cute_eye(cx, 158, 72 * eye_scale, eye_height, gaze_x, color)

        self._draw_cheeks(color)
        self._draw_mouth(now, color, pulse)

        label = self.state.value.upper()
        self.canvas.create_text(240, 278, text=label, fill=MUTED, font=("Segoe UI", 9, "bold"))

    def _draw_cute_eye(
        self,
        cx: float,
        cy: float,
        width: float,
        height: float,
        gaze_x: float,
        color: str,
    ) -> None:
        """Draw a glossy rounded eye with a dark pupil and two highlights."""
        self.canvas.create_oval(
            cx - width / 2 - 5,
            cy - height / 2 - 5,
            cx + width / 2 + 5,
            cy + height / 2 + 5,
            fill="#12343F",
            outline="",
        )
        self.canvas.create_oval(
            cx - width / 2,
            cy - height / 2,
            cx + width / 2,
            cy + height / 2,
            fill=color,
            outline="",
        )
        pupil_width = width * 0.46
        pupil_height = max(4, height * 0.56)
        self.canvas.create_oval(
            cx + gaze_x - pupil_width / 2,
            cy - pupil_height / 2 + 5,
            cx + gaze_x + pupil_width / 2,
            cy + pupil_height / 2 + 5,
            fill="#06212A",
            outline="",
        )
        if height > 24:
            self.canvas.create_oval(cx + gaze_x - 10, cy - 22, cx + gaze_x + 4, cy - 8, fill=WHITE, outline="")
            self.canvas.create_oval(cx + gaze_x + 8, cy - 4, cx + gaze_x + 15, cy + 3, fill="#B8FAFF", outline="")

    def _draw_closed_eyes(self, color: str, sleeping: bool = False) -> None:
        start = 200 if sleeping else 205
        extent = 140 if sleeping else 130
        for cx in (157, 323):
            self.canvas.create_arc(
                cx - 45,
                130,
                cx + 45,
                194,
                start=start,
                extent=extent,
                style="arc",
                outline=color,
                width=12,
            )

    def _draw_error_eyes(self, color: str) -> None:
        for cx in (157, 323):
            self.canvas.create_line(cx - 30, 128, cx + 30, 188, fill=color, width=12, capstyle="round")
            self.canvas.create_line(cx + 30, 128, cx - 30, 188, fill=color, width=12, capstyle="round")

    def _draw_thinking_eyes(self, now: float) -> None:
        """Use rotating dots as eyes, inspired by the Windows busy indicator."""
        palette = ("#3A2A53", "#4C376B", "#60458A", "#7755AA", "#9068CA", "#AA7FE9", "#C19CFF", "#D6BBFF")
        active_step = int(now * 10) % len(palette)
        for cx in (157, 323):
            for index in range(8):
                angle = ((index / 8) * math.tau) - (math.pi / 2)
                x = cx + math.cos(angle) * 34
                y = 158 + math.sin(angle) * 34
                brightness = (index - active_step) % 8
                radius = 5 + ((7 - brightness) * 0.45)
                self.canvas.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=palette[7 - brightness],
                    outline="",
                )

    def _draw_cheeks(self, color: str) -> None:
        if self.state != RobotState.HAPPY:
            return
        cheek = "#FF7895"
        self.canvas.create_oval(84, 200, 130, 220, fill=cheek, outline="")
        self.canvas.create_oval(350, 200, 396, 220, fill=cheek, outline="")

    def _draw_mouth(self, now: float, color: str, pulse: float) -> None:
        if self.state == RobotState.SLEEPING:
            self.canvas.create_text(385, 100, text="z", fill=MUTED, font=("Segoe UI", 18, "bold"))
            self.canvas.create_text(408, 76, text="z", fill=MUTED, font=("Segoe UI", 13, "bold"))
            return
        if self.state == RobotState.ERROR:
            self.canvas.create_line(222, 223, 258, 211, fill=color, width=6, capstyle="round")
            return
        if self.state == RobotState.SPEAKING:
            mouth_height = 18 + (14 * pulse)
            self.canvas.create_oval(222, 211 - mouth_height / 2, 258, 211 + mouth_height / 2, fill=color, outline="")
            self.canvas.create_oval(230, 216, 250, 224, fill="#FF7895", outline="")
            return
        if self.state == RobotState.THINKING:
            self.canvas.create_oval(233, 207, 247, 221, fill=color, outline="")
            return
        self.canvas.create_arc(216, 190, 264, 228, start=200, extent=140, style="arc", outline=color, width=6)

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

