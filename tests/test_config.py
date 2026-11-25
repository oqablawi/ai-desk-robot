import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from robot_display.config import RobotConfig, load_dotenv


class ConfigTests(unittest.TestCase):
    def test_defaults_are_safe_for_laptop(self):
        with patch.dict(os.environ, {}, clear=True):
            config = RobotConfig.from_environment()
        self.assertEqual(config.mode, "demo")
        self.assertFalse(config.fullscreen)
        self.assertEqual(config.scale, 2)
        self.assertEqual(config.start_screen, "idle")
        self.assertIsNone(config.xai_api_key)

    def test_dotenv_does_not_replace_existing_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text("ROBOT_MODE=spotify\nROBOT_SCALE=1\n", encoding="utf-8")
            with patch.dict(os.environ, {"ROBOT_MODE": "demo"}, clear=True):
                load_dotenv(path)
                self.assertEqual(os.environ["ROBOT_MODE"], "demo")
                self.assertEqual(os.environ["ROBOT_SCALE"], "1")


if __name__ == "__main__":
    unittest.main()
