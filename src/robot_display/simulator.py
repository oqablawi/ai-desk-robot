"""Scripted laptop demo timings.

The mode controller lives in robot.py. This module keeps a short
import path for the demo step list.
"""
from .robot import DEMO_END_SECONDS, DEMO_STEPS, Robot

__all__ = ["DEMO_END_SECONDS", "DEMO_STEPS", "Robot"]
