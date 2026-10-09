# eLo on Alexa — morning checklist (card 0008)

## 0 · First, 30 seconds: the Test tab (probably why nothing reached eLo last night)
Alexa developer console → **DISENELO Presence** → **Test** tab → the dropdown at the top must say **Development**, not **Off**.
Then type `open elo`. If eLo answers, the current setup works. You still want a permanent address (below), because tonight's address dies when that Terminal window closes.

## 1 · Pick ONE option and double-click its file (in this folder)

| | Option | You need first | Time |
|---|---|---|---|
| **1** | `option1_ngrok.command` (**simplest**) | Free account at dashboard.ngrok.com/signup. Copy **Your Authtoken**, then **Domains → claim your free static domain** | ~5 min |
| **2** | `option2_cloudflare.command` (most robust) | Free Cloudflare account **with a domain on it**. disenelo.com's DNS is at Oracle, so this needs a spare or new domain | ~15 min+ |
| **3** | `option3_tailscale.command` | Free Tailscale account (the script installs the app and opens sign-in) | ~10 min |

If macOS says the file can't be opened: right-click → **Open** (first time only).

Each script:
- installs what it needs;
- asks only for what it can't know (token/domain/hostname);
- starts the tunnel with a **fixed address**, and offers to start it at login (say **y**);
- tests the address from the internet (it should report "reached eLo's listener");
- saves it as `ALEXA_TUNNEL_URL` in `~/elo-ai/.env` (backup kept);
- copies `https://…/alexa` to your clipboard and prints the 6 Alexa console steps (paste into Endpoint → Save → Test tab on **Development**).

After that the address never changes, so there's no console editing after restarts. You can close last night's cloudflared Terminal window.

## Safety (same for all three)
The tunnel reaches **only** eLo's Alexa listener (port 5051), which serves `/alexa` and its own short-lived voice clips and accepts only Amazon-signed requests for your skill. eLo's main server (5050) is never exposed. Cloudflare's config forwards `/alexa` only.

## Then
"Alexa, open elo" on the Echo Dot-Studio. Builder 3 checks the logs (what Amazon heard, which model answered, how long it took, eLo's voice or not).
