"""Hardware-free interaction state. No microphone, network or audio is used."""
from __future__ import annotations

import time
from typing import Callable

from .models import RobotState


class SimulatorController:
    PHASES = (
        (0.0, RobotState.LISTENING),
        (2.5, RobotState.THINKING),
        (4.5, RobotState.SPEAKING),
        (7.5, RobotState.HAPPY),
    )

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.mode = "eyes"
        self.state = RobotState.IDLE
        self.demo_started: float | None = None

    @property
    def demo_running(self) -> bool:
        return self.demo_started is not None

    def cancel_demo(self) -> None:
        if self.demo_running:
            self.state = RobotState.IDLE
        self.demo_started = None

    def set_mode(self, mode: str) -> None:
        if mode not in ("eyes", "spotify", "talk"):
            raise ValueError(f"Unknown screen: {mode}")
        self.cancel_demo()
        self.mode = mode

    def set_state(self, state: RobotState) -> None:
        self.cancel_demo()
        self.mode = "eyes"
        self.state = state

    def start_demo(self) -> None:
        self.mode = "talk"
        self.demo_started = self.clock()
        self.state = RobotState.LISTENING

    def update(self) -> bool:
        """Return True exactly once when the demo requests the music screen."""
        if self.demo_started is None:
            return False
        elapsed = self.clock() - self.demo_started
        if elapsed >= 9.0:
            self.demo_started = None
            self.state = RobotState.HAPPY
            self.mode = "spotify"
            return True
        for start, state in self.PHASES:
            if elapsed >= start:
                self.state = state
        return False
