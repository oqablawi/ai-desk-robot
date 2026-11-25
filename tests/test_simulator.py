import unittest

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
        self.player.play()

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


if __name__ == "__main__":
    unittest.main()
