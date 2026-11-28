"""Push-to-talk voice loop for the desk robot.

Hold the GPIO button, or hold V on the keyboard, to record. On release
the loop transcribes the clip, asks Grok, speaks the reply, and sets
the face or music screen.

Audio uses the xAI speech-to-text and text-to-speech APIs with the
same XAI_API_KEY. Those APIs run in the cloud, which is a better fit
for a Raspberry Pi Zero 2 W than a local speech model. If the key or
microphone is missing, the loop falls back to a short demo reply or a
clear spoken error. espeak-ng is an offline backup for speech out.
"""
from __future__ import annotations

import shutil
import signal
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable

from .diagnostics import log_voice_error
from .ai import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TTS_VOICE,
    GrokReply,
    ask_grok,
    synthesize_speech,
    transcribe_audio,
)
from .robot import Robot


def recorder_command() -> list[str] | None:
    """Return a command that records 16 kHz mono WAV to a file path."""
    if shutil.which("arecord"):
        return ["arecord", "-q", "-f", "S16_LE", "-r", "16000", "-c", "1"]
    if shutil.which("ffmpeg"):
        return ["ffmpeg", "-y", "-loglevel", "error", "-f", "alsa", "-ac", "1",
                "-ar", "16000", "-i", "default"]
    return None


def play_audio_file(path: Path) -> bool:
    """Play a WAV or MP3 file. Returns True if a player was found."""
    suffix = path.suffix.lower()
    candidates = []
    if suffix == ".wav":
        candidates.extend((
            ["aplay", "-q", str(path)],
            ["paplay", str(path)],
        ))
    candidates.extend((
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
        ["afplay", str(path)],
        ["mpg123", "-q", str(path)],
    ))
    for command in candidates:
        if shutil.which(command[0]):
            subprocess.run(command, check=False)
            return True
    return False


def speak_with_espeak(text: str) -> bool:
    engine = "espeak-ng" if shutil.which("espeak-ng") else "espeak" if shutil.which("espeak") else None
    if not engine:
        return False
    subprocess.run([engine, "-s", "160", text], check=False)
    return True


def apply_music_action(provider, action: str) -> None:
    if provider is None or action in (None, "", "none"):
        return
    if action == "play":
        play = getattr(provider, "play", None)
        if play:
            play()
    elif action == "pause":
        current = provider.current() if hasattr(provider, "current") else None
        if current is not None and getattr(current, "is_playing", False):
            provider.toggle_playback()
    elif action == "skip_next":
        provider.skip(1)
    elif action == "skip_prev":
        provider.skip(-1)


class VoiceLoop:
    """One conversation at a time, run on a background thread."""

    def __init__(
        self,
        robot: Robot,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        tts_voice: str = DEFAULT_TTS_VOICE,
        playback_fn: Callable | None = None,
        provider=None,
    ) -> None:
        self.robot = robot
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.tts_voice = tts_voice
        self.playback_fn = playback_fn
        self.provider = provider
        self.history: list[tuple[str, str]] = []
        self.busy = False
        self._lock = threading.Lock()
        self._recorder: subprocess.Popen | None = None
        self._wav_path: Path | None = None
        self._max_timer: threading.Timer | None = None
        self._button = None
        self._closed = False

    def attach_gpio(self, pin: int = 17) -> bool:
        """Listen for a push button on a Pi GPIO pin. Returns True if attached.

        Wire a momentary button between the pin (default BCM 17, physical
        pin 11) and ground. The pin uses an internal pull-up.
        """
        try:
            from gpiozero import Button
        except ImportError:
            return False
        try:
            button = Button(pin, pull_up=True, bounce_time=0.05)
            button.when_pressed = self.press
            button.when_released = self.release
        except Exception:
            return False
        self._button = button
        return True

    def press(self) -> None:
        """Start listening. Safe to call from GPIO, a key, or a test."""
        with self._lock:
            if self._closed or self.busy or self._recorder is not None:
                return
            command = recorder_command()
            self.robot.cancel_demo()
            self.robot.set_mode("listening")
            if command is None:
                self._wav_path = None
                return
            handle, name = tempfile.mkstemp(prefix="desk-robot-", suffix=".wav")
            os.close(handle)
            path = Path(name)
            try:
                self._recorder = subprocess.Popen(command + [str(path)])
            except OSError:
                path.unlink(missing_ok=True)
                self._recorder = None
                self._wav_path = None
                return
            self._wav_path = path
            self._max_timer = threading.Timer(15.0, self.release)
            self._max_timer.daemon = True
            self._max_timer.start()

    def release(self) -> None:
        """Stop recording and start the conversation thread."""
        with self._lock:
            if self._closed or self.busy:
                return
            if self._max_timer is not None:
                self._max_timer.cancel()
                self._max_timer = None
            recorder = self._recorder
            path = self._wav_path
            self._recorder = None
            self._wav_path = None
            if recorder is None and path is None and self.robot.mode != "listening":
                return
            self.busy = True
        if recorder is not None:
            self._stop_recorder(recorder)
        thread = threading.Thread(
            target=self._run_conversation,
            args=(path,),
            daemon=True,
            name="robot-voice",
        )
        thread.start()

    def close(self) -> None:
        self._closed = True
        if self._max_timer is not None:
            self._max_timer.cancel()
        recorder = self._recorder
        self._recorder = None
        if recorder is not None:
            self._stop_recorder(recorder)
        if self._wav_path is not None:
            self._wav_path.unlink(missing_ok=True)
            self._wav_path = None
        button = self._button
        self._button = None
        if button is not None:
            close = getattr(button, "close", None)
            if close:
                close()

    def _run_conversation(self, wav_path: Path | None) -> None:
        try:
            self.robot.set_mode("thinking")
            user_text = self._hear(wav_path)
            if user_text is None:
                reply = GrokReply(
                    mode="error",
                    say="I could not find a microphone. On a laptop, press T to run the visual demo.",
                )
            elif not user_text:
                reply = GrokReply(mode="happy", say="I did not catch that. Please try again.")
            else:
                playback = self.playback_fn() if self.playback_fn else None
                reply = ask_grok(
                    user_text,
                    self.api_key,
                    model=self.model,
                    base_url=self.base_url,
                    playback=playback,
                    history=self.history,
                )
                self.history.append((user_text, reply.say))
                self.history = self.history[-4:]
            self._deliver(reply)
        except Exception as exc:
            log_voice_error("voice conversation", exc)
            self.robot.set_mode("error")
        finally:
            if wav_path is not None:
                wav_path.unlink(missing_ok=True)
            self.busy = False

    def _hear(self, wav_path: Path | None) -> str | None:
        """Return transcript text, '' if silent, or None if there is no mic."""
        if wav_path is None or not wav_path.exists() or wav_path.stat().st_size < 64:
            return None if wav_path is None else ""
        if not self.api_key:
            # No cloud STT, but a recording existed. Use a stand-in phrase
            # so demo_reply can still run.
            return "hello"
        try:
            return transcribe_audio(wav_path, self.api_key, base_url=self.base_url)
        except Exception as exc:
            log_voice_error("speech-to-text", exc)
            return ""

    def _deliver(self, reply: GrokReply) -> None:
        apply_music_action(self.provider, reply.music_action)
        if reply.say:
            self.robot.say(reply.say)
            self._speak(reply.say)
        if reply.show_music:
            self.robot.hold_mode = False
            self.robot.set_mode("music")
        else:
            self.robot.hold_mode = True
            self.robot.set_mode(reply.mode if reply.mode != "music" else "happy")

    def _speak(self, text: str) -> None:
        if self.api_key:
            try:
                audio = synthesize_speech(
                    text,
                    self.api_key,
                    base_url=self.base_url,
                    voice=self.tts_voice,
                )
                suffix = ".wav" if audio.startswith(b"RIFF") else ".mp3"
                with tempfile.NamedTemporaryFile(prefix="desk-robot-tts-", suffix=suffix, delete=False) as handle:
                    handle.write(audio)
                    path = Path(handle.name)
                try:
                    if play_audio_file(path):
                        return
                finally:
                    path.unlink(missing_ok=True)
            except Exception as exc:
                log_voice_error("text-to-speech", exc)
        if not speak_with_espeak(text):
            # Last resort: the face still shows speaking, with no audio.
            return

    @staticmethod
    def _stop_recorder(recorder: subprocess.Popen) -> None:
        if recorder.poll() is not None:
            return
        try:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=3)
        except Exception:
            recorder.kill()
            recorder.wait(timeout=3)
