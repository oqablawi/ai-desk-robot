import unittest

from robot_display.ai import GrokReply
from robot_display.robot import Robot
from robot_display.voice import VoiceLoop, apply_music_action


class FakeTrack:
    def __init__(self, playing=True):
        self.is_playing = playing
        self.title = "Robot Dreams"
        self.artist = "Demo"


class FakeProvider:
    def __init__(self, playing=True):
        self.actions = []
        self.track = FakeTrack(playing)

    def current(self):
        return self.track

    def play(self):
        self.track.is_playing = True
        self.actions.append("play")

    def toggle_playback(self):
        self.track.is_playing = not self.track.is_playing
        self.actions.append("toggle")

    def skip(self, direction=1):
        self.actions.append(("skip", direction))


class MusicActionTests(unittest.TestCase):
    def test_actions(self):
        provider = FakeProvider()
        apply_music_action(provider, "none")
        self.assertEqual(provider.actions, [])
        apply_music_action(provider, "play")
        apply_music_action(provider, "skip_next")
        apply_music_action(provider, "skip_prev")
        apply_music_action(provider, "pause")
        self.assertEqual(provider.actions, ["play", ("skip", 1), ("skip", -1), "toggle"])


class VoiceDeliverTests(unittest.TestCase):
    def test_show_music_sets_music_mode(self):
        robot = Robot()
        provider = FakeProvider(playing=False)
        loop = VoiceLoop(robot, provider=provider)
        loop._speak = lambda text: None
        loop._deliver(GrokReply(mode="happy", show_music=True, say="Sure.", music_action="play"))
        self.assertEqual(robot.mode, "music")
        self.assertFalse(robot.hold_mode)
        self.assertEqual(robot.spoken_text, "Sure.")
        self.assertEqual(provider.actions, ["play"])

    def test_face_reply_sets_hold_mode(self):
        robot = Robot()
        loop = VoiceLoop(robot)
        loop._speak = lambda text: None
        loop._deliver(GrokReply(mode="happy", show_music=False, say="Hi."))
        self.assertEqual(robot.mode, "happy")
        self.assertTrue(robot.hold_mode)

    def test_hear_without_recording_reports_no_mic(self):
        loop = VoiceLoop(Robot(), api_key="unused")
        self.assertIsNone(loop._hear(None))
