---
name: opencode
description: "Delegate coding to OpenCode CLI (features, PR review)."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

Use [OpenCode](https://opencode.ai) as an autonomous coding worker orchestrated by Hermes terminal/process tools. OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.

## When to Use

- User explicitly asks to use OpenCode
- You want an external coding agent to implement/refactor/review code
- You need long-running coding sessions with progress checks
- You want parallel task execution in isolated workdirs/worktrees

## Prerequisites

- OpenCode installed: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- Auth configured: `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)
- Verify: `opencode auth list` should show at least one provider
- Git repository for code tasks (recommended)
- `pty=true` for interactive TUI sessions

## Install (macOS/Linux, no node needed)

The official installer drops a standalone binary — no npm, brew, or sudo:

```
curl -fsSL https://opencode.ai/install | bash     # → ~/.opencode/bin/opencode
```

**It only appends the PATH export to `~/.zshrc`.** macOS login/non-interactive shells read
`~/.zprofile` instead, so after a "successful" install `ssh mac 'opencode --version'` and
`zsh -lc opencode` still say `command not found` while an interactive terminal works. Add the
export to `~/.zprofile` as well (back it up first), then verify all three ways:

```
zsh -lc 'opencode --version'   # login shell (what SSH/cron get)
zsh -ic 'opencode --version'   # interactive
~/.opencode/bin/opencode --version   # absolute path, always works
```

OpenCode ships free models, so it is usable with zero API keys; a provider login is optional.

## Desktop app (GUI) — separate line from the CLI

"Install the OpenCode GUI" means **OpenCode Desktop**, an Electron app that is versioned on its own
line (2.x while the CLI is 1.x). It is not shipped by the CLI installer and has no CLI subcommand
(`opencode --help` lists `acp`, `service`, `mini`, `run` — no `web`/`gui`).

macOS Apple Silicon, no Homebrew needed (338 MB DMG):

```bash
curl -fL -o ~/Downloads/opencode-desktop.dmg \
  https://opencode.ai/download/latest/darwin-aarch64-dmg      # redirects to /files/bin/<ver>/opencode-desktop-mac-arm64.dmg
MNT=$(hdiutil attach -nobrowse ~/Downloads/opencode-desktop.dmg | tail -1 | awk '{print $NF}')
cp -R "$MNT"/OpenCode.app /Applications/
hdiutil detach "$MNT" -quiet
xattr -dr com.apple.quarantine /Applications/OpenCode.app     # else Gatekeeper blocks first launch
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' /Applications/OpenCode.app/Contents/Info.plist
```

Other platform paths follow the same shape: `/download/latest/darwin-x64-dmg`, `linux-x64-deb`,
`linux-x64-rpm`, `windows-x64-nsis`. With Homebrew present: `brew install --cask opencode-desktop`.

- **Credentials are shared, so no re-login:** Desktop reads `~/.local/share/opencode/auth.json`.
  If the CLI is already authenticated with ChatGPT-plan OAuth, Desktop opens on the same model and
  shows **$0.00 spent** — the plan quota is consumed, not per-token billing. Confirm with
  `opencode auth list` (expect `OpenAI oauth`) before claiming it is free.
- Verify the GUI actually runs headlessly-installed: `open -a /Applications/OpenCode.app`, then
  `pgrep -fl OpenCode` must show the main binary plus renderer/GPU helpers.
- Launching it opens a **Default Project** workspace (an empty folder); the user must point it at a
  real repo via the workspace selector before it is useful. Say so instead of assuming it works.
- The in-app version banner may offer `/update` to the next major (2.x). Treat a major jump as a
  separate change: finish evaluating the working version first, upgrade on explicit request.

## GUI alternative: OpenBot (ACP orchestrator)

[OpenBot](https://openbot.run) is a separate desktop team workspace from
`nightly-labs/openbot`, not OpenCode Desktop. Check documentation at the installed release tag:
provider protocols differ (OpenCode uses ACP; Codex uses its app server). For a remote Mac install,
load `openbot-macos-ops`.

- Discover the official release through GitHub's release API; validate its arm64 asset digest,
  codesign, and notarization before installation. A source clone is unnecessary for desktop use.
- OpenBot can use a compatible existing OpenCode executable or download its own managed runtime.
  An explicit `OPENBOT_OPENCODE_PATH` override takes precedence. Do not upgrade the user's system
  CLI just because OpenBot offers a managed download; check actual runtime discovery first.
- The v0.60.0 documentation supports a free-model onboarding path without account/login. OpenBot
  account sign-in is optional; never tell users email/OTP is universally required.
- Provider credentials and model availability must be verified in OpenBot itself. Working OAuth
  in OpenCode Desktop is not proof that an OpenBot agent has inherited that authentication.
- First-launch consent and macOS Computer Use permissions are distinct from installing the bundle.
  Do not bypass them, and do not claim end-to-end readiness from a running process alone.
- Local-first does not mean offline: cloud model prompts leave the device. Desktop work requires
  the app/host to stay available; Linux server/Docker deployments are a separate supported path.
- Check licensing before business rollout: v0.60.0 uses PolyForm Noncommercial with separate
  commercial licensing. Do not buy a license or enroll a paid plan without user approval.

## Binary Resolution (Important)

Shell environments may resolve different OpenCode binaries. If behavior differs between your terminal and Hermes, check:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

If needed, pin an explicit binary path:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## One-Shot Tasks

Use `opencode run` for bounded, non-interactive tasks:

```
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files with `-f`:

```
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
```

Show model thinking with `--thinking`:

```
terminal(command="opencode run 'Debug why tests fail in CI' --thinking", workdir="~/project")
```

Force a specific model:

```
terminal(command="opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4", workdir="~/project")
```

## Interactive Sessions (Background)

For iterative work requiring multiple exchanges, start the TUI in background:

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**Important:** Do NOT use `/exit` — it is not a valid OpenCode command and will open an agent selector dialog instead. Use Ctrl+C (`\x03`) or `process(action="kill")` to exit.

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

### Resuming Sessions

After exiting, OpenCode prints a session ID. Resume with:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Common Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue the last OpenCode session |
| `--session <id>` / `-s` | Continue a specific session |
| `--agent <name>` | Choose OpenCode agent (build or plan) |
| `--model provider/model` | Force specific model |
| `--format json` | Machine-readable output/events |
| `--file <path>` / `-f` | Attach file(s) to the message |
| `--thinking` | Show model thinking blocks |
| `--variant <level>` | Reasoning effort (high, max, minimal) |
| `--title <name>` | Name the session |
| `--attach <url>` | Connect to a running opencode server |

## Procedure

1. Verify tool readiness:
   - `terminal(command="opencode --version")`
   - `terminal(command="opencode auth list")`
2. For bounded tasks, use `opencode run '...'` (no pty needed).
3. For iterative tasks, start `opencode` with `background=true, pty=true`.
4. Monitor long tasks with `process(action="poll"|"log")`.
5. If OpenCode asks for input, respond via `process(action="submit", ...)`.
6. Exit with `process(action="write", data="\x03")` or `process(action="kill")`.
7. Summarize file changes, test results, and next steps back to user.

## PR Review Workflow

OpenCode has a built-in PR command:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or review in a temporary clone for isolation:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode run 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Parallel Work Pattern

Use separate workdirs/worktrees to avoid collisions:

```
terminal(command="opencode run 'Fix issue #101 and commit'", workdir="~/.hermes/cache/scratch/issue-101", background=true, pty=true)
terminal(command="opencode run 'Add parser regression tests and commit'", workdir="~/.hermes/cache/scratch/issue-102", background=true, pty=true)
process(action="list")
```

## Session & Cost Management

List past sessions:

```
terminal(command="opencode session list")
```

Check token usage and costs:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## Pitfalls

- Interactive `opencode` (TUI) sessions require `pty=true`. The `opencode run` command does NOT need pty.
- Installed but "not found": the binary lives in `~/.opencode/bin` and PATH was written to `~/.zshrc` only — login shells need the same export in `~/.zprofile`. Report the absolute-path check as proof before believing the install failed.
- Belt-and-braces on macOS: `ln -sf ~/.opencode/bin/opencode ~/.local/bin/opencode` — `~/.local/bin` is already on the default PATH, so the command resolves even in shells that never read either rc file.
- A terminal opened BEFORE the install keeps the old PATH. `exec zsh -l` reloads it in the same window (no need to close the tab); a new window or `source ~/.zprofile` also works.
- `/exit` is NOT a valid command — it opens an agent selector. Use Ctrl+C to exit the TUI.
- PATH mismatch can select the wrong OpenCode binary/model config.
- If OpenCode appears stuck, inspect logs before killing:
  - `process(action="log", session_id="<id>")`
- Avoid sharing one working directory across parallel OpenCode sessions.
- Enter may need to be pressed twice to submit in the TUI (once to finalize text, once to send).

## Verification

Smoke test:

```
terminal(command="opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Success criteria:
- Output includes `OPENCODE_SMOKE_OK`
- Command exits without provider/model errors
- For code tasks: expected files changed and tests pass

## Rules

1. Prefer `opencode run` for one-shot automation — it's simpler and doesn't need pty.
2. Use interactive background mode only when iteration is needed.
3. Always scope OpenCode sessions to a single repo/workdir.
4. For long tasks, provide progress updates from `process` logs.
5. Report concrete outcomes (files changed, tests, remaining risks).
6. Exit interactive sessions with Ctrl+C or kill, never `/exit`.
