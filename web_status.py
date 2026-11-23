"""Einfaches Web-Interface zum Prüfen des Minecraft-Serverstatus."""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, render_template_string, request
from mcstatus import JavaServer

MC_ADDRESS = os.environ.get("MC_ADDRESS", "").strip()
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
STATE_FILE = Path("state.json")
LOCAL_TIMEZONE = ZoneInfo("Europe/Berlin")

if not MC_ADDRESS:
    raise RuntimeError("MC_ADDRESS fehlt oder ist leer.")
if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL fehlt oder ist leer.")

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Minecraft Server Status</title>
  <style>
    html, body { margin: 0; min-height: 100%; font-family: system-ui, sans-serif; }
    body { display: grid; place-items: center; background: #111827; color: #f9fafb; }
    main { width: min(420px, calc(100% - 32px)); padding: 28px; border-radius: 16px; background: #1f2937; text-align: center; box-shadow: 0 16px 40px rgba(0,0,0,.35); }
    button { width: 100%; border: 0; border-radius: 10px; padding: 14px 18px; background: #5865F2; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }
    button:hover { background: #4752c4; }
    .online { color: #57F287; }
    .offline { color: #ED4245; }
  </style>
</head>
<body>
  <main>
    <h1>Minecraft Server</h1>
    {% if result %}
      <h2 class="{{ 'online' if online else 'offline' }}">{{ 'Online' if online else 'Offline' }}</h2>
      {% if notified %}<p>Discord-Nachricht gesendet.</p>{% else %}<p>Status hat sich nicht verändert.</p>{% endif %}
    {% else %}
      <p>Serverstatus prüfen</p>
    {% endif %}
    <form method="post">
      <button type="submit">Status prüfen</button>
    </form>
  </main>
</body>
</html>
"""


def read_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def format_relative_time(timestamp):
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


def offline_title(state):
    version = state.get("version") or "Unbekannt"
    players_online = state.get("players_online")
    players_max = state.get("players_max")
    if players_online is not None and players_max is not None:
        players = f"{players_online}/{players_max}"
    else:
        players = "-/-"
    relative_time = format_relative_time(state.get("last_seen"))
    time_text = f" {relative_time}" if relative_time else ""
    return f"🔴 Server ist offline! Version {version} Spieler {players}{time_text}"


def post_embed(embed):
    body = json.dumps({"embeds": [embed]}).encode()
    request = urllib.request.Request(
        WEBHOOK_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "mc-status-web/1.0",
        },
    )
    urllib.request.urlopen(request, timeout=15).read()


def check_server():
    try:
        server = JavaServer.lookup(MC_ADDRESS, timeout=5)
        status = server.status()
        return True, status
    except Exception:
        return False, None


@app.route("/", methods=["GET", "POST"])
def index():
    result = False
    online = False
    notified = False

    if request.method == "POST":
        online, status = check_server()
        previous = read_state()

        if previous.get("online") != online:
            now = datetime.now(timezone.utc).isoformat()
            if online:
                post_embed({
                    "title": "🟢 Server ist online!",
                    "color": 0x57F287,
                    "timestamp": now,
                    "fields": [
                        {"name": "Version", "value": status.version.name, "inline": True},
                        {"name": "Spieler", "value": f"{status.players.online}/{status.players.max}", "inline": True},
                    ],
                })
                previous = {
                    "online": True,
                    "version": status.version.name,
                    "players_online": status.players.online,
                    "players_max": status.players.max,
                    "last_seen": now,
                }
            else:
                post_embed({
                    "title": offline_title(previous),
                    "color": 0xED4245,
                    "timestamp": now,
                })
                previous["online"] = False

            STATE_FILE.write_text(json.dumps(previous), encoding="utf-8")
            notified = True

        result = True

    return render_template_string(PAGE, result=result, online=online, notified=notified)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
