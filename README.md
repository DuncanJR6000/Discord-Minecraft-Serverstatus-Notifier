# Discord Minecraft Server Status Notifier

Der Serverstatus wird auf zwei Arten geprüft:

- GitHub Actions prüft automatisch alle 30 Minuten.
- Eine lokale oder öffentlich gehostete Webseite kann jederzeit per Knopf geprüft werden.

Die Discord-Nachricht wird nur gesendet, wenn sich der Status von online zu offline oder umgekehrt verändert hat.

## GitHub Actions

1. Lege `DISCORD_WEBHOOK_URL` als Repository-Geheimnis an.
2. Lege `MC_ADDRESS` als Repository-Variable an.
3. Aktiviere das Schreiben in GitHub Actions.
4. Starte `MC Status` einmal manuell, um `state.json` zu initialisieren.

Der 30-Minuten-Timer steht in `.github/workflows/mc-status.yml`. Die Prüfung erfolgt in `mc_status_bot.py`.

## Webseite

`web_status.py` stellt eine Statusseite mit einem **Status prüfen**-Button bereit.

```shell
export MC_ADDRESS="mc.example.net:25565"
export DISCORD_WEBHOOK_URL="DEIN-DISCORD-WEBHOOK"

source .venv/bin/activate
pip install -r requirements.txt
python web_status.py
```

Danach ist die Seite unter <http://127.0.0.1:5000> verfügbar.

Für einen fest erreichbaren Link wird die Website auf einem VPS, Raspberry Pi oder einem anderen dauerhaft laufenden Python-Hostingdienst betrieben.

Es wird keine Discord-Bot-Anwendung, kein Bot-Tokenn oder keine Slash-Command-Konfiguration benötigt.

## Cloudflare-Worker mit Status-Button

Der Worker stellt eine öffentliche URL bereit. Beim Klick startet er den GitHub-Workflow über `workflow_dispatch`.

1. Öffne Cloudflare Dashboard → **Workers & Pages** → **Create application**.
2. Erstelle einen Worker und lade den Inhalt aus `cloudflare-worker/src/index.js` hoch.
3. Trage in `cloudflare-worker/wrangler.toml` deinen GitHub-Benutzernamen ein.
4. Lege beim Worker unter **Settings → Variables and Secrets** das Geheimnis `GITHUB_TOKEN` an.
5. Der Token benötigt für das Repository die Berechtigung **Actions: Read and write**.
6. Für lokale Bereitstellung via Wrangler:

```shell
cd cloudflare-worker
npx wrangler deploy
npx wrangler secret put GITHUB_TOKEN
```

Die Worker-URL öffnet die Seite mit dem Status-Button. Der Button startet `mc-status.yml` im Modus `change-only`; ein unveränderter Status erzeugt keine Discord-Nachricht.
