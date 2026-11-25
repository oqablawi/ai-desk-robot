from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from dataclasses import replace
from typing import Callable, Protocol

from .models import PlaybackInfo


class PlaybackProvider(Protocol):
    def current(self) -> PlaybackInfo | None: ...


class BackgroundPlaybackProvider:
    """Keep slow network calls away from Tk's animation thread."""

    def __init__(self, provider: PlaybackProvider, poll_seconds: float = 2.0) -> None:
        self.provider = provider
        self.poll_seconds = poll_seconds
        self.index = 0
        self._current: PlaybackInfo | None = None
        self._actions: queue.Queue[tuple[str, tuple]] = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="spotify-worker")
        self._thread.start()

    def current(self) -> PlaybackInfo | None:
        return self._current

    def toggle_playback(self) -> None:
        self._actions.put(("toggle_playback", ()))

    def play(self) -> None:
        self._actions.put(("play", ()))

    def skip(self, direction: int = 1) -> None:
        self._actions.put(("skip", (direction,)))

    def seek(self, fraction: float) -> None:
        self._actions.put(("seek", (fraction,)))

    @property
    def is_demo(self) -> bool:
        return getattr(self.provider, "is_demo", False)

    @property
    def index(self) -> int:
        return getattr(self.provider, "index", 0)

    def close(self) -> None:
        self._stop.set()

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                action, args = self._actions.get(timeout=self.poll_seconds)
                getattr(self.provider, action)(*args)
            except queue.Empty:
                pass
            try:
                self._current = self.provider.current()
            except Exception:
                # A display must remain responsive through Wi-Fi/API failures.
                continue


class DemoSpotifyProvider:
    """Local fake playback source used before Spotify authorization is configured."""

    is_demo = True
    TRACKS = (
        PlaybackInfo("Robot Dreams", "Omar's Desk Robot", 214_000, 0, True),
        PlaybackInfo("Little Orbit", "The Desktop Sessions", 183_000, 0, True),
        PlaybackInfo("After Hours", "Soft Circuit", 246_000, 0, True),
    )

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._updated = clock()
        self.index = 0
        self._progress_ms = 0.0
        # Start paused so the laptop opens on the face, not the music screen.
        self.is_playing = False

    def _advance(self) -> None:
        now = self._clock()
        if self.is_playing:
            self._progress_ms += max(0.0, now - self._updated) * 1000
            # Bound the work if the laptop wakes after hours asleep.
            self._progress_ms %= sum(track.duration_ms for track in self.TRACKS)
            while self._progress_ms >= self.TRACKS[self.index].duration_ms:
                self._progress_ms -= self.TRACKS[self.index].duration_ms
                self.index = (self.index + 1) % len(self.TRACKS)
        self._updated = now

    def current(self) -> PlaybackInfo:
        self._advance()
        return replace(self.TRACKS[self.index], progress_ms=int(self._progress_ms), is_playing=self.is_playing)

    def toggle_playback(self) -> None:
        self._advance()
        self.is_playing = not self.is_playing

    def play(self) -> None:
        self._advance()
        self.is_playing = True

    def skip(self, direction: int = 1) -> None:
        self._advance()
        self.index = (self.index + direction) % len(self.TRACKS)
        self._progress_ms = 0.0

    def seek(self, fraction: float) -> None:
        self._advance()
        # Keep an end-of-bar click on this song until the next clock tick.
        self._progress_ms = min(max(fraction, 0.0), 1.0) * (self.TRACKS[self.index].duration_ms - 1)


class SpotifyWebApiProvider:
    """Spotify metadata/control client with refreshable PKCE tokens."""

    is_demo = False
    ENDPOINT = "https://api.spotify.com/v1/me/player"
    TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"

    def __init__(self, access_token: str | None = None, token_file: str | Path = ".spotify-token.json") -> None:
        self.access_token = access_token or os.getenv("SPOTIFY_ACCESS_TOKEN")
        self.token_file = Path(token_file)
        self.refresh_token: str | None = None
        self.expires_at = 0.0
        self.index = 0
        self._load_token()

    def _load_token(self) -> None:
        if self.access_token or not self.token_file.exists():
            return
        try:
            data = json.loads(self.token_file.read_text(encoding="utf-8"))
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.expires_at = float(data.get("expires_at", 0))
        except (OSError, ValueError, TypeError):
            return

    def _save_token(self, data: dict) -> None:
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.expires_at = time.time() + int(data.get("expires_in", 3600)) - 60
        payload = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
        }
        self.token_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _refresh_if_needed(self) -> None:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        if not self.refresh_token or not client_id or time.time() < self.expires_at:
            return
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": client_id,
        }).encode()
        request = urllib.request.Request(self.TOKEN_ENDPOINT, data=body)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                self._save_token(json.load(response))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            return

    def _request(self, method: str = "GET", endpoint: str | None = None, body: bytes | None = None):
        self._refresh_if_needed()
        if not self.access_token:
            return None
        request = urllib.request.Request(
            endpoint or self.ENDPOINT,
            data=body,
            method=method,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return None if response.status == 204 else json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            return None

    def current(self) -> PlaybackInfo | None:
        payload = self._request()
        if not payload:
            return None

        item = payload.get("item") or {}
        artists = ", ".join(
            artist.get("name", "") for artist in item.get("artists", [])
        ).strip(", ")
        images = (item.get("album") or {}).get("images") or []
        return PlaybackInfo(
            title=item.get("name") or "Unknown title",
            artist=artists or "Unknown artist",
            duration_ms=int(item.get("duration_ms") or 0),
            progress_ms=int(payload.get("progress_ms") or 0),
            is_playing=bool(payload.get("is_playing")),
            album_art_url=images[0].get("url") if images else None,
        )

    def toggle_playback(self) -> None:
        playback = self.current()
        endpoint = self.ENDPOINT + ("/pause" if playback and playback.is_playing else "/play")
        self._request("PUT", endpoint, b"")

    def play(self) -> None:
        self._request("PUT", self.ENDPOINT + "/play", b"")

    def skip(self, direction: int = 1) -> None:
        action = "next" if direction >= 0 else "previous"
        self._request("POST", self.ENDPOINT + f"/{action}", b"")

    def seek(self, fraction: float) -> None:
        playback = self.current()
        if playback:
            position = int(playback.duration_ms * min(1.0, max(0.0, fraction)))
            self._request("PUT", self.ENDPOINT + f"/seek?position_ms={position}", b"")


def authorize_spotify(client_id: str, redirect_uri: str, token_file: str | Path) -> None:
    """Run a one-time local OAuth PKCE login and save refreshable tokens."""
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(24)
    result: dict[str, str] = {}

    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - required by BaseHTTPRequestHandler
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if query.get("state", [None])[0] != state:
                self.send_error(400, "OAuth state mismatch")
                return
            result["code"] = query.get("code", [""])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Spotify connected. You may close this tab.")

        def log_message(self, *_args):
            return

    parsed = urllib.parse.urlparse(redirect_uri)
    server = HTTPServer((parsed.hostname or "127.0.0.1", parsed.port or 8765), Callback)
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "user-read-playback-state user-modify-playback-state",
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    })
    webbrowser.open("https://accounts.spotify.com/authorize?" + params)
    server.handle_request()
    if not result.get("code"):
        raise RuntimeError("Spotify authorization did not return a code")
    body = urllib.parse.urlencode({
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(SpotifyWebApiProvider.TOKEN_ENDPOINT, data=body), timeout=10) as response:
        SpotifyWebApiProvider(token_file=token_file)._save_token(json.load(response))

