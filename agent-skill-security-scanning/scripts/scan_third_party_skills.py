#!/usr/bin/env python3
"""Triase keamanan untuk satu/lebih repo skill pihak ketiga.

Pakai:
    python3 scan_third_party_skills.py /tmp/slopaudit

Memindai semua file teks di tiap subfolder repo dan menandai:
  - instruction override (prompt injection)
  - eksekusi shell dari jaringan (curl|sh), base64|sh, nc -e
  - exfiltrasi env/token, chmod 777, akses authorized_keys
  - HOOK otomatis di package.json (postinstall/preinstall/prepare/postpack)

Interpretasi: hit di tests/ evals/ fixtures/ examples/ biasanya sampel uji (benign).
Hit di SKILL.md / references/ / scripts/ / agents/ atau hook otomatis = periksa manual.
"""
import json
import os
import re
import sys

PATTERNS = {
    "injection": r"(ignore (all )?previous instructions|disregard .{0,25}(previous|above)|you are now|new system prompt|override .{0,20}safety)",
    "pipe_shell": r"curl[^\n|]{0,120}\|\s*(ba|z)?sh",
    "rm_root": r"rm\s+-rf\s+/(\s|$)",
    "exfil": r"(exfiltrat|send .{0,40}(api[_-]?key|token|secret)|post .{0,30}to https?://(?!github))",
    "b64_exec": r"(base64 -d|atob\()[^\n]{0,80}\|\s*(ba)?sh",
    "netcat": r"\bnc\s+-[a-z]*e\b|\bncat\b",
    "chmod777": r"chmod\s+777",
    "ssh_edit": r"(authorized_keys|\.ssh/id_)",
    "env_dump": r"(env\s*\|\s*curl|printenv\s*\|\s*curl)",
}
HOOKS = ("postinstall", "preinstall", "prepare", "postpack")
BENIGN_DIRS = {"tests", "test", "evals", "eval", "fixtures", "examples", "__tests__"}
TEXT_EXT = {".md", ".txt", ".sh", ".bash", ".py", ".js", ".ts", ".mjs", ".cjs",
            ".json", ".yaml", ".yml", ".toml", ".mdc", ".rule"}
SKIP_DIRS = {".git", "node_modules", "dist", "target", "vendor", "build"}


def scan_file(path):
    hits = []
    try:
        txt = open(path, "r", errors="replace").read()
    except OSError:
        return hits
    for name, pat in PATTERNS.items():
        m = re.search(pat, txt, re.I)
        if m:
            hits.append((name, m.group(0)[:90]))
    return hits


def main(root):
    for repo in sorted(os.listdir(root)):
        d = os.path.join(root, repo)
        if not os.path.isdir(d):
            continue
        print("=" * 72)
        print("REPO:", repo)
        scanned = 0
        real, benign, hooks = [], [], []
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
            rel_dir = os.path.relpath(dirpath, d).lower()
            in_benign = any(part in BENIGN_DIRS for part in rel_dir.split(os.sep))
            for f in filenames:
                p = os.path.join(dirpath, f)
                if os.path.splitext(f)[1].lower() in TEXT_EXT:
                    scanned += 1
                    h = scan_file(p)
                    if h:
                        (benign if in_benign else real).append((os.path.relpath(p, d), h))
                if f == "package.json":
                    try:
                        sc = json.load(open(p)).get("scripts") or {}
                        hooks += [(os.path.relpath(p, d), k, sc[k][:80]) for k in HOOKS if k in sc]
                    except Exception:
                        pass
        print(f"  file teks dipindai: {scanned}")
        print(f"  HOOK otomatis: {hooks or 'tidak ada'}")
        print(f"  temuan di file NON-uji: {len(real)}")
        for fp, h in real[:10]:
            print("   ! ", fp, "->", h)
        if benign:
            print(f"  (diabaikan) temuan di folder uji/sampel: {len(benign)} file")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
