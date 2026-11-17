#!/usr/bin/env python3
"""Probe MCP stdio server pihak-3 TANPA Hermes (handshake JSON-RPC).

Pakai:  python3 scripts/mcp_stdio_probe.py -- /usr/local/bin/zn mcp
Ganti perintah setelah '--' dengan server MCP stdio apa pun.

Keluaran: serverInfo, jumlah tool, daftar nama + deskripsi singkat tiap tool.
Pakai subprocess interaktif, BUKAN pipe sekali-jalan: banyak server menutup stdio saat
stdin EOF dan melapor 'server is closing: EOF', yang tampak seperti gagal padahal bukan.
"""
import json
import subprocess
import sys


def main() -> int:
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if not argv:
        print("usage: mcp_stdio_probe.py -- <command> [args...]", file=sys.stderr)
        return 2

    proc = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, bufsize=1,
    )

    def send(obj: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    def read() -> dict | None:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        return json.loads(line) if line.strip() else None

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "hermes-probe", "version": "1.0"}}})
    init = read() or {}
    print("serverInfo:", json.dumps(init.get("result", {}).get("serverInfo", {})))

    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    listing = read() or {}
    tools = listing.get("result", {}).get("tools", [])
    print("JUMLAH TOOL:", len(tools))
    for tool in tools:
        desc = (tool.get("description") or "").replace("\n", " ")[:70]
        print(f"  - {tool['name']}: {desc}")

    proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
