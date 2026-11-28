"""Small local diagnostics for voice failures; never records user speech or secrets."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re


def log_voice_error(stage: str, error: BaseException) -> None:
    """Append a compact, secret-safe failure note for the Pi owner to inspect."""
    try:
        log_dir = Path.home() / ".local" / "state" / "desk-robot"
        log_dir.mkdir(parents=True, exist_ok=True)
        detail = str(error).replace("\n", " ")[:240]
        detail = re.sub(r"(?i)bearer\s+\S+", "Bearer [redacted]", detail)
        detail = re.sub(r"(?i)(api[_ -]?key\s*[=:]\s*)\S+", r"\1[redacted]", detail)
        status = getattr(error, "code", None)
        if status is not None:
            detail = f"HTTP {status}: {detail}"
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = f"{stamp} stage={stage} error={type(error).__name__}: {detail}\n"
        with (log_dir / "voice-errors.log").open("a", encoding="utf-8") as log:
            log.write(line)
    except Exception:
        # Diagnostics must never crash the robot UI or voice loop.
        pass
