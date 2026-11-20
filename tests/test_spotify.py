import unittest

from robot_display.spotify import SpotifyWebApiProvider


class SpotifyTests(unittest.TestCase):
    def test_missing_token_is_safe(self):
        provider = SpotifyWebApiProvider(access_token=None, token_file="does-not-exist.json")
        self.assertIsNone(provider.current())


if __name__ == "__main__":
    unittest.main()
