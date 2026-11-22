# Discord Minecraft Server Status Notifier

GitHub Actions checks a Minecraft Java server every five minutes and sends a
Discord webhook message when its status changes. The first run and every manual
workflow run also send a notification.

## Setup

1. Add the Discord webhook URL as an Actions secret named
   `DISCORD_WEBHOOK_URL`.
2. Add the server address (for example `mc.example.net:25565`) as an Actions
   variable named `MC_ADDRESS`.
3. Ensure the workflow can write repository contents. The workflow requests
   this permission with `contents: write` so it can commit `state.json`.
4. Run **MC Status** once manually from the repository's **Actions** tab to
   initialize the saved state and verify the Discord webhook.

The workflow is in `.github/workflows/mc-status.yml`; the check is implemented
in `mc_status_bot.py`. If you want to keep the server address private, store it
as an Actions secret instead and change the workflow's `MC_ADDRESS` expression
from `vars.MC_ADDRESS` to `secrets.MC_ADDRESS`.
