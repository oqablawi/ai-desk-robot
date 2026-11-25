from __future__ import annotations

import math
import random
import time
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from .models import PlaybackInfo, RobotState
from .models import FACE_MODES
from .robot import Robot
from .spotify import DemoSpotifyProvider, PlaybackProvider


WIDTH = 480
HEIGHT = 320
BACKGROUND = "#000000"
CYAN = "#41F6FF"
MUTED = "#8CA5B2"
WHITE = "#ECF7FA"

# Use the first family the computer actually has. Segoe UI is common on
# Windows; the Pi typically has DejaVu Sans or Liberation Sans.
FONT_CANDIDATES = (
    "Segoe UI",
    "Ubuntu",
    "DejaVu Sans",
    "Liberation Sans",
    "Helvetica",
    "Arial",
)


def pick_font_family(root: tk.Misc) -> str:
    available = set(tkfont.families(root))
    for name in FONT_CANDIDATES:
        if name in available:
            return name
    return "TkDefaultFont"


class RobotDisplayApp:
    def __init__(self, provider: PlaybackProvider | None = None, scale: int = 2,
                 fullscreen: bool = False, robot: Robot | None = None) -> None:
        if scale not in (1, 2, 3):
            raise ValueError("Scale must be 1, 2 or 3")
        self.scale = scale
        self.fullscreen = fullscreen
        self._scale_x = float(scale)
        self._scale_y = float(scale)
        self.root = tk.Tk()
        self.root.title("AI Desk Robot")
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
        self.robot = robot or Robot()
        self.robot.attach_display()
        self.help_open = False
        self.hitboxes: list[tuple[tuple[float, float, float, float], Callable[[], None]]] = []
        self._font_family = pick_font_family(self.root)
        self._fonts: dict[tuple[int, str, float], tkfont.Font] = {}
        self._frame_id: str | None = None
        self.started = time.monotonic()
        self.last_blink = self.started
        self.next_blink = random.uniform(2.5, 5.0)
        self.blink_started: float | None = None
        self.playback: PlaybackInfo | None = None
        self.voice = None
        self._ptt_held = False
        self.root.bind("<KeyPress>", self._key)
        self.root.bind("<KeyRelease>", self._key_release)
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Motion>", self._hover)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def attach_voice(self, voice) -> None:
        self.voice = voice

    @property
    def mode(self) -> str:
        return self.robot.mode

    @property
    def state(self) -> RobotState:
        return self.robot.state

    def set_mode(self, mode: str) -> None:
        """Change the screen. Call this from the Tk thread (keys or tests).

        Background AI code should call robot.set_mode() instead. Those
        calls stay on a queue until the display loop applies them.
        """
        self.robot.set_mode(mode)
        self.robot.apply_pending()
        if self.mode in FACE_MODES:
            self.blink_started = None
            self.last_blink = time.monotonic()

    def say(self, text: str) -> None:
        self.robot.say(text)
        self.robot.apply_pending()

    def set_state(self, state: RobotState) -> None:
        self.set_mode(state.value)

    def toggle_playback(self, _event: tk.Event | None = None) -> None:
        self.provider.toggle_playback()

    def close(self) -> None:
        if self._frame_id is not None:
            self.root.after_cancel(self._frame_id)
            self._frame_id = None
        if self.voice is not None:
            self.voice.close()
            self.voice = None
        close_provider = getattr(self.provider, "close", None)
        if close_provider:
            close_provider()
        self.root.destroy()

    def _key(self, event: tk.Event) -> None:
        # Keyboard shortcuts are a developer fallback. The real robot
        # will change modes through robot.set_mode(), not on-screen buttons.
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
        if key in ("v", "p"):
            # Hold V (or P) to talk. Ignore keyboard auto-repeat.
            if not self._ptt_held and self.voice is not None:
                self._ptt_held = True
                self.voice.press()
            return
        if key in "1234567" and len(key) == 1:
            self.set_mode(list(FACE_MODES)[int(key) - 1])
        elif key == "e":
            self.set_mode("idle")
        elif key == "s":
            self.set_mode("music")
        elif key == "t":
            self.robot.start_demo()
        elif key == "space":
            self.toggle_playback()
        elif key in ("left", "right"):
            direction = 1 if key == "right" else -1
            if self.mode == "music":
                self.provider.skip(direction)
            else:
                self._cycle_expression(direction)

    def _key_release(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key in ("v", "p") and self._ptt_held:
            self._ptt_held = False
            if self.voice is not None:
                self.voice.release()

    def _cycle_expression(self, direction: int) -> None:
        names = list(FACE_MODES)
        current = self.mode if self.mode in FACE_MODES else "idle"
        self.set_mode(names[(names.index(current) + direction) % len(names)])

    def _action_at(self, x: float, y: float) -> Callable[[], None] | None:
        if not self.help_open and self.mode == "music" and 24 <= x <= 456 and 223 <= y <= 241:
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
            self._fonts[key] = tkfont.Font(
                root=self.root,
                family=self._font_family,
                size=-max(1, round(size * display_scale)),
                weight=weight,
            )
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
        playback = self.provider.current()
        self.robot.update(playback, play=self.provider.play)
        # If music has no track at all, never leave a blank screen.
        if self.robot.mode == "music" and self.provider.current() is None:
            self.robot.set_mode("idle")
            self.robot.apply_pending()
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
        if self.mode == "music":
            self._draw_spotify(now)
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

    def _draw_face(self, now: float) -> None:
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
        self.canvas.move("face", 0, -24)

    def _draw_eyes(self, now: float) -> None:
        self._draw_face(now)

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
            # Safety net: never paint an empty music frame.
            self._draw_eyes(now)
            return
        is_demo = getattr(self.provider, "is_demo", False)
        if is_demo:
            index = getattr(self.provider, "index", 0) % 3
            self._draw_cover(index)
        else:
            self._draw_art_placeholder(track)
        self._text(186, 68, "NOW PLAYING" if track.is_playing else "PAUSED", 10, CYAN, "w", "bold")
        self._text(186, 99, track.title, 23, WHITE, "w", "bold", max_width=270)
        self._text(186, 126, track.artist, 12, MUTED, "w", max_width=270)

        self._button((210, 173, 260, 211), "|‹", lambda: self.provider.skip(-1))
        self._button((270, 173, 340, 211), "Ⅱ" if track.is_playing else "▶", self.toggle_playback, True)
        self._button((350, 173, 400, 211), "›|", lambda: self.provider.skip(1))
        left, right, y = 24, 456, 232
        self.canvas.create_line(left, y, right, y, fill="#1B3542", width=4, capstyle="round")
        position = left + (right - left) * track.progress_fraction
        if position > left:
            self.canvas.create_line(left, y, position, y, fill=CYAN, width=4, capstyle="round")
        self.canvas.create_oval(position - 4, y - 4, position + 4, y + 4, fill=WHITE, outline="")
        self._text(left, 253, track.format_time(track.progress_ms), 11, MUTED, "w")
        self._text(right, 253, track.format_time(track.duration_ms), 11, MUTED, "e")
        if is_demo:
            self._text(240, 253, "Demo tracks · no audio or Spotify login", 10, MUTED)

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
        titles = ("ROBOT DREAMS", "LITTLE ORBIT", "AFTER HOURS")
        self._text(37, 194, titles[index % 3], 10, WHITE, "w", "bold")

    def _draw_art_placeholder(self, track: PlaybackInfo) -> None:
        # TODO: show album art from track.album_art_url once we can decode
        # JPEG images on the Pi without adding new packages. Tk PhotoImage
        # only opens PNG and GIF, and Spotify art is usually JPEG.
        self.canvas.create_rectangle(24, 66, 166, 211, fill="#173F4B", outline="")
        initial = (track.title or "?").strip()[:1].upper() or "?"
        self._text(95, 138, initial, 48, CYAN, weight="bold")

    def _draw_help(self) -> None:
        self.hitboxes.clear()
        self.canvas.create_rectangle(12, 46, 468, 313, fill="#101F2A", outline="#294451")
        self._text(30, 70, "Developer controls", 19, WHITE, "w", "bold")
        rows = (
            ("Hold V", "Push-to-talk (keyboard fallback)"),
            ("E / S", "Face / music screen"),
            ("1-7", "Idle · listen · think · speak · happy · sleep · error"),
            ("Left / Right", "Change expression or skip demo track"),
            ("Space", "Play / pause music"),
            ("T", "Run the scripted mode demo"),
            ("H / Esc", "Close help; Esc outside help exits"),
        )
        for i, (key, meaning) in enumerate(rows):
            self._text(30, 100 + 20 * i, key, 10, CYAN, "w", "bold")
            self._text(150, 100 + 20 * i, meaning, 10, WHITE, "w")
        self._text(240, 251, "Grok chooses the mode · keys are a laptop fallback", 10, MUTED)
        self._button((166, 272, 314, 302), "BACK TO ROBOT", lambda: setattr(self, "help_open", False), True)
