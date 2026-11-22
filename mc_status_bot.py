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

from mcstatus import JavaServer

MC_ADDRESS = os.environ.get("MC_ADDRESS", "").strip()
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
STATE_FILE = Path("state.json")
RETRIES = 3          # Versuche, bevor "offline" gilt
RETRY_DELAY = 10     # Sekunden zwischen den Versuchen


if not MC_ADDRESS:
    raise RuntimeError("MC_ADDRESS fehlt oder ist leer.")
if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL fehlt oder ist leer.")


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
            "User-Agent": "mc-status-actions/1.0",  # Discord blockt den Standard-UA
        },
    )
    urllib.request.urlopen(req, timeout=15).read()


def main():
    status = check()
    online = status is not None
    manual_run = os.environ.get("NOTIFY_ON_MANUAL", "").lower() == "true"

    old = None
    if STATE_FILE.exists():
        old = json.loads(STATE_FILE.read_text()).get("online")

    if old is None or old != online or manual_run:
        now = datetime.now(timezone.utc).isoformat()
        if online:
            post({
                "title": "🟢 Server ist online!",
                "description": f"`{MC_ADDRESS}` ist jetzt erreichbar.",
                "color": 0x57F287,
                "timestamp": now,
                "fields": [
                    {"name": "Version", "value": status.version.name, "inline": True},
                    {"name": "Spieler",
                     "value": f"{status.players.online}/{status.players.max}",
                     "inline": True},
                ],
            })
        else:
            post({
                "title": "🔴 Server ist offline!",
                "description": f"`{MC_ADDRESS}` ist nicht mehr erreichbar.",
                "color": 0xED4245,
                "timestamp": now,
            })

    STATE_FILE.write_text(json.dumps({"online": online}))
    print("online" if online else "offline")


if __name__ == "__main__":
    main()
