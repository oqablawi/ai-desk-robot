from __future__ import annotations

import math
import random
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from .models import PlaybackInfo, RobotState
from .spotify import DemoSpotifyProvider, PlaybackProvider
from .simulator import SimulatorController


WIDTH = 480
HEIGHT = 320
BACKGROUND = "#000000"
CYAN = "#41F6FF"
MUTED = "#8CA5B2"
WHITE = "#ECF7FA"


class RobotDisplayApp:
    def __init__(self, provider: PlaybackProvider | None = None, scale: int = 2,
                 fullscreen: bool = False) -> None:
        if scale not in (1, 2, 3):
            raise ValueError("Scale must be 1, 2 or 3")
        self.scale = scale
        self.fullscreen = fullscreen
        self._scale_x = float(scale)
        self._scale_y = float(scale)
        self.root = tk.Tk()
        self.root.title("AI Desk Robot Display Simulator")
        self.root.geometry(f"{WIDTH * scale}x{HEIGHT * scale}")
        self.root.resizable(False, False)
        self.root.configure(bg=BACKGROUND)
        self.root.attributes("-fullscreen", fullscreen)
        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH * scale,
            height=HEIGHT * scale,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.provider = provider or DemoSpotifyProvider()
        self.controller = SimulatorController()
        self.help_open = False
        self.hitboxes: list[tuple[tuple[float, float, float, float], Callable[[], None]]] = []
        self._fonts: dict[tuple[int, str, float], tkfont.Font] = {}
        self._frame_id: str | None = None
        self.started = time.monotonic()
        self.last_blink = self.started
        self.next_blink = random.uniform(2.5, 5.0)
        self.blink_started: float | None = None
        self.playback: PlaybackInfo | None = None
        self.root.bind("<KeyPress>", self._key)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._hover)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    @property
    def mode(self) -> str:
        return self.controller.mode

    @property
    def state(self) -> RobotState:
        return self.controller.state

    def set_mode(self, mode: str) -> None:
        self.controller.set_mode(mode)

    def set_state(self, state: RobotState) -> None:
        self.controller.set_state(state)
        self.blink_started = None
        self.last_blink = time.monotonic()

    def toggle_demo_playback(self, _event: tk.Event | None = None) -> None:
        self.provider.toggle_playback()

    def close(self) -> None:
        if self._frame_id is not None:
            self.root.after_cancel(self._frame_id)
            self._frame_id = None
        close_provider = getattr(self.provider, "close", None)
        if close_provider:
            close_provider()
        self.root.destroy()

    def _key(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key == "escape":
            if self.help_open:
                self.help_open = False
            else:
                self.close()
            return
        if key in ("h", "question"):
            self.help_open = not self.help_open
            return
        if self.help_open:
            return
        if key in "1234567" and len(key) == 1:
            self.set_state(list(RobotState)[int(key) - 1])
        elif key == "e":
            self.set_mode("eyes")
        elif key == "s":
            self.set_mode("spotify")
        elif key == "t":
            self.controller.start_demo()
        elif key == "space":
            if self.mode == "talk":
                self._toggle_talk()
            else:
                self.toggle_demo_playback()
        elif key in ("left", "right"):
            direction = 1 if key == "right" else -1
            if self.mode == "eyes":
                self._cycle_expression(direction)
            elif self.mode == "spotify":
                self.provider.skip(direction)

    def _cycle_expression(self, direction: int) -> None:
        states = list(RobotState)
        self.set_state(states[(states.index(self.state) + direction) % len(states)])

    def _toggle_talk(self) -> None:
        if self.controller.demo_running:
            self.controller.cancel_demo()
        else:
            self.controller.start_demo()

    def _action_at(self, x: float, y: float) -> Callable[[], None] | None:
        if not self.help_open and self.mode == "spotify" and 24 <= x <= 456 and 223 <= y <= 241:
            return lambda: self.provider.seek((x - 24) / 432)
        for (left, top, right, bottom), action in reversed(self.hitboxes):
            if left <= x <= right and top <= y <= bottom:
                return action
        return None

    def _click(self, event: tk.Event) -> None:
        action = self._action_at(event.x / self._scale_x, event.y / self._scale_y)
        if action:
            action()

    def _hover(self, event: tk.Event) -> None:
        action = self._action_at(event.x / self._scale_x, event.y / self._scale_y)
        self.canvas.configure(cursor="hand2" if action else "")

    def _font(self, size: int, weight: str = "normal") -> tkfont.Font:
        display_scale = min(self._scale_x, self._scale_y)
        key = (size, weight, round(display_scale, 3))
        if key not in self._fonts:
            self._fonts[key] = tkfont.Font(root=self.root, family="Segoe UI",
                                           size=-max(1, round(size * display_scale)), weight=weight)
        return self._fonts[key]

    def _text(self, x: float, y: float, text: str, size: int = 12, color: str = WHITE,
              anchor: str = "center", weight: str = "normal", max_width: int | None = None) -> None:
        font = self._font(size, weight)
        if max_width is not None and font.measure(text) > max_width * self._scale_x:
            while text and font.measure(text + "…") > max_width * self._scale_x:
                text = text[:-1]
            text += "…"
        self.canvas.create_text(x, y, text=text, fill=color, anchor=anchor, font=font)

    def _button(self, bounds: tuple[int, int, int, int], label: str,
                action: Callable[[], None], active: bool = False) -> None:
        x1, y1, x2, y2 = bounds
        self.canvas.create_rectangle(*bounds, fill="#FFD400" if active else "#15180F",
                                     outline="#FFD400" if active else "#3B3D2B", width=1)
        self._text((x1 + x2) / 2, (y1 + y2) / 2, label, 12,
                   "#080A07" if active else MUTED, weight="bold")
        self.hitboxes.append((bounds, action))

    def run(self) -> None:
        self._frame()
        self.root.mainloop()

    def _frame(self) -> None:
        if self.controller.update():
            self.provider.play()
        self._render(time.monotonic())
        self._frame_id = self.root.after(33, self._frame)

    def _render(self, now: float) -> None:
        if self.fullscreen:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width > 1 and height > 1:
                self._scale_x = width / WIDTH
                self._scale_y = height / HEIGHT
        else:
            self._scale_x = float(self.scale)
            self._scale_y = float(self.scale)
        self.canvas.delete("all")
        self.hitboxes.clear()
        if self.mode == "spotify":
            self._draw_spotify(now)
        elif self.mode == "talk":
            self._draw_talk(now)
        else:
            self._draw_eyes(now)
        if self.help_open:
            self._draw_help()
        # The design stays on a 480 x 320 grid at every desktop zoom level.
        self.canvas.scale("all", 0, 0, self._scale_x, self._scale_y)
        for item in self.canvas.find_all():
            if self.canvas.type(item) != "text":
                width = float(self.canvas.itemcget(item, "width") or 0)
                self.canvas.itemconfigure(item, width=width * min(self._scale_x, self._scale_y))

    def _blink_amount(self, now: float) -> float:
        if self.state == RobotState.HAPPY:
            return 0.0
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

    def _draw_face(self, now: float, compact: bool = False) -> None:
        before = set(self.canvas.find_all())
        blink = self._blink_amount(now)
        pulse = (math.sin((now - self.started) * 2.0) + 1.0) / 2.0
        colors = {
            RobotState.ERROR: "#FF5364",
            RobotState.THINKING: "#B68CFF",
            RobotState.LISTENING: "#54FFB5",
        }
        color = colors.get(self.state, CYAN)

        if self.state == RobotState.ERROR:
            self._draw_error_eyes(color)
        elif self.state == RobotState.THINKING:
            self._draw_thinking_eyes(now)
        elif self.state == RobotState.SLEEPING or blink > 0.82:
            self._draw_closed_eyes(color, sleeping=self.state == RobotState.SLEEPING)
        else:
            gaze_x = 8 * math.sin((now - self.started) * 0.55)
            eye_scale = 1.08 if self.state == RobotState.LISTENING else 1.0
            eye_height = max(8, 82 * eye_scale * (1.0 - blink))
            for cx in (157, 323):
                self._draw_cute_eye(cx, 150, 98 * eye_scale, eye_height, gaze_x, color)

        self._draw_cheeks(color)
        self._draw_mouth(now, color, pulse)

        for item in set(self.canvas.find_all()) - before:
            self.canvas.addtag_withtag("face", item)
        if compact:
            self.canvas.scale("face", 240, 158, 0.48, 0.48)
            self.canvas.move("face", 0, -38)
        else:
            self.canvas.move("face", 0, -24)

    def _draw_eyes(self, now: float) -> None:
        self._draw_face(now)
        # The entire display is the character. Tap either half to change expression.
        self.hitboxes.append(((0, 0, 240, 320), lambda: self._cycle_expression(-1)))
        self.hitboxes.append(((240, 0, 480, 320), lambda: self._cycle_expression(1)))

    def _draw_cute_eye(
        self,
        cx: float,
        cy: float,
        width: float,
        height: float,
        gaze_x: float,
        color: str,
    ) -> None:
        """Draw a soft rounded-square light inspired by compact desk robots."""
        if height <= 10:
            self.canvas.create_line(cx - width / 2, cy, cx + width / 2, cy,
                                    fill=color, width=max(2, height), capstyle="round")
            return
        radius = min(20, height / 3)
        self._rounded_rect(cx + gaze_x - width / 2, cy - height / 2,
                           cx + gaze_x + width / 2, cy + height / 2,
                           radius, color)

    def _rounded_rect(self, x1: float, y1: float, x2: float, y2: float,
                      radius: float, fill: str) -> None:
        radius = max(1, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline="")
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline="")
        self.canvas.create_oval(x1, y1, x1 + 2 * radius, y1 + 2 * radius, fill=fill, outline="")
        self.canvas.create_oval(x2 - 2 * radius, y1, x2, y1 + 2 * radius, fill=fill, outline="")
        self.canvas.create_oval(x1, y2 - 2 * radius, x1 + 2 * radius, y2, fill=fill, outline="")
        self.canvas.create_oval(x2 - 2 * radius, y2 - 2 * radius, x2, y2, fill=fill, outline="")

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
            self._text(385, 100, "z", 20, MUTED, weight="bold")
            self._text(408, 76, "z", 15, MUTED, weight="bold")
            return
        if self.state == RobotState.ERROR:
            self.canvas.create_line(222, 223, 258, 211, fill=color, width=6, capstyle="round")
            return
        if self.state == RobotState.SPEAKING:
            mouth_height = 18 + (14 * pulse)
            mouth_top = 211 - mouth_height / 2
            mouth_bottom = 211 + mouth_height / 2
            self.canvas.create_oval(222, mouth_top, 258, mouth_bottom,
                                    fill="#050505", outline=color, width=3)
            tongue_bottom = mouth_bottom - 3
            tongue_top = max(mouth_top + 4, tongue_bottom - 6)
            self.canvas.create_oval(230, tongue_top, 250, tongue_bottom,
                                    fill="#FF7895", outline="")
            return
        if self.state == RobotState.THINKING:
            self.canvas.create_oval(233, 207, 247, 221, fill=color, outline="")
            return
        self.canvas.create_arc(226, 195, 254, 217, start=200, extent=140,
                               style="arc", outline=color, width=3)

    def _draw_spotify(self, now: float) -> None:
        track = self.playback = self.provider.current()
        if track is None:
            self._text(240, 128, "NOTHING PLAYING", 20, WHITE, weight="bold")
            self._text(240, 157, "Start Spotify on your phone or computer", 11, MUTED)
            return
        index = getattr(self.provider, "index", 0)
        self._draw_cover(index)
        self._text(186, 68, "NOW PLAYING" if track.is_playing else "PAUSED", 10, CYAN, "w", "bold")
        self._text(186, 99, track.title, 23, WHITE, "w", "bold", max_width=270)
        self._text(186, 126, track.artist, 12, MUTED, "w", max_width=270)
        self._text(186, 148, f"DESK SESSIONS   /   0{index + 1}", 10, MUTED, "w")

        self._button((210, 173, 260, 211), "|‹", lambda: self.provider.skip(-1))
        self._button((270, 173, 340, 211), "Ⅱ" if track.is_playing else "▶", self.toggle_demo_playback, True)
        self._button((350, 173, 400, 211), "›|", lambda: self.provider.skip(1))
        left, right, y = 24, 456, 232
        self.canvas.create_line(left, y, right, y, fill="#1B3542", width=4, capstyle="round")
        position = left + (right - left) * track.progress_fraction
        if position > left:
            self.canvas.create_line(left, y, position, y, fill=CYAN, width=4, capstyle="round")
        self.canvas.create_oval(position - 4, y - 4, position + 4, y + 4, fill=WHITE, outline="")
        self._text(left, 253, track.format_time(track.progress_ms), 11, MUTED, "w")
        self._text(right, 253, track.format_time(track.duration_ms), 11, MUTED, "e")
        self._text(240, 253, "Demo tracks · no audio / Spotify connection", 10, MUTED)

    def _draw_cover(self, index: int) -> None:
        """Original geometric demo artwork; no remote assets or album downloads."""
        colors = (("#173F4B", CYAN), ("#292443", "#C3A4FF"), ("#452A3C", "#FFB18F"))
        background, accent = colors[index % len(colors)]
        self.canvas.create_rectangle(24, 66, 166, 211, fill=background, outline="")
        if index == 0:
            for radius in (54, 43, 30):
                self.canvas.create_oval(95 - radius, 131 - radius, 95 + radius, 131 + radius,
                                        fill="#0B202E", outline=accent, width=1)
            self.canvas.create_oval(86, 122, 104, 140, fill=accent, outline="")
        elif index == 1:
            self.canvas.create_oval(44, 98, 146, 164, outline=accent, width=2)
            self.canvas.create_oval(65, 80, 125, 180, outline=accent, width=1)
            self.canvas.create_oval(80, 115, 110, 145, fill=accent, outline="")
            self.canvas.create_oval(133, 111, 143, 121, fill=WHITE, outline="")
        else:
            self.canvas.create_oval(59, 86, 131, 158, fill=accent, outline="")
            for y in range(136, 183, 8):
                self.canvas.create_rectangle(36, y, 154, y + 4, fill=background, outline="")
        self._text(37, 194, ("ROBOT DREAMS", "LITTLE ORBIT", "AFTER HOURS")[index], 10, WHITE, "w", "bold")

    def _draw_header(self) -> None:
        self.canvas.create_rectangle(18, 15, 27, 24, fill=CYAN, outline="")
        self._text(36, 20, "DESK//UNIT", 11, WHITE, "w", "bold")
        self.canvas.create_rectangle(151, 10, 205, 30, fill="#25250F", outline="#FFD400")
        self._text(178, 20, "ONLINE", 8, CYAN, weight="bold")
        self._text(409, 20, time.strftime("%I:%M %p").lstrip("0"), 11, MUTED, "e")
        self._button((430, 6, 462, 34), "?", lambda: setattr(self, "help_open", True))
        self.canvas.create_line(18, 40, 462, 40, fill="#5D5A22")
        self.canvas.create_line(18, 43, 112, 43, fill="#FFD400", width=2)

    def _draw_navigation(self) -> None:
        self.canvas.create_line(18, 281, 462, 281, fill="#3E3B18")
        self._text(22, 298, "MODE", 8, MUTED, "w", "bold")
        for bounds, mode, code, label in (
            ((72, 287, 178, 309), "eyes", "01", "OPTIC"),
            ((184, 287, 290, 309), "spotify", "02", "TAPE"),
            ((296, 287, 402, 309), "talk", "03", "COMMS"),
        ):
            active = self.mode == mode
            x1, y1, x2, y2 = bounds
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         fill="#FFD400" if active else "#0C0E09",
                                         outline="#FFD400" if active else "#393B29")
            self._text(x1 + 10, 298, code, 7, "#080A07" if active else "#6F705D", "w", "bold")
            self._text(x1 + 35, 298, label, 8, "#080A07" if active else MUTED, "w", "bold")
            self.hitboxes.append((bounds, lambda m=mode: self.set_mode(m)))
        self._text(456, 298, "SEL", 7, "#5D5A22", "e", "bold")

    def _draw_crt_texture(self) -> None:
        """Subtle phosphor scanlines and registration marks for a retro terminal feel."""
        for y in range(48, 278, 8):
            self.canvas.create_line(10, y, 470, y, fill="#0D100A")
        mark = "#4A471A"
        for x, y, sx, sy in ((12, 50, 1, 1), (468, 50, -1, 1),
                             (12, 270, 1, -1), (468, 270, -1, -1)):
            self.canvas.create_line(x, y, x + 12 * sx, y, fill=mark, width=2)
            self.canvas.create_line(x, y, x, y + 12 * sy, fill=mark, width=2)

    def _draw_talk(self, now: float) -> None:
        running = self.controller.demo_running
        self._text(24, 60, "A LITTLE CONVERSATION", 11, WHITE, "w", "bold")
        self._text(456, 60, "SCRIPTED DEMO", 10, MUTED, "e")
        self._draw_face(now, compact=True)
        labels = {
            RobotState.LISTENING: 'You: “Play something mellow.”',
            RobotState.THINKING: "Choosing a demo track…",
            RobotState.SPEAKING: 'Robot: “Here is a little desk music.”',
            RobotState.HAPPY: "Opening the music screen…",
        }
        self._text(240, 183, labels.get(self.state, "See how a voice request will feel.") if running
                   else "See how a voice request will feel.", 15, WHITE)
        self._text(240, 207, "Simulated listening & speech · microphone stays off", 10, MUTED)
        self._button((140, 225, 340, 260), "STOP DEMO" if running else "TRY CONVERSATION",
                     self._toggle_talk, True)
        if running:
            phase = [state for _, state in self.controller.PHASES].index(self.state)
            for i in range(4):
                x = 216 + i * 16
                self.canvas.create_oval(x, 164, x + 5, 169, fill=CYAN if i == phase else "#31434F", outline="")

    def _draw_help(self) -> None:
        self.hitboxes.clear()
        self.canvas.create_rectangle(12, 46, 468, 313, fill="#101F2A", outline="#294451")
        self._text(30, 70, "Your robot, on your laptop", 19, WHITE, "w", "bold")
        rows = (
            ("E / S", "Face / music screen"),
            ("1–7", "Idle · listen · think · speak · happy · sleep · error"),
            ("← / →", "Change expression or skip demo track"),
            ("Space", "Play / pause music; start / stop talk demo"),
            ("T", "Run the scripted conversation"),
            ("H / Esc", "Close help; Esc outside help exits"),
        )
        for i, (key, meaning) in enumerate(rows):
            self._text(30, 104 + 23 * i, key, 11, CYAN, "w", "bold")
            self._text(97, 104 + 23 * i, meaning, 10, WHITE, "w")
        self._text(240, 251, "480 × 320 layout · fictional music · no microphone or cloud AI", 10, MUTED)
        self._button((166, 272, 314, 302), "BACK TO ROBOT", lambda: setattr(self, "help_open", False), True)
