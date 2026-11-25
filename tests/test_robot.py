import unittest

from robot_display.models import RobotState
from robot_display.robot import Robot
from robot_display.spotify import DemoSpotifyProvider


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakeTrack:
    def __init__(self, playing, title="Song"):
        self.is_playing = playing
        self.title = title


class RobotTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.robot = Robot(self.clock)

    def test_set_mode_and_say_work_without_tk(self):
        self.robot.set_mode("listening")
        self.assertEqual(self.robot.mode, "listening")
        self.assertEqual(self.robot.state, RobotState.LISTENING)
        self.robot.say("Hello there.")
        self.assertEqual(self.robot.mode, "speaking")
        self.assertEqual(self.robot.spoken_text, "Hello there.")
        self.robot.set_mode("music")
        self.assertEqual(self.robot.mode, "music")

    def test_old_mode_names_still_work(self):
        self.robot.set_mode("eyes")
        self.assertEqual(self.robot.mode, "idle")
        self.robot.set_mode("spotify")
        self.assertEqual(self.robot.mode, "music")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            self.robot.set_mode("dance")

    def test_queued_commands_wait_until_apply_pending(self):
        self.robot.attach_display()
        self.robot.set_mode("happy")
        self.assertEqual(self.robot.mode, "idle")
        self.robot.apply_pending()
        self.assertEqual(self.robot.mode, "happy")

    def test_scripted_demo_walks_through_modes_then_music(self):
        plays = []
        self.robot.start_demo()
        for now, mode in ((0, "listening"), (2.5, "thinking"),
                          (4.5, "speaking"), (7.5, "happy")):
            self.clock.now = now
            self.robot.update(play=lambda: plays.append("play"))
            self.assertEqual(self.robot.mode, mode)
            self.assertTrue(self.robot.demo_running)
        self.assertEqual(self.robot.spoken_text, "Here is a little desk music.")
        self.clock.now = 9
        self.robot.update(play=lambda: plays.append("play"))
        self.assertEqual(self.robot.mode, "music")
        self.assertFalse(self.robot.demo_running)
        self.assertEqual(plays, ["play"])

    def test_manual_mode_cancels_demo(self):
        self.robot.start_demo()
        self.robot.set_mode("sleeping")
        self.clock.now = 20
        self.robot.update()
        self.assertEqual(self.robot.mode, "sleeping")
        self.assertFalse(self.robot.demo_running)

    def test_auto_music_when_idle_and_playing(self):
        self.robot.update(FakeTrack(True))
        self.assertEqual(self.robot.mode, "music")
        self.assertTrue(self.robot.auto_music)
        self.robot.update(FakeTrack(False))
        self.assertEqual(self.robot.mode, "idle")

    def test_talking_mode_is_not_replaced_by_music(self):
        self.robot.set_mode("listening")
        self.robot.update(FakeTrack(True))
        self.assertEqual(self.robot.mode, "listening")

    def test_hold_mode_blocks_auto_music(self):
        self.robot.hold_mode = True
        self.robot.set_mode("happy")
        self.robot.update(FakeTrack(True))
        self.assertEqual(self.robot.mode, "happy")

    def test_explicit_music_mode_stays_when_paused(self):
        self.robot.set_mode("music")
        self.robot.update(FakeTrack(False))
        self.assertEqual(self.robot.mode, "music")
        self.assertFalse(self.robot.auto_music)


class DemoPlaybackStartTests(unittest.TestCase):
    def test_demo_provider_starts_paused(self):
        player = DemoSpotifyProvider(Clock())
        self.assertFalse(player.current().is_playing)
        self.assertEqual(player.current().progress_ms, 0)


if __name__ == "__main__":
    unittest.main()
