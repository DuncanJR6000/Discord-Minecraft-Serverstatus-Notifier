export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/") {
      return new Response(`<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Minecraft Status prüfen</title>
  <style>
    body { min-height: 100vh; margin: 0; display: grid; place-items: center; background: #111827; color: #f9fafb; font-family: system-ui, sans-serif; }
    main { width: min(420px, calc(100% - 32px)); padding: 28px; border-radius: 16px; background: #1f2937; text-align: center; }
    button { width: 100%; border: 0; border-radius: 10px; padding: 14px; background: #5865F2; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }
  </style>
</head>
<body>
  <main>
    <h1>Minecraft Server</h1>
    <button onclick="location.href='/check'">Status prüfen</button>
  </main>
</body>
</html>`, {
        headers: { "Content-Type": "text/html;charset=UTF-8" },
      });
    }

    if (url.pathname === "/check") {
      const workflowUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW}/dispatches`;
      const response = await fetch(workflowUrl, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json",
          "User-Agent": "minecraft-status-worker",
        },
        body: JSON.stringify({ ref: "main" }),
      });

      if (!response.ok) {
        const detail = await response.text();
        return new Response(`GitHub-Auftrag fehlgeschlagen: ${response.status}<br>${detail}`, {
          status: 502,
          headers: { "Content-Type": "text/html;charset=UTF-8" },
        });
      }

      return new Response(`<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Prüfung gestartet</title>
<style>body{min-height:100vh;margin:0;display:grid;place-items:center;background:#111827;color:#f9fafb;font-family:system-ui,sans-serif}main{text-align:center}</style></head>
<body><main><h1>Prüfung gestartet</h1><p>Das Ergebnis erscheint in Discord.</p><p><a style="color:#57F287" href="/">Zurück</a></p></main></body></html>`, {
        headers: { "Content-Type": "text/html;charset=UTF-8" },
      });
    }

    return new Response("Nicht gefunden", { status: 404 });
  },
};
