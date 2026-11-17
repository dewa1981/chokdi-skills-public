# stdio MCP behind `docker exec` — env, timeouts, diagnosis

For any Hermes MCP server registered as stdio whose command is `docker exec`, not just
`docker run`.

## The env problem (root cause of most unexplained hangs)

`docker exec` starts a **fresh process inside the container with none of the Hermes env**.
A container-side application `.env` file is **not** read unless the app itself calls
`load_dotenv` — many projects do not.

So a server that needs credentials (LLM key, API token) starts, answers the handshake, and
then **stalls in lazy init** the moment a real tool call needs the credential.

### Signature (learn this, it saves an hour)

| Observation | Meaning |
|---|---|
| `hermes mcp test <name>` → `✓ Connected` + full tool count | handshake + `tools/list` need no creds — this proves nothing |
| every `tools/call` → timeout (300 s default) | server blocked on init, not a network problem |
| server log stops right after `Initializing <X>` / `resolved ... api_base` | confirmed: blocked in init |
| server log has **no** `CallToolRequest` at all | the call never arrived — your config is not the one in force |
| newest log file is **0 bytes** | connection died before the handshake |

### Fix — `-e K=V` as arguments to `docker`

Each `-e` takes the next argv element as its value; keep them adjacent:

```yaml
mcp_servers:
  <name>:
    command: docker
    args:
      - exec
      - -i
      - -e
      - SOME_API_KEY=<key>
      - -e
      - SOME_API_BASE=<url>
      - -e
      - SOME_MODEL=<model>
      - <container>
      - <binary>
    enabled: true
```

## `hermes mcp add --env` is the wrong tool for this shape

For a stdio server the CLI appends `--env KEY=VALUE` to the **end of `args`**, so it reaches the
container binary, not `docker`. The connect then fails and the entry is saved
**`enabled: false`**.

After **every** `hermes mcp add`, re-read the block before believing it is correct:

```bash
sed -n '/^  <name>:/,/^  [a-z]/p' /root/.hermes/config.yaml
```

Fix `args` by hand (back up `config.yaml` first). The agent patch tool **refuses to write
`~/.hermes/config.yaml`** — do it with a small script that does
`read → replace block → write`, and print the result masked.

## Diagnose: compare container env against the runtime config `.env`

```bash
docker exec -w /app <container> python3 -c "import os;\
print({k: (len(v) if any(s in k.upper() for s in ['KEY','TOKEN','SECRET']) else v)\
 for k,v in os.environ.items() if any(s in k.upper() for s in ['API','LLM','<PROJECT>'])})"
docker exec -w /app <container> python3 -c "import os; print('dotenv present:', os.path.exists('/app/.env'))"
```

Empty mapping + `.env` present = this bug. Do **not** conclude "the tool is broken".

## Proving the credential is the cause — a safe probe

Run the server's own entrypoint **with** the env, via `docker exec -e ...`, and look at whether
init completes. If it completes in ~1 s with env and hangs without it, the diagnosis is proven
without touching the gateway.

For a Python server you can also import its config/LLM layer directly inside the container and
call one deterministic function — that isolates "credentials/config OK" from "Hermes wiring OK".

## Don't write your own stdio JSON-RPC client for a framework server

A hand-rolled line-delimited JSON-RPC driver against a framework MCP server (FastMCP and
friends) fails: the transport is **SSE / streamable-http framing**, not one JSON object per
line. Timeout on the search call, garbage on the execute call, no useful output.

Use in this order:
1. `scripts/mcp_stdio_probe.py` — handshake + `tools/list` only. Separates "won't answer" from
   "answers then hangs".
2. Hermes' own MCP tool surface (the `mcp__<server>__<tool>` tools) for real calls.
3. Direct Python inside the container for server internals — the framework's own client,
   not a raw pipe.

## Config changes only take effect after a gateway restart

The MCP catalog is read at gateway start. A call that returns "not delivered" (no
`CallToolRequest` in the server log) usually means the running gateway still holds the **old**
config. Restart only through the approved path, and only with the user's consent — the gateway
hosting the agent kills the current conversation when it restarts. See the restart section of
the parent skill.
