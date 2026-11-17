---
name: hermes-cron-web-toolset
description: Use when a Hermes cron agent lacks web access in cron.
---

# Hermes Cron Web-Toolset Fix

When a cron job (e.g. "Skor & Hasil Bola Real-time") reports it has NO web access
("I only have WordPress MCP tools", "no web_search/browser/web_extract"), the web
toolset is not reaching the cron-agent. This is a 2-part fix — both must be right,
plus a restart.

## Root causes (both must be checked)

1. **Wrong toolset name in jobs.json.** `enabled_toolsets` must use TOOLSET names,
   not TOOL names. From `tools_config.py` line 97: toolset `"web"` = tools
   `web_search, web_extract`. Setting `enabled_toolsets: ["web_search","web_extract"]`
   silently fails — nothing loads. Must be `["web"]` (also `"browser"`, `"search"`,
   `"vision"` are valid toolset names).
2. **No available web backend.** `check_web_api_key()` gates web_search/web_extract.
   Default backend `firecrawl` needs `FIRECRAWL_API_KEY` (often unset). If no API key,
   install `ddgs` (DuckDuckGo backend, no key): `ddgs`=package-importable → available.

## Steps

```bash
# 1. Locate the profile's cron jobs.json
#    e.g. /opt/data/profiles/<name>/cron/jobs.json
#    Backup first: cp jobs.json jobs.json.bak-$(date +%H%M%S)

# 2. Fix enabled_toolsets to toolset names (python, not yaml.dump)
python3 - <<'PY'
import json
p="/opt/data/profiles/bang_ucok/cron/jobs.json"
d=json.load(open(p))
jobs = d if isinstance(d,list) else d.get("jobs",d)
if isinstance(jobs,dict): jobs=list(jobs.values())
for j in jobs:
    if isinstance(j,dict) and j.get("enabled_toolsets"):
        j["enabled_toolsets"]=["web"]   # toolset name, not web_search
json.dump(d,open(p,"w"),indent=2)
print("fixed")
PY

# 3. Install ddgs web backend (no API key) into the Hermes venv
/opt/hermes-v0204/.venv/bin/pip install ddgs
/opt/hermes-v0204/.venv/bin/python -c "import ddgs; print('ddgs ok')"

# 4. Verify availability (should print True)
HERMES_HOME=/opt/data/profiles/<name> /opt/hermes-v0204/.venv/bin/python -c \
  "from tools.web_tools import check_web_api_key; print(check_web_api_key())"

# 5. Restart the gateway (USER runs this — agent restart is blocked by guard)
#    /usr/bin/systemctl --user restart hermes-gateway-<name>.service
#    then check: is-active → active, and PID changed

# 6. Trigger a manual run to confirm
HERMES_HOME=/opt/data/profiles/<name> /opt/hermes-v0204/.venv/bin/python \
  -m hermes_cli.main cron run <job_id>
#    Check cron runs: hermes_cli.main cron runs <job_id> → look for source=direct completed
#    Check output: cron/output/<job_id>/*.md → "## Response" should show real fetched data
```

## Verification

- `check_web_api_key` in gateway log no longer returns `False`.
- `hermes cron status` shows scheduler running.
- Manual run `source=direct` → `completed` (not "Fire claim lost").
- Output file contains real data (actual scores / honest "no matches" reasoning), NOT
  "This is a WordPress content-management executor".

## Pitfalls

- A manual `cron run` that overlaps a scheduled tick can both fire; one wins the fire
  claim and the other logs "Fire claim lost; execution was not started" — harmless.
- Do NOT edit config.yaml with `yaml.dump` (known Hermes hazard) — use sed/patch/json.
- If the job still falls to fallback provider, check the job's own `provider` creds
  (e.g. `xiaomi` with no XIAOMI_API_KEY) — that's a separate auth issue, not toolset.
- **Don't chase a false alarm in standalone Python**: running
  `from agent.web_search_registry import _providers` outside the gateway prints
  `[]` (empty) even though web providers ARE registered. Providers register at
  gateway import-time, not in a bare script — so an empty registry in a standalone
  probe is normal and NOT evidence the web backend is missing. Trust
  `check_web_api_key()` as the authoritative gate; ignore `_providers` from scripts.
- Only the LAST gateway PID matters when confirming a restart landed: check
  `ps aux | grep '<name> gateway run'` and confirm the PID differs from the
  pre-restart one (e.g. 761224 → 777834). A stale-still-purple PID means the
  config/skill-cabinet hasn't reloaded.
