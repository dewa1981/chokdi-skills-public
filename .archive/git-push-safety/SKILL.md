---
name: git-push-safety
description: "Use when pushing to a shared branch from a stale clone."
platforms: [linux, macos]
---

# Git Push Safety on Shared Branches

Before any `git push` to a shared branch (especially `main` of a repo other
agents or people also write to), prove the push is additive. A local clone that
fell behind still holds old copies of files that upstream moved on from — so a
push (or a forced rebase) silently **reverts their work**.

## The preflight: read the divergence, not just the status

```bash
git fetch origin
git log --oneline origin/main..HEAD     # what I would ADD
git diff --stat origin/main HEAD        # what I would DELETE
```

An append-only change to one file should read `~N insertions, 0 deletions`.
A line like `73 insertions, 146 deletions` on a file you only appended to is the
tell: the local copy is stale and pushing it wipes content. **Stop and switch to
the API flow below.**

## The stale-clone signal during a rebase

`git pull --rebase origin main` stopping with `Could not apply <sha>` plus
`git status` showing `UU <file>` (both modified) is NOT a merge problem to force
through — it is the same stale-clone signal. Recover without losing the commit:

```bash
git rebase --abort             # commit survives; tree returns to pre-rebase
git log --oneline -2           # confirm your commit is still there
grep -c '<your-marker>' <file> # confirm your edit is still in the file
```

Then use the API flow instead of retrying the push.

## The safe write: Contents API, always based on the REMOTE copy

Non-negotiable ordering: **GET the true remote content first, modify that copy,
PUT it back with the remote `sha`.** Never base a PUT on a local file that may be
stale; never PUT without a `sha` for an existing file.

1. GET the file and its `sha`:

```bash
curl -4 -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/OWNER/REPO/contents/PATH" -o /tmp/meta.json
```

`meta.json` carries `sha` (required for the PUT) and base64 `content`. Decode
with a real base64 decoder, not string surgery.

2. Modify that remote copy, anchored on a stable delimiter:

```python
js = open(remote_copy, encoding="utf-8").read()
if SLUG in js:                      # idempotent - re-runs must not double-insert
    raise SystemExit("already present")
idx = js.rfind("];")                # anchor on the LAST closing bracket
assert idx != -1, "anchor not found - file shape changed, inspect manually"
new = js[:idx] + entry + js[idx:]
```

3. **Assert the delta is exactly what you intended** - this catches a clobber
   before it is published:

```python
assert new.count("slug:") == before + 1, "entry count changed by more than one"
assert "<an-entry-that-must-survive>" in new, "existing entry was dropped"
```

4. PUT with the payload in a FILE (never inline):

```bash
curl -4 -s -X PUT \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/OWNER/REPO/contents/PATH" \
  -d @/opt/data/cache/payload.json -o /tmp/put_result.json
```

Payload: `{message, content (base64 -w0), sha, branch}`. Two reasons the file
indirection is mandatory: inline JSON in `curl -d` breaks the shell when content
contains `&` or quotes, and `base64 -w0` output fed inline corrupts JSON with
embedded newlines.

5. Verify the write, then the downstream artifact:

```bash
python3 -c "import json; d=json.load(open('/tmp/put_result.json')); \
  print(d['commit']['sha'] if d.get('commit') else d.get('message'))"
```

`commit.sha` = landed. `message` = failed — read it (`Bad credentials`,
`sha does not match`, `Not Found`). Then fetch the live artifact URL; the commit
existing is not proof the change is serving.

## Pitfalls

- **Never `git push --force` a shared branch.** The API flow exists precisely so
  you never need force and can never discard someone else's commits.
- **Credentials are per-remote, not per-machine.** A remote without an embedded
  token fails with `could not read Username for 'https://github.com'`. Verify
  *which* env file holds a working token before pushing — a stale `GITHUB_TOKEN`
  in a different env file returns `Bad credentials`:
  `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $T" https://api.github.com/user` -> 200.
- **Check for secrets before committing.** `git diff --cached` first; a token
  pasted into source survives in history after the commit.
- **A green CI/CD status is not proof the artifact exists.** When an external
  builder (CF Pages/Netlify/Vercel) reports `build: success` + `deploy: success`
  yet the live URL is wrong, the fault is inside the build output or caching -
  not the deploy. Fetch the immutable per-deployment host
  (`https://<deploy-id>.<project>.pages.dev`) to bypass CDN cache and check what
  that specific build actually produced.
- **Restore and re-verify after an aborted rebase** — `git rebase --abort` returns
  you to pre-rebase state, but confirm with `git log --oneline -2` and a marker
  grep rather than assuming.

## Support files

- `references/deploy-green-but-404.md` — full ordered diagnosis for when CI says
  `build: success` + `deploy: success` but the live page is still wrong
  (file-present check -> stage check -> local build output check -> future-date
  probe via `--buildFuture`, plus the per-deployment cache-bypass URL trick).
