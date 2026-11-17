---
name: hermes-venv-repair
description: "Use when a Hermes tool fails on missing python packages."
version: 1.0.0
author: Patty (pattysnow448)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, venv, packages, certifi, interpreter, troubleshooting]
    related_skills: [hermes-install-upgrade]
---

# Repairing the Hermes runtime venv

## When to Use

- A built-in tool fails on its own dependencies rather than on the user's data:
  `web_search` / `web_extract` returning `Could not find a suitable TLS CA certificate bundle,
  invalid path: .../site-packages/certifi/cacert.pem`; a generator script returning
  `ModuleNotFoundError: No module named 'openpyxl'` / `'docx'` / `'fitz'`.
- You need a python for a document/spreadsheet script and the shell's `python3` is the wrong one.
- Right after a Hermes upgrade or install-method cutover, when working tools start complaining
  about packages.

This is environment state, not a broken tool. Fix it and carry on; never report "web search does
not work" or "this tool is broken" to the user or into a skill.

## Diagnosis in two calls

```bash
python3 -c "import sys; print(sys.executable)"          # what the shell actually resolves
find / -maxdepth 7 -type d \( -name openpyxl -o -name docx -o -name certifi \) \
  -path '*site-packages*' 2>/dev/null | head -20
```

The second call is the important one: it lists every venv on the box that has the library. Invoke
that venv's python by absolute path; do not `pip install` into whichever venv the PATH points at
(it is often a profile venv with no `pip` at all).

## Pitfall: the gateway does NOT run on the venv

`--version`, `py_compile`, and `import x` under `<install>/.venv/bin/python` all passing proves
nothing about the running gateway. This host's gateway is launched through a **standalone
interpreter** (`/opt/data/tools/python-3.X.Y.../bin/python3 -I ...`) and never touches `.venv`, so a
package installed in `.venv` is invisible to every tool at runtime — the tool fails with
`ModuleNotFoundError` / "provider selected but package not installed" while `pip list` cheerfully
shows the package present.

Find the interpreter the gateway actually uses before installing anything:

```bash
ps -eo pid,cmd | grep "gateway run" | grep -v grep | cut -c1-120   # the python binary in front
<PARSED_PYTHON> -c "import <pkg>; print(<pkg>.__version__)"          # test with THAT binary
```

- Import fails there while `<install>/.venv` has it → interpreter mismatch, not a missing package.
- Fix by installing into the **gateway's** interpreter (`<PARSED_PYTHON> -m pip install <pkg>`), which
  needs no service edit and no restart of the venv; switching the service to `.venv` is the heavier,
  riskier option and changes every other dependency at once.
- Any package fix needs a gateway restart to take effect in-process; say so instead of implying the
  fix is already live.

## Fix: copy from the disabled install

An upgrade keeps the previous install beside the new one as `<install_dir>.disabled/`, and a new
install directory ships a **fresh venv** — packages pip-installed ad hoc into the old one are gone.
Copy them across rather than reinstalling:

```bash
NEW=$(ls -d /opt/data/installs/*/environments/*/venv | tail -1)   # active install's venv
OLD=$(ls -d /opt/data/installs/*.disabled/environments/*/venv | tail -1)
cp -a "$OLD"/lib/python3.*/site-packages/certifi      "$NEW"/lib/python3.*/site-packages/
cp -a "$OLD"/lib/python3.*/site-packages/openpyxl     "$NEW"/lib/python3.*/site-packages/ 2>/dev/null
"$NEW"/bin/python -m pip install --quiet python-docx pymupdf 2>&1 | tail -3   # if pip exists there
```

On this host `/opt/hermes-v0204/.venv/bin/python` is the interpreter carrying `openpyxl` +
`python-docx`, and the one to use for `python3 script.py` runs of document generators; pymupdf
installs into it with `-m pip install pymupdf`.

## Verify with the real path, then say it is fixed

`import x` succeeding under some interpreter proves nothing about the tool that failed. Confirm with
the actual entry point — one real `web_search` query, or one real .docx/.xlsx generated and re-opened
— before telling the user it works.

## Pitfalls

- The error quotes a `certifi/cacert.pem` path as if the file were merely misplaced; the directory
often does not exist at all. Do not settle for `export SSL_CERT_FILE=/etc/ssl/certs/...` — restore
the package, because other libraries in the same venv look for it too.
- Do not install into a profile's venv just because `python3` resolves there; it may lack `pip`, and
  packages there are not what the Hermes tools import.
- Re-check after every upgrade: these symptoms return until the packages are restored, and they show
  up first in tools that look unrelated to the one that broke.
