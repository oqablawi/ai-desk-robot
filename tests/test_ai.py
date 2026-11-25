import json
import unittest
from io import BytesIO
from unittest.mock import patch

from robot_display.ai import ask_grok, decide_mode, demo_reply, parse_reply


class ParseReplyTests(unittest.TestCase):
    def test_plain_json(self):
        reply = parse_reply('{"mode":"happy","show_music":false,"say":"Hello there.","music_action":"none"}')
        self.assertEqual(reply.mode, "happy")
        self.assertFalse(reply.show_music)
        self.assertEqual(reply.say, "Hello there.")
        self.assertEqual(reply.music_action, "none")

    def test_markdown_fence_and_aliases(self):
        text = "```json\n{\"mode\":\"spotify\",\"show_music\":true,\"say\":\"Sure.\",\"music_action\":\"skip_next\"}\n```"
        reply = parse_reply(text)
        self.assertEqual(reply.mode, "music")
        self.assertTrue(reply.show_music)
        self.assertEqual(reply.music_action, "skip_next")

    def test_music_action_implies_show_music(self):
        reply = parse_reply('{"mode":"happy","show_music":false,"say":"Skipping.","music_action":"skip_next"}')
        self.assertTrue(reply.show_music)

    def test_bare_sentence_and_bad_json(self):
        reply = parse_reply("Just a spoken sentence.")
        self.assertEqual(reply.mode, "happy")
        self.assertEqual(reply.say, "Just a spoken sentence.")
        reply = parse_reply("{not-json")
        self.assertEqual(reply.mode, "happy")

    def test_unknown_mode_falls_back_to_happy(self):
        reply = parse_reply('{"mode":"dance","say":"Wow."}')
        self.assertEqual(reply.mode, "happy")
        self.assertEqual(reply.say, "Wow.")


class DecideModeTests(unittest.TestCase):
    def test_idle_and_playing_shows_music(self):
        self.assertEqual(decide_mode({
            "type": "playback",
            "current_mode": "idle",
            "is_playing": True,
            "auto_music": False,
        }), "music")

    def test_auto_music_returns_to_idle_when_stopped(self):
        self.assertEqual(decide_mode({
            "type": "playback",
            "current_mode": "music",
            "is_playing": False,
            "auto_music": True,
        }), "idle")

    def test_hold_mode_and_demo_do_not_auto_switch(self):
        self.assertIsNone(decide_mode({
            "type": "playback",
            "current_mode": "idle",
            "is_playing": True,
            "hold_mode": True,
        }))
        self.assertIsNone(decide_mode({
            "type": "playback",
            "current_mode": "idle",
            "is_playing": True,
            "demo_running": True,
        }))


class AskGrokTests(unittest.TestCase):
    def test_missing_key_uses_demo_reply(self):
        reply = ask_grok("play a song", api_key=None)
        self.assertTrue(reply.show_music)
        self.assertEqual(reply.say, "Here is a little desk music.")
        polite = demo_reply("hello")
        self.assertIn("API key", polite.say)
        self.assertFalse(polite.show_music)

    def test_parses_a_mocked_api_response(self):
        payload = {
            "choices": [{
                "message": {
                    "content": '{"mode":"happy","show_music":false,"say":"Hi from Grok.","music_action":"none"}'
                }
            }]
        }

        class FakeResponse(BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(request, timeout=60):
            return FakeResponse(json.dumps(payload).encode())

        with patch("robot_display.ai.urllib.request.urlopen", fake_urlopen):
            reply = ask_grok("hello", api_key="test-key")
        self.assertEqual(reply.say, "Hi from Grok.")
        self.assertEqual(reply.mode, "happy")


if __name__ == "__main__":
    unittest.main()
