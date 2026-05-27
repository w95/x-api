import json
import logging
from pathlib import Path

from .deps import get_api

log = logging.getLogger("x-api.sessions")

SESSIONS_FILE = Path(__file__).resolve().parents[1] / "sessions.jsonl"


async def load_sessions() -> int:
    """Read sessions.jsonl and register each cookie session in the twscrape pool.

    File format (one JSON object per line):
        {"kind":"cookie","username":"...","auth_token":"...","ct0":"..."}
    """
    if not SESSIONS_FILE.exists():
        log.warning("sessions file missing: %s", SESSIONS_FILE)
        return 0

    api = get_api()
    existing = {a.username for a in await api.pool.get_all()}
    added = 0

    for i, raw in enumerate(SESSIONS_FILE.read_text().splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("sessions.jsonl line %d is not valid JSON, skipping", i)
            continue
        if entry.get("kind") != "cookie":
            log.warning("line %d: only kind=cookie supported, got %r", i, entry.get("kind"))
            continue

        username = entry.get("username") or f"session{i}"
        if username in existing:
            continue

        cookies = f"auth_token={entry['auth_token']}; ct0={entry['ct0']}"
        await api.pool.add_account(
            username=username,
            password="x",
            email="x@x",
            email_password="x",
            cookies=cookies,
        )
        await api.pool.set_active(username, True)
        added += 1

    return added
