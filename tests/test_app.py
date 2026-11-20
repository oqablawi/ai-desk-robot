"""Render and interaction checks with real Tk; skipped without a desktop display."""
import time
import tkinter as tk
import unittest
from types import SimpleNamespace

from robot_display.app import RobotDisplayApp, HEIGHT, WIDTH
from robot_display.models import RobotState


class AppTests(unittest.TestCase):
    def setUp(self):
        try:
            self.app = RobotDisplayApp(scale=2)
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.app.root.withdraw()

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.close()

    def render(self):
        self.app._render(time.monotonic())
        self.app.root.update_idletasks()

    def test_all_screens_render_with_text_inside_display(self):
        for scale in (1, 2, 3):
            self.app.scale = scale
            self.app._fonts.clear()
            for mode in ("eyes", "spotify", "talk"):
                self.app.set_mode(mode)
                self.render()
                self.assert_text_visible(scale)
            for state in RobotState:
                self.app.set_state(state)
                self.render()
                self.assert_text_visible(scale)
            self.app.help_open = True
            self.render()
            self.assert_text_visible(scale)
            self.app.help_open = False

    def assert_text_visible(self, scale):
        for item in self.app.canvas.find_all():
            if self.app.canvas.type(item) == "text":
                x1, y1, x2, y2 = self.app.canvas.bbox(item)
                text = self.app.canvas.itemcget(item, "text")
                with self.subTest(text=text, scale=scale):
                    self.assertGreaterEqual(x1, 0)
                    self.assertGreaterEqual(y1, 0)
                    self.assertLessEqual(x2, WIDTH * scale)
                    self.assertLessEqual(y2, HEIGHT * scale)

    def test_scaled_clicks_cycle_expression_and_programmatic_modes_work(self):
        self.render()
        self.app._click(SimpleNamespace(x=700, y=300))
        self.assertEqual(self.app.state, RobotState.LISTENING)
        self.app.set_mode("spotify")
        self.render()
        self.app._click(SimpleNamespace(x=610, y=384))
        self.assertFalse(self.app.provider.current().is_playing)
        self.app._click(SimpleNamespace(x=480, y=464))
        self.assertAlmostEqual(self.app.provider.current().progress_fraction, 0.5, places=4)

    def test_help_blocks_underlying_music_controls(self):
        self.app.set_mode("spotify")
        self.app.help_open = True
        self.render()
        self.app._click(SimpleNamespace(x=610, y=384))
        self.assertTrue(self.app.provider.current().is_playing)

    def test_happy_stays_open_and_only_happy_has_blush(self):
        for state in RobotState:
            self.app.set_state(state)
            self.render()
            cheeks = [item for item in self.app.canvas.find_all()
                      if self.app.canvas.type(item) == "oval"
                      and self.app.canvas.itemcget(item, "fill") == "#FF7895"]
            self.assertEqual(len(cheeks), 2 if state == RobotState.HAPPY else 1 if state == RobotState.SPEAKING else 0)
        self.app.set_state(RobotState.HAPPY)
        self.app.blink_started = time.monotonic() - 0.11
        self.assertEqual(self.app._blink_amount(time.monotonic()), 0)


if __name__ == "__main__":
    unittest.main()
