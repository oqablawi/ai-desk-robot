import unittest

from robot_display.models import PlaybackInfo


class PlaybackInfoTests(unittest.TestCase):
    def test_progress_is_clamped(self) -> None:
        high = PlaybackInfo("x", "y", 100, 200, True)
        low = PlaybackInfo("x", "y", 100, -20, True)
        self.assertEqual(high.progress_fraction, 1.0)
        self.assertEqual(low.progress_fraction, 0.0)

    def test_zero_duration_is_safe(self) -> None:
        track = PlaybackInfo("x", "y", 0, 50, False)
        self.assertEqual(track.progress_fraction, 0.0)

    def test_time_format(self) -> None:
        self.assertEqual(PlaybackInfo.format_time(154_000), "2:34")


if __name__ == "__main__":
    unittest.main()

