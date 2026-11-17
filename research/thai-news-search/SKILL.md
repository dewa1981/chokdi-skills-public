---
name: thai-news-search
description: Use when searching Thai news/headlines without a browser.
---

# Thai News Search (no browser needed)

Reliable way to pull current Thai-language news headlines when the browser is
unavailable or you just need a fast headline sweep. This is the go-to for
Patty's recurring "เช็คข่าวให้ที" (check the news for me), morning briefings,
and fact-check requests.

## Why not the browser / curl
- `browser_exec` may be down (chrome not running). Don't block on it — this RSS
  path works from plain `terminal`.
- `curl` with raw Thai characters in the URL returns **HTTP 400** (malformed
  request). The query MUST be percent-encoded.

## Core technique — Google News RSS via Python urllib

Use the bundled script for one-shot queries:

```
python3 scripts/thai_news.py "รอยเลื่อน แผ่นดินไหว ไทย" 15
```

Or inline (no script needed):

```python
import urllib.parse, urllib.request, re
q = "รอยเลื่อน แผ่นดินไหว ไทย"
url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
       + "&hl=th&gl=TH&ceid=TH:th")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
items = re.findall(r"<item>(.*?)</item>", data, re.DOTALL)
for it in items:
    t = re.search(r"<title>(.*?)</title>", it, re.DOTALL)
    s = re.search(r"<source[^>]*>(.*?)</source>", it, re.DOTALL)
    d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.DOTALL)
    print("-", t.group(1) if t else "?")
    print("  ", s.group(1) if s else "?", "|", d.group(1) if d else "?")
```

Add `&tbs=qdr:d` to a **Google web search** URL (not the RSS feed) to filter to
the last 24h; the RSS feed returns newest-first by default.

## Pitfalls
- **Thai chars in `curl` → 400.** Always `urllib.parse.quote()` the query.
  Non-ASCII in a raw URL is the #1 cause of the "malformed request" error.
- **Google News article redirects are JS-gated.** The `<link>`/description URLs
  like `https://news.google.com/rss/articles/CBMi...` just return the text
  "Google News" when fetched (even with a cookie jar + redirect handler). RSS is
  good for **headline + source + timestamp + one-line description** — enough for
  a briefing. Don't burn time chasing full article text through those redirects.
- **Direct news-site fetch is inconsistent.** Observed: bangkokbiznews search
  page loads (~80KB) but doesn't expose clean article URLs in `href`;
  springnews returns 403 to urllib; TNN returns 403. When you need the *body* of
  one story, try the site's own search or a known article URL — but treat RSS
  headlines as the reliable default, and say so honestly if you couldn't get the
  full text.
- **Cross-check with multiple sources.** Headlines from 3–5 outlets on the same
  story (e.g. ปภ./ThaiPBS/springnews/bangkokbiznews/TNN) give you confidence in
  the facts without needing full articles.

## Fact-check workflow (Patty forwards an article/viral post and asks "จริงมั้ย / เป็นไปได้มั้ย")
The job is verifying, not summarising. Order that works:

1. **Get the PRIMARY reports, not the forwarded post.** The forwarded text is usually a secondary
   rewrite; fetch the same event from the outlets themselves (Prachatai, Post Today, Bangkok Biz,
   Nation, Thai PBS) and cross-check at least two:
   ```bash
   curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36" \
     --max-time 45 "<url>" -o /tmp/pg.html
   # then strip to text: re.sub(r'(?is)<(script|style|noscript|nav|footer|header).*?</\1>',' ',t)
   #                     re.sub(r'(?s)<[^>]+>',' ',t)  then html.unescape(t)
   ```
2. **Sort every claim into three buckets and label them in the answer:**
   (a) **verified** — the forum/event/expert/source is real, with the outlet named;
   (b) **dramatised** — headline framing the expert never said ("ระเบิดเวลา…จ่อ", "time bomb") versus
   the actual message ("อย่าประมาท เตรียมพร้อม");
   (c) **unverified** — numbers you could not confirm in any primary source. Say so explicitly rather
   than repeating them.
3. **Re-derive every number from a primary source — rewrites drop digits.** A secondary article can
   print `0.2g` where the primary said `0.02` and turn "an order of magnitude lower" into "equal to".
   Any figure that appears only in the forwarded post stays unverified.
4. **Statistical claims are not schedules.** "Return period ~100 years, 96 years elapsed" is a long-run
   average: annual probability stays small and does not grow with elapsed time. Spelling that out is
   what actually calms her.
5. **Answer shape:** 🟢 real & credible → ⚠️ what is dramatised → ✅ what IS true (each with outlet
   named) → ❌ wrong/unverified → 💡 what it means for HER (her 28th-floor condo, her house build,
   her trip) with one concrete action. Never alarmist; verify before reassuring.

## Delivery style for Patty (morning news / fact-check briefings)
- Thai, polite (use ครับ). Moderate emoji, keep scannable with bullets/headers.
- **Earthquake/disaster news → calm first, empathy-first.** Patty lived through
  the 2025 M7.7 quake with her baby; quake headlines spike her anxiety. Lead by
  distinguishing "เฝ้าระวัง/เตรียมพร้อม" (monitoring) from "ภัยฉุกเฉิน" (active
  threat), and end with a reassurance + practical next step. Never alarmist.
- She values honest, sourced, direct truth over sugarcoating — cite the outlet
  names and dates so she can verify.
