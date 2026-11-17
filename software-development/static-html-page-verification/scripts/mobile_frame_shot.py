#!/usr/bin/env python3
"""True-width mobile screenshot of a local HTML page + numeric overflow check.

Why this exists: headless Chrome clamps its window to ~500px wide, so
`--window-size=390,...` lays the page out at 500px and crops the PNG at 390px,
which fakes 'content cut off on the right'. Rendering the page inside a 390px
iframe gives a real 390px layout viewport.

Usage:
  python3 mobile_frame_shot.py <page.html> [--widths 320,360,390]
                                  [--outdir /tmp/shots] [--chrome PATH]

Outputs: <outdir>/<name>_<w>_full.png and a JSON line per width with
scrollWidth/clientWidth/height (overflow is real only when sw > cw).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

CANDIDATES = [
    os.path.expanduser("~/.cache/ms-playwright"),
    "/opt/data/tools",
    "/root/.agent-browser/browsers",
]


def find_chrome(explicit: str | None) -> str:
    if explicit:
        return explicit
    for root in CANDIDATES:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if "chrome" in files and dirpath.endswith(("chrome-linux64", "chrome-linux")):
                return os.path.join(dirpath, "chrome")
    raise SystemExit("chrome binary not found; pass --chrome")


def frame_html(page: str, width: int) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{{margin:0;background:#000}}iframe{{border:0;display:block;width:{width}px;height:20000px}}</style>
</head><body><iframe id="f" src="{page}" scrolling="no"></iframe>
<script>
window.onload=function(){{setTimeout(function(){{
  var doc=document.getElementById('f').contentDocument;
  var d=doc.documentElement, b=doc.body;
  document.title='M:'+d.scrollWidth+','+d.clientWidth+','+(b.scrollHeight||d.scrollHeight);
}},1500);}};
</script></body></html>"""


def run(chrome: str, args: list[str]) -> str:
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    return (p.stdout or "") + (p.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--widths", default="390")
    ap.add_argument("--outdir", default="/tmp/shots")
    ap.add_argument("--chrome")
    a = ap.parse_args()

    page = os.path.abspath(a.page)
    if not os.path.exists(page):
        raise SystemExit(f"not found: {page}")
    chrome = find_chrome(a.chrome)
    os.makedirs(a.outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(page))[0]
    results = []

    for w in [int(x) for x in a.widths.split(",") if x.strip()]:
        tmp = tempfile.mkdtemp()
        frame = os.path.join(tmp, "frame.html")
        with open(frame, "w") as fh:
            fh.write(frame_html(page, w))

        dom = run(chrome, [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                           "--allow-file-access-from-files", f"--window-size={max(500, w)},1000",
                           "--virtual-time-budget=5000", "--dump-dom", f"file://{frame}"])
        m = re.search(r"M:(\d+),(\d+),(\d+)", dom)
        if not m:
            print(f"[{w}px] could not measure (DOM dump has no marker)")
            continue
        sw, cw, height = (int(x) for x in m.groups())
        shot = os.path.join(a.outdir, f"{name}_{w}_full.png")
        run(chrome, [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                     "--allow-file-access-from-files", "--hide-scrollbars",
                     f"--window-size={max(500, w)},{height + 60}",
                     "--virtual-time-budget=8000", f"--screenshot={shot}", f"file://{frame}"])

        try:
            from PIL import Image
            im = Image.open(shot)
            im.crop((0, 0, w, min(height, im.size[1]))).save(shot)
            size = (w, min(height, im.size[1]))
        except Exception as exc:  # PIL optional
            size = ("?") , str(exc)

        results.append({"width": w, "scrollWidth": sw, "clientWidth": cw,
                        "overflow": sw > cw, "height": height, "png": shot})
        flag = "OVERFLOW" if sw > cw else "ok"
        print(json.dumps({"w": w, "sw": sw, "cw": cw, "h": height,
                          "verdict": flag, "png": shot, "crop": str(size)}))
    return 1 if any(r["overflow"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
