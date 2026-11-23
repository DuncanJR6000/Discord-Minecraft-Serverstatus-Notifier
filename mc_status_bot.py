"""
Einmaliger Status-Check für GitHub Actions.
Postet per Discord-Webhook, wenn der Minecraft-Server online/offline geht.
Der letzte bekannte Zustand wird in state.json gespeichert.
"""
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from mcstatus import JavaServer

MC_ADDRESS = os.environ.get("MC_ADDRESS", "").strip()
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
STATE_FILE = Path("state.json")
RETRIES = 3          # Versuche, bevor "offline" gilt
RETRY_DELAY = 10     # Sekunden zwischen den Versuchen
LOCAL_TIMEZONE = ZoneInfo("Europe/Berlin")


if not MC_ADDRESS:
    raise RuntimeError("MC_ADDRESS fehlt oder ist leer.")
if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL fehlt oder ist leer.")


def format_relative_time(timestamp):
    if not timestamp:
        return ""

    try:
        when = datetime.fromisoformat(timestamp)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        when = when.astimezone(LOCAL_TIMEZONE)
    except (TypeError, ValueError):
        return ""

    now = datetime.now(LOCAL_TIMEZONE)
    day_difference = (now.date() - when.date()).days
    clock = when.strftime("%H:%M")

    if day_difference == 0:
        return f"heute um {clock} Uhr"
    if day_difference == 1:
        return f"gestern um {clock} Uhr"
    if day_difference == -1:
        return f"morgen um {clock} Uhr"
    return f"am {when.strftime('%d.%m.%Y')} um {clock} Uhr"


def read_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def offline_title(state):
    version = state.get("version")
    players_online = state.get("players_online")
    players_max = state.get("players_max")

    details = []
    if version:
        details.append(f"Version {version}")
    if players_online is not None and players_max is not None:
        details.append(f"Spieler {players_online}/{players_max}")

    relative_time = format_relative_time(state.get("last_seen"))
    if relative_time:
        details.append(relative_time)

    suffix = f" {' '.join(details)}" if details else ""
    return f"🔴 Server ist offline!{suffix}"


def check():
    server = JavaServer.lookup(MC_ADDRESS, timeout=5)
    for attempt in range(RETRIES):
        try:
            return server.status()
        except Exception:
            if attempt < RETRIES - 1:
                time.sleep(RETRY_DELAY)
    return None


def post(embed):
    body = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "mc-status-actions/1.0",
        },
    )
    urllib.request.urlopen(req, timeout=15).read()


def main():
    status = check()
    online = status is not None
    manual_run = os.environ.get("NOTIFY_ON_MANUAL", "").lower() == "true"
    state = read_state()
    old = state.get("online")

    if old is None or old != online or manual_run:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        if online:
            post({
                "title": "🟢 Server ist online!",
                "color": 0x57F287,
                "timestamp": now_iso,
                "fields": [
                    {"name": "Version", "value": status.version.name, "inline": True},
                    {"name": "Spieler", "value": f"{status.players.online}/{status.players.max}", "inline": True},
                ],
            })
            state = {
                "online": True,
                "version": status.version.name,
                "players_online": status.players.online,
                "players_max": status.players.max,
                "last_seen": now_iso,
            }
        else:
            post({
                "title": offline_title(state),
                "color": 0xED4245,
                "timestamp": now_iso,
            })
            state["online"] = False

    STATE_FILE.write_text(json.dumps(state))
    print("online" if online else "offline")


if __name__ == "__main__":
    main()
