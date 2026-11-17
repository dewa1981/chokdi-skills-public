# Project / plot geo-risk check — working recipes

Goal: answer "โครงการนี้/ที่ดินนี้ปลอดภัยไหม" with measured numbers, and compare candidate sites
fairly. All sources below are key-free. Run them from `terminal` / `execute_code`.

## 1. Coordinates
Property-portal and developer pages embed the map centre in the HTML:

```python
import re
c = re.findall(r'(?:lat|lng|latitude|longitude)["\']?\s*[:=]\s*["\']?(-?\d{1,2}\.\d{3,})', html)
```

Fallback — geocode the name / the ตำบล through Nominatim (Thailand only, be polite with a UA):

```python
import json, urllib.parse, urllib.request
UA = {"User-Agent": "home-risk-check/1.0"}
q = "เทศบาลนครเชียงราย"
u = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
    {"q": q, "format": "json", "limit": 4, "countrycodes": "th"})
d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
```

Project names in Thai usually return nothing — go to the developer's own project page first
(`.../single-home/<project>/`), the address line there gives the ตำบล/หมู่, the embedded coords
give the exact centre. Portals (nayoo.co, home.co.th, thinkofliving, homenayoo) repeat the coords.

## 2. Elevation (SRTM 30 m, free)

```python
def elev(lat, lon):
    u = f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}"
    return json.loads(urllib.request.urlopen(u, timeout=45).read())["results"][0]["elevation"]
```

±5 m noise. Use for ranking sites, never for an absolute "above flood level" claim.

### 2b. Gradient + drainage direction (the reading that actually answers "จะท่วมไหม")

One reading ranks sites; a **grid** shows which way the ground falls and therefore where the
water leaves. Sample the point, then 8 compass points at ~300 m and ~1 km, then transects
(N–S and E–W) every 500 m out to 2 km — 1 km ≈ 0.009° latitude ≈ 0.0095° longitude in
northern Thailand. Sleep ~1.1 s between calls; the free tier starts erroring when hammered.

```python
import json, time, urllib.request
def elev(lat, lon, ds="srtm90m"):        # srtm30m works too; 90m is enough for a 300 m grid
    u = f"https://api.opentopodata.org/v1/{ds}?locations={lat},{lon}"
    return json.loads(urllib.request.urlopen(u, timeout=25).read())["results"][0]["elevation"]

base = (19.878330, 99.856143)
for name, dx, dy in [("N",0,0.009),("S",0,-0.009),("E",0.0095,0),("W",-0.0095,0),
                     ("NE",0.0067,0.0067),("NW",-0.0067,0.0067),
                     ("SE",0.0067,-0.0067),("SW",-0.0067,-0.0067)]:
    time.sleep(1.1)
    print(name, elev(base[0]+dy, base[1]+dx))
```

How to read the result (this is the part that must not be skipped):

- **Total relief inside ~2 km tells you the hazard TYPE.** A site whose 2 km neighbourhood varies
  by only 5–10 m is a flat basin: the risk is **standing water / poor drainage**, not a flash
  flood or a slope failure. Say that in those words instead of a generic "เสี่ยvน้ำท่วม".
- **The compass point that reads lowest is where water wants to go.** Quote it (e.g. "N 389 m vs
  S 398 m → runoff drains north") and check whether a creek, canal or the project outfall sits on
  that side, using §3.
- **A site sitting 3–4 m above its lowest 1 km neighbour is not safe, just not the first to flood** —
  frame it as "พอรับน้ำฝนปกติ แต่ไม่กันน้ำท่วมใหญ่".
- **Compare against a plot the user already trusts** as the control (her own land), one number per
  site: it turns an abstract m-slope into "สูงกว่า/ต่ำกว่าเท่าไร".
- **Build-stage risk the map cannot show:** while neighbouring plots are still bare and being
  filled, each newly raised pad sends its runoff to the finished units. Always pair the gradient
  reading with "ขอระดับถมดินเป็นตัวเลข (ซม.) เทียบถนนโครงการ" and "บ่อพัก/ท่อระบายอยู่ตรงไหน".
- Never convert SRTM into "ต่ำกว่าระดับน้ำท่วมปี X กี่ ซม." — that number only exists in the
  developer's engineering drawings, so ask for it in writing.

## 3. Nearest creek / river (Overpass)

```python
q = (f'[out:json][timeout:60];'
     f'(way(around:3000,{lat},{lon})["waterway"];'
     f'way(around:3000,{lat},{lon})["natural"="water"];);out geom 80;')
# POST to https://overpass.kumi.systems/api/interpreter  (fallback: overpass-api.de)
# take min distance per named way -> distance + the way's own elevation for the level gap
```

Rate limits are real: `HTTP 429` and `504` both happen. Alternate the two mirrors and
`sleep 5–10` between sites, otherwise one site comes back empty and you mis-rank it.
A single `waterway=river` query with `radius=7000` is the cheap version when only the main
river matters.

## 4. Site-to-site distance

```python
def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b
    import math
    R = 6371000
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = math.radians(la2-la1), math.radians(lo2-lo1)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
```

Under ~1 km apart = one micro-location. State that the geo-risk is equal and switch the
recommendation to the things that actually differ (price, developer track record, contract
terms, resale).

## 5. News cross-check (per ตำบล)

Fetch the primary flood/quake reporting as text (Google News RSS for the sweep, direct fetch for
the body — see the `thai-news-search` skill):

```bash
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36" \
  --max-time 45 "<url>" -o /tmp/pg.html
# strip: script/style/nav/footer -> tags -> html.unescape ; then search for the ตำบล and the highway name
```

What to extract: which ตำบล/หมู่ flooded and which creek topped out; whether the highway in
front of the project flooded and how deep; the province's damaging quakes and the fault names.

## 6. Answer shape (deliverable)

1. **Clarify the project name first.** Ask/flag when the name does not exist — users conflate
   marketing names (e.g. "อเวนิว 14" vs the real "14 แกรนดิโอ" + "อเวนิว 12"). Listing what the
   developer actually has is itself useful.
2. Table: ระดับดิน (SRTM) | คลอง/ลำน้ำใกล้สุด + ระยะ | ราคา | เจ้า/แบรนด์ | จุดเด่น.
3. Flood section (measured lines first, history second), quake section (faults + the fact the
   differentiator is the build standard, not the plot), then ONE bottom-line recommendation.
4. **5 questions to ask the developer**: ถมดินสูงเท่าไรเทียบถนนสาธารณะ; น้ำท่วมถึงตัวแปลงปีไหน;
   ผลเจาะสำรวจดิน (borehole) + แบบโครงสร้างตาม มยผ.1301/1302; รับประกันโครงสร้างกี่ปี;
   ระบายน้ำออกทางไหนและเคยล้นไหม.
5. Offer the Word/doc version — she prints it to talk to the sales office.
