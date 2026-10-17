from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import replace
from typing import Protocol

from .models import PlaybackInfo


class PlaybackProvider(Protocol):
    def current(self) -> PlaybackInfo | None: ...


class DemoSpotifyProvider:
    """Local fake playback source used before Spotify authorization is configured."""

    def __init__(self) -> None:
        self._track = PlaybackInfo(
            title="Robot Dreams",
            artist="Omar's Desk Robot",
            duration_ms=214_000,
            progress_ms=48_000,
            is_playing=True,
        )

    def current(self) -> PlaybackInfo:
        step = 1_000 if self._track.is_playing else 0
        progress = (self._track.progress_ms + step) % self._track.duration_ms
        self._track = replace(self._track, progress_ms=progress)
        return self._track

    def toggle_playback(self) -> None:
        self._track = replace(self._track, is_playing=not self._track.is_playing)


class SpotifyWebApiProvider:
    """Small Web API adapter; OAuth/PKCE setup will supply the access token later."""

    ENDPOINT = "https://api.spotify.com/v1/me/player"

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token or os.getenv("SPOTIFY_ACCESS_TOKEN")

    def current(self) -> PlaybackInfo | None:
        if not self.access_token:
            return None

        request = urllib.request.Request(
            self.ENDPOINT,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 204:
                    return None
                payload = json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
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

