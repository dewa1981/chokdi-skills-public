#!/usr/bin/env python3
"""Screenshot halaman HTML pada lebar TEPAT (desktop + mobile) via CDP.

Kenapa bukan `chrome --window-size`: headless Chrome meng-clamp lebar window ke ~485-500px,
sehingga `--window-size=390` merender layout 485px lalu memotong PNG di 390px -> semua elemen
kanan tampak "terpotong" dan QC melaporkan overflow palsu. Emulation.setDeviceMetricsOverride
menghilangkan clamp itu, sekaligus memberi captureBeyondViewport untuk halaman penuh.

Pakai:
    python3 fullpage_cdp_shot.py /abs/page.html /abs/outdir ["js-sebelum-shot"]

Contoh js-sebelum-shot (opsional, dijalankan setelah load, sebelum capture):
    "localStorage.setItem('pkl_lang','en');location.reload();"

Butuh: chromium binary (default di bawah) + python `websockets`.
Output: <outdir>/full_desktop.png, <outdir>/full_mobile.png + baris metrik ke stdout.
"""
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

CHROME = os.environ.get("CHROME_BIN") or "/opt/data/tools/chromium-1208/chrome-linux64/chrome"
PORT = int(os.environ.get("CDP_PORT", "9340"))


def find_chrome():
    if os.path.exists(CHROME):
        return CHROME
    for base in (os.path.expanduser("~/.cache/ms-playwright"), "/opt/data/tools"):
        for root, _dirs, files in os.walk(base):
            if "chrome" in files and root.endswith("chrome-linux64"):
                return os.path.join(root, "chrome")
    return CHROME


async def main(html, outdir, pre_js):
    os.makedirs(outdir, exist_ok=True)
    chrome = find_chrome()
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], capture_output=True)
    proc = subprocess.Popen([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                             f"--remote-debugging-port={PORT}", f"--user-data-dir=/tmp/cdp_prof_shot_{PORT}",
                             "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws_url = None
    for _ in range(60):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1) as r:
                ws_url = json.load(r)["webSocketDebuggerUrl"]
            break
        except Exception:
            time.sleep(0.4)
    if not ws_url:
        raise SystemExit("chrome CDP tidak siap")
    import websockets

    async with websockets.connect(ws_url, max_size=200 * 1024 * 1024) as sock:
        mid = 0

        async def send(method, params=None, session=None):
            nonlocal mid
            mid += 1
            msg = {"id": mid, "method": method, "params": params or {}}
            if session:
                msg["sessionId"] = session
            await sock.send(json.dumps(msg))
            while True:
                data = json.loads(await sock.recv())
                if data.get("id") == mid:
                    if "error" in data:
                        raise RuntimeError(f"{method}: {data['error']}")
                    return data.get("result", {})

        target = await send("Target.createTarget", {"url": "about:blank"})
        att = await send("Target.attachToTarget", {"targetId": target["targetId"], "flatten": True})
        s = att["sessionId"]
        await send("Page.enable", session=s)
        url = "file://" + os.path.abspath(html)

        for label, w, h, dsf, mobile in (("desktop", 1440, 900, 1, False), ("mobile", 390, 844, 2, True)):
            await send("Emulation.setDeviceMetricsOverride",
                       {"width": w, "height": h, "deviceScaleFactor": dsf, "mobile": mobile}, session=s)
            await send("Page.navigate", {"url": url}, session=s)
            await asyncio.sleep(2.5)
            if pre_js:
                await send("Runtime.evaluate", {"expression": pre_js}, session=s)
                await asyncio.sleep(2.5)
            ev = await send("Runtime.evaluate", {
                "expression": "JSON.stringify({sw:document.documentElement.scrollWidth,"
                              "cw:document.documentElement.clientWidth,h:document.body.scrollHeight})",
                "returnByValue": True}, session=s)
            dims = json.loads(ev["result"]["value"])
            shot = await send("Page.captureScreenshot", {
                "format": "png", "captureBeyondViewport": True,
                "clip": {"x": 0, "y": 0, "width": dims["cw"], "height": dims["h"], "scale": 1}}, session=s)
            out = os.path.join(outdir, f"full_{label}.png")
            with open(out, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            overflow = bool(dims["sw"] > dims["cw"])
            print(json.dumps({"variant": label, "file": out, "width": dims["cw"],
                              "scrollWidth": dims["sw"], "height": dims["h"],
                              "horizontal_overflow": overflow}))
        await send("Target.closeTarget", {"targetId": target["targetId"]})
    proc.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
