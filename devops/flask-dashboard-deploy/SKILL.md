---
name: flask-dashboard-deploy
description: "Deploy Flask dashboards to VPS safely without breaking prod."
---

# Flask Dashboard Deployment

## Rule: NEVER touch production without backup
1. Backup dulu: `cp app.py app.py.bak-$(date +%m%d)`
2. Edit copy dulu, test locally, baru push ke server
3. Kalau error syntax → RESTORE dari backup langsung

## Restart Flask safely
```bash
ssh -p 22022 root@IP "pkill -f 'app.py'; sleep 1; cd /dir && nohup python app.py >/dev/null 2>&1 &"
```
- JANGAN pakai `pkill -9` — data bisa corrupt
- SELALU verify: `ps aux | grep app.py | grep -v grep`
- SELALU test: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:PORT/`

## CSS fixes — HATI-HATI
- Jangan ubah CSS yang sudah jalan tanpa understanding context
- Test CSS di browser dulu sebelum push
- Kalau user bilang "restore" → RESTORE, jangan coba fix lagi

## Common mistakes (JANGAN ULANG)
- ❌ Python string + JS inline = SyntaxError
- ❌ display:block di table = layout hancur
- ❌ Edit CSS tanpa test = dashboard mati
- ❌ "Fixed" tanpa verify = user marah
