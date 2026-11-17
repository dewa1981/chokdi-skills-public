#!/usr/bin/env python3
"""Fetch current Thai news headlines from Google News RSS (no browser needed).

Usage:
    python3 thai_news.py "รอยเลื่อน แผ่นดินไหว ไทย" [count]
"""
import re
import sys
import urllib.parse
import urllib.request

QUERY = sys.argv[1] if len(sys.argv) > 1 else "ข่าววันนี้"
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 15


def fetch_rss(query: str, count: int = 15):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=th&gl=TH&ceid=TH:th"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    items = re.findall(r"<item>(.*?)</item>", data, re.DOTALL)
    out = []
    for it in items[:count]:
        t = re.search(r"<title>(.*?)</title>", it, re.DOTALL)
        s = re.search(r"<source[^>]*>(.*?)</source>", it, re.DOTALL)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.DOTALL)
        out.append({
            "title": t.group(1) if t else "?",
            "source": s.group(1) if s else "?",
            "date": d.group(1) if d else "?",
        })
    return out


if __name__ == "__main__":
    results = fetch_rss(QUERY, COUNT)
    print(f"QUERY: {QUERY}  ({len(results)} results)\n")
    for r in results:
        print("-", r["title"])
        print("   ", r["source"], "|", r["date"])
