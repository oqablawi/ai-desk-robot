"""Display software for the AI desk robot."""

from .ai import GrokReply, ask_grok, decide_mode, parse_reply
from .models import MODES, PlaybackInfo, RobotState
from .robot import Robot

__all__ = [
    "PlaybackInfo",
    "RobotState",
    "Robot",
    "MODES",
    "GrokReply",
    "ask_grok",
    "decide_mode",
    "parse_reply",
]
