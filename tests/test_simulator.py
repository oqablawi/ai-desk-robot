import unittest

from robot_display.models import RobotState
from robot_display.simulator import SimulatorController
from robot_display.spotify import DemoSpotifyProvider


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.player = DemoSpotifyProvider(self.clock)

    def test_reads_do_not_advance_playback(self):
        self.clock.now = 1.5
        for _ in range(10):
            self.assertEqual(self.player.current().progress_ms, 1500)

    def test_pause_and_resume_preserve_position(self):
        self.clock.now = 2
        self.player.toggle_playback()
        self.clock.now = 20
        self.assertEqual(self.player.current().progress_ms, 2000)
        self.assertFalse(self.player.current().is_playing)
        self.player.toggle_playback()
        self.clock.now = 21
        self.assertEqual(self.player.current().progress_ms, 3000)

    def test_elapsed_time_advances_tracks_without_polling(self):
        self.clock.now = 214 + 183 + 7
        self.assertEqual(self.player.current().title, "After Hours")
        self.assertEqual(self.player.current().progress_ms, 7000)

    def test_long_sleep_keeps_remainder(self):
        self.clock.now = (214 + 183 + 246) * 100 + 220
        self.assertEqual(self.player.current().title, "Little Orbit")
        self.assertEqual(self.player.current().progress_ms, 6000)

    def test_skip_wraps_and_preserves_pause(self):
        self.player.toggle_playback()
        self.player.skip(-1)
        self.assertEqual(self.player.current().title, "After Hours")
        self.assertFalse(self.player.current().is_playing)
        self.player.skip()
        self.assertEqual(self.player.current().title, "Robot Dreams")

    def test_seek_clamps_and_changes_position(self):
        self.player.seek(0.5)
        self.assertAlmostEqual(self.player.current().progress_fraction, 0.5, places=4)
        self.player.seek(-1)
        self.assertEqual(self.player.current().progress_ms, 0)
        self.player.seek(2)
        track = self.player.current()
        self.assertEqual(track.progress_ms, track.duration_ms - 1)


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.controller = SimulatorController(self.clock)

    def test_full_sequence_opens_music_once(self):
        self.controller.start_demo()
        for now, state in ((0, RobotState.LISTENING), (2.5, RobotState.THINKING),
                           (4.5, RobotState.SPEAKING), (7.5, RobotState.HAPPY)):
            self.clock.now = now
            self.assertFalse(self.controller.update())
            self.assertEqual(self.controller.state, state)
        self.clock.now = 9
        self.assertTrue(self.controller.update())
        self.assertEqual(self.controller.mode, "spotify")
        self.assertFalse(self.controller.update())

    def test_switch_screen_cancels_pending_demo(self):
        self.controller.start_demo()
        self.controller.set_mode("eyes")
        self.clock.now = 20
        self.assertFalse(self.controller.update())
        self.assertEqual(self.controller.mode, "eyes")
        self.assertEqual(self.controller.state, RobotState.IDLE)

    def test_manual_expression_overrides_demo_and_music(self):
        self.controller.start_demo()
        self.controller.set_state(RobotState.SLEEPING)
        self.clock.now = 20
        self.controller.update()
        self.assertEqual(self.controller.state, RobotState.SLEEPING)
        self.assertEqual(self.controller.mode, "eyes")
        self.controller.set_mode("spotify")
        self.controller.set_state(RobotState.HAPPY)
        self.assertEqual(self.controller.mode, "eyes")

    def test_restart_uses_new_start_time(self):
        self.controller.start_demo()
        self.clock.now = 5
        self.controller.start_demo()
        self.controller.update()
        self.assertEqual(self.controller.state, RobotState.LISTENING)


if __name__ == "__main__":
    unittest.main()
