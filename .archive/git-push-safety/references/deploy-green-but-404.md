# Diagnosing a wrong live response when the deploy says success

For static sites built by an external CI (Cloudflare Pages, Netlify, Vercel).
The failure mode this file exists for: **the pipeline is green, the file is in
the repo, sibling pages serve fine, and your new page is still wrong.** Do not
diagnose that as "deploy hasn't run yet", "cache", or "file wasn't picked up".

## Order of checks (cheapest discriminator first)

### 1. Confirm the file actually reached the remote repo

An absent file and a present-but-rejected file look identical from a browser.

```bash
curl -4 -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/OWNER/REPO/contents/PATH/TO/FILE" \
  -o /tmp/f.json
python3 -c "import json; d=json.load(open('/tmp/f.json')); \
  print('PRESENT', d['size']) if d.get('sha') else print('ABSENT', d.get('message'))"
```

Present -> the problem is in the BUILD or the request, not the upload.

### 2. Confirm the deploy for THIS commit succeeded

Grab the deployment list and read `stages[]`, not just the headline status.

```bash
curl -4 -s -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT/pages/projects/$PROJECT/deployments?per_page=3"
```

Every stage `success` (queued/initialize/clone_repo/build/deploy) for your commit
-> the pipeline is exonerated. Look at the build output instead.

### 3. Reproduce the build LOCALLY and look for the output path

This is the step that actually finds the fault. All other checks can pass while
the generator quietly withholds the page.

```bash
PATH=/opt/data/.local/bin:$PATH hugo --destination /tmp/out
ls -d /tmp/out/posts/<slug>/          # does the page exist in the output?
find /tmp/out/posts -name index.html | wc -l   # sanity: page count unchanged?
```

A build that completes with a page count but **omits your page** is the signal.

### 4. Use the future-date probe to confirm a date withholding

Hugo (and similar generators) withhold pages whose frontmatter `date` is later
than build time, defaulting to `buildFuture=false`. The disambiguating test:

```bash
hugo --destination /tmp/out-future --buildFuture
ls -d /tmp/out-future/posts/<slug>/   # MUNCUL here = date was the cause
```

Appears with `--buildFuture` and nowhere else -> conclusively a future date.

```bash
TZ=Asia/Jakarta date                  # get the REAL current time
```

Set `date:` at or before that value. Never invent a time: writing `19:00` when
the build runs at `18:21` WIB 404s the page for the next ~40 minutes, and
looks exactly like an infrastructure failure.

## Why the deploy URL is still worth fetching

Each deployment has an immutable host (`https://<deploy-id>.<project>.pages.dev`).
Fetching that instead of the production alias bypasses CDN/browser cache and
answers "what did THIS build produce?" — which is what distinguishes a caching
problem from a build problem. If the deployment URL also fails, the build is at
fault and caching is irrelevant.

## Anti-patterns

- Re-pushing the same content hoping the deploy "catches up" — the pipeline was
  never the problem, and each push adds noise to the history.
- Editing the production branch, custom domain, or DNS while diagnosing — none of
  those can withhold a single page from an otherwise-successful build.
- Declaring success from the commit existing or CI being green. The deliverable is
  the served page; verify the served page.
