---
name: static-html-page-verification
description: "Use when verifying a static HTML page or its AMP twin."
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [html, landing-page, verification, screenshot, headless-chrome, qa]
    category: software-development
---

# Verifying a static HTML page before sending / deploying

A written HTML file is not a finished deliverable. Raw-text leaks, dead CTAs, and mobile
overflow are invisible in the source and obvious on screen. Run these checks in order —
each is cheap and each has caught a real defect that would otherwise reach the user.

Applies to landing pages, articles, dashboards and panels — anything rendered from an
`.html` file on disk.

## Step 1 — text-first checks in Python (no browser needed)

Run these before spending time on screenshots; they are deterministic and instant.

```python
import re
h = open(path).read()

# 1a. Unclosed / mismatched structural tags
for t in ['html','head','body','style','header','footer','section','div','details','table']:
    o = len(re.findall(r'<'+t+r'[\s>]', h)); c = len(re.findall(r'</'+t+r'>', h))
    if o != c: print('TAG MISMATCH', t, o, c)

# 1b. Anchor targets — every href="#X" needs a matching id="X"
anchors = set(re.findall(r'href="#([a-z0-9-]+)"', h))
ids     = set(re.findall(r'id="([a-z0-9-]+)"', h))
print('anchors without target:', anchors - ids)      # MUST be empty

# 1c. Raw-markup leak (typo that renders as literal text, not as an error)
for pat in [r'\.badge>', r'DIV CLASS', r'</iv>', r'margin0', r'<class=', r'--ext2', r'repat']:
    if re.search(pat, h): print('SUSPECT LITERAL:', pat)
```

Why 1c matters: a dropped `<` or a misspelled tag name raises nothing — the browser prints
the markup as body text. It is invisible in the editor and glaring on the page.

### Pitfall — angka yang tampil `****` di output tool BUKAN berarti file rusak

`read_file`, `grep`, dan `curl` menyamarkan nomor telepon/rahasia di output (mis. `+855****6547`).
Jangan simpulkan JSON-LD / nomor kontak rusak dari tampilan itu — cek dengan assert boolean yang
tidak ikut disamarkan:

```bash
python3 -c "import re;h=open('index.html').read();print('tel_ok', bool(re.search(r'\"telephone\": *\"\+855\d{8,9}\"',h)))"
```

Aturan umum: kalau temuan bergantung pada karakter yang MUNGKIN disamarkan (digit, token), buktikan
dengan boolean/hash/length, bukan dengan mengutip tampilan.

## Step 2 — link inventory by kind

Classify every link and assert each class points where it should:

```python
aff = h.count('tomat.jagungbaru.com/banner/')            # CTA / register links
wa  = len(re.findall(r'wa\.me|whatsapp', h, re.I))       # 0 unless the user asked for it
print('affiliate links:', aff, '| WA refs:', wa)
```

**A register button pointing at `href="#daftar"` with no `id="daftar"` section is a dead
CTA, not a harmless placeholder.** It scrolls nowhere and registers nobody. Point every
DAFTAR / LOGIN / CHAT button at the real destination URL (`target="_blank" rel="noopener"`);
reserve bare `#anchors` for in-page navigation that genuinely has a section behind it.

## Step 3 — screenshot with the cached chromium binary (no python playwright needed)

The Playwright **browser cache** is often present even when the python `playwright` module
is not importable. Do not conclude screenshots are unavailable — call the binary directly:

```bash
CHROME=$(ls ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome | head -1)

# desktop
$CHROME --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1280,2400 --screenshot=/tmp/page_desktop.png \
  --virtual-time-budget=3000 "file:///abs/path/page.html"
```

- The headless binary **can** open `file://` — it is not subject to the private/internal-address
  block that some in-agent browser tools apply.
- `dbus/UPower ... ServiceUnknown` on stderr is **noise**. Confirm success with `ls -lh`:
  a real render is hundreds of KB; a 0-byte file means it genuinely failed.
- `--window-size` with a tall height approximates a full-page capture;
  `--virtual-time-budget=3000` lets CSS/fonts settle before the shot.
- Always produce **both** widths. Desktop-only review misses exactly the defects that make a
  page unusable on a phone.

### Pitfall — headless Chrome refuses a viewport narrower than ~500px

`--window-size=390,2000` does **not** give a 390px layout in most Linux headless builds: the
window is clamped to a ~500px minimum, the page lays out at 500px, and the PNG is cut at 390px.
Everything on the right then *looks* truncated and you will report fake mobile overflow.
Verify the trap once with a blank page before trusting a narrow shot:

```bash
printf '<html><body><script>onload=()=>{document.title="W="+document.documentElement.clientWidth}</script></body></html>' > /tmp/blank.html
$CHROME --headless=new --no-sandbox --window-size=390,900 --virtual-time-budget=1500 \
  --dump-dom file:///tmp/blank.html | grep -o 'W=[0-9]*'   # 500 => clamped
```

**Correct mobile capture = iframe of the real width inside a wide window**, then crop:

```bash
# frame.html: <iframe src="./index.html" width=390 height=8000 scrolling=no>
$CHROME --headless=new --no-sandbox --allow-file-access-from-files --hide-scrollbars \
  --window-size=500,8100 --virtual-time-budget=8000 \
  --screenshot=/tmp/raw.png file:///abs/path/frame.html
python3 -c "from PIL import Image; im=Image.open('/tmp/raw.png'); im.crop((0,0,390,im.size[1])).save('/tmp/mobile.png')"
```

Read the page height from inside the iframe (`contentDocument.body.scrollHeight`), not from
`documentElement.scrollHeight` — the latter is clamped to the iframe viewport and will silently
return the iframe height whenever the page is shorter.
`scripts/mobile_frame_shot.py` does the whole thing (probe + shot + crop).

### Jalur lebih bersih: override metrik lewat CDP (tanpa iframe, tanpa crop)

Kalau python `websockets` tersedia, jalankan chromium dengan `--remote-debugging-port` lalu set viewport
di level protokol — tidak ada clamp, tidak perlu iframe:

```python
await send("Emulation.setDeviceMetricsOverride",
           {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True}, session=s)
await send("Page.navigate", {"url": "file:///abs/page.html"}, session=s)
# ukur di sesi yang sama:
#   document.documentElement.scrollWidth / clientWidth / document.body.scrollHeight
await send("Page.captureScreenshot",
           {"format": "png", "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": cw, "height": scrollHeight, "scale": 1}}, session=s)
```

Keunggulannya: lebar TEPAT 390 (bukan 485/500 hasil clamp), `scrollWidth == clientWidth` terbaca di
pass yang sama, dan satu skrip bisa menghasilkan desktop + mobile halaman-penuh. `scripts/fullpage_cdp_shot.py`
sudah membungkus ini (argumen: path html + folder output; cetak lebar/tinggi/scrollWidth tiap varian).

**Artefak elemen `position:fixed` di screenshot halaman-penuh:** floating CTA / sticky bar menempel ke
dasar VIEWPORT, jadi pada window raksasa (mis. `--window-size=1440,18000`) ia muncul di baris paling bawah
gambar. Dua efek samping yang menipu: (a) trim "baris terakhir yang bukan background" tidak pernah
berhenti dan menyimpulkan halaman setinggi window; (b) `vision_analyze` melaporkan "tombol menutupi
stats/FAQ" padahal di perangkat nyata tombol itu melayang di bawah viewport. Untuk menilai overlap,
ambil screenshot **viewport** (tanpa `captureBeyondViewport`) di beberapa posisi scroll; untuk mengukur
tinggi halaman pakai `document.body.scrollHeight`, bukan scan piksel.

### Ukur clearance sticky/fixed bar secara numerik (jangan dinilai dari PNG)

Screenshot tidak bisa membuktikan footer tertutup atau tidak: pada window tinggi, bar menempel di dasar
viewport gambar sehingga crop paling bawah selalu menampilkan bar, bukan isi halaman. Ukur rect-nya.
Tanpa driver browser: tempel satu `<script>` pengukur ke **salinan** halaman (file asli jangan disentuh),
lalu baca hasilnya dari atribut DOM lewat `--dump-dom`.

```html
<script>
addEventListener('load',function(){setTimeout(function(){
  window.scrollTo(0, document.documentElement.scrollHeight);
  var q=function(s){return document.querySelector(s)},g=function(e){return e?e.getBoundingClientRect():null};
  var st=q('.sticky'),ft=q('.footer'),cr=q('.footer .copyright'),cs=st?getComputedStyle(st):null;
  document.body.setAttribute('data-measure', JSON.stringify({
    vw:innerWidth, vh:innerHeight, docH:document.documentElement.scrollHeight,
    stickyDisplay: cs?cs.display:'MISSING',                 // 'none' = bar memang dimatikan di lebar ini
    stickyTop: g(st)?Math.round(g(st).top):null,
    copyrightBottom: g(cr)?Math.round(g(cr).bottom):null,
    hOverflow: document.documentElement.scrollWidth>innerWidth
  }));
},400)});
</script>
```

```bash
google-chrome --headless=new --no-sandbox --window-size=360,800 --virtual-time-budget=3000 \
  --dump-dom file:///abs/measure.html | grep -o 'data-measure="[^"]*"'
```

Cara baca: pada scroll paling bawah, elemen terakhir footer harus berada **di atas** bar
(`copyrightBottom < stickyTop`); kalau tidak, `padding-bottom` halaman kurang. Jalankan juga di lebar desktop
untuk memastikan bar memang disembunyikan (`stickyDisplay:"none"`), bukan cuma "tidak terlihat di screenshot".
**Catat `vw` yang dilaporkan**: window 360 di Linux headless sering clamp ke ~500, jadi jangan mengklaim
"mobile 360 lolos" dari pass yang lebar sebenarnya 500 — pakai iframe atau CDP override kalau butuh 360 pasti.

### Step 3b — assert overflow numerically, not by eye

Before blaming the layout, measure it at the target widths. Inside the iframe:

```javascript
var d = frame.contentDocument.documentElement;
// d.scrollWidth === d.clientWidth  => no horizontal overflow at this width
```

Run at **320, 360 and 390** — 320 catches grids that only just fit 390. Only when
`scrollWidth > clientWidth` is it a real defect; a cropped screenshot is not evidence.

## Step 3c — uji perilaku JS dengan jsdom (bukan cuma mata)

Halaman berisi kalkulator / form / lightbox / toggle bahasa-tema bisa "terlihat benar" tapi tidak berfungsi.
Uji tanpa browser: `npm i jsdom` di folder scratch, lalu

```js
const dom = new JSDOM(html, {
  runScripts: "dangerously",
  url: "https://contoh.test/",                      // WAJIB http(s)
  beforeParse(w){ w.open = (u) => opened.push(u); }  // tangkap URL wa.me / redirect
});
```

- `url: "file://..."` membuat `localStorage` melempar SecurityError (kode yang sudah try/catch tetap lolos,
  tapi persistensi tidak teruji) — pakai origin http(s) fiktif.
- Set input dengan `el.value = x; el.dispatchEvent(new Event("input",{bubbles:true}))`; assignment `.value`
  saja tidak memicu handler.
- Assert **angka/isi konkret** (mis. ansuran `RM 3,563`, gross yield `4.8%`, URL `wa.me/...` hasil decode), bukan
  "elemen ada". Satu file test per halaman, exit code non-zero kalau ada yang gagal.
- Untuk halaman dwibahasa: ganti bahasa lalu ulangi assert nilai kalkulator + prefill WhatsApp + caption.

**Kalau `vision_analyze` melaporkan elemen yang tidak ada di source** (mis. "kotak putih di belakang paragraf"),
jangan buru-buru menulis ulang CSS. Ambil `getComputedStyle(el).backgroundColor/backgroundImage` lewat CDP:
penyebab tersering adalah satu nama class dipakai dua komponen, dan hanya computed style yang menunjukkan
deklarasi mana yang menang.

## Step 4 — review the pixels, not the markup

Load each PNG with `vision_analyze` and ask specifically about: raw markup showing as text,
horizontal overflow, tap targets under ~44px, unreadably small text, stray alignment, and a
sticky bottom bar covering content. Layout problems are a property of the render, not of the
file — this step catches what reading source cannot.

## Step 5 — AMP variant: generate from the full page, never hand-write it

If the page needs an AMP twin, **derive it from the finished full page** so the two can never
diverge — extract the CSS and body, re-wrap, and convert images by regex:

```python
import re
html = open('brand.html').read()
css  = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
body = re.search(r'<body>(.*?)</body>', html, re.S).group(1)
body = re.sub(r'<img([^>]*?)src="([^"]+)"([^>]*?)>',
              r'<amp-img\1src="\2"\3 width="150" height="46" layout="fixed"></amp-img>', body)
# <html amp lang="id"> + <link rel="canonical"> + <style amp-custom>{css}</style>
```

- `layout="fixed"` is safer than `responsive` for a logo (its aspect ratio is already known from
  `width`/`height`), and it is what keeps the validator quiet.
- **Count the `<script>` tags in the output and assert exactly 1** (only `v0.js`). A second one
  means a script leaked out of the body — silent invalid AMP.
- Deploy the pair as **`index.html` + `amp.html`** so `canonical="./index.html"` and
  `<link rel="amphtml" href="./amp.html">` point at each other without hardcoding the deploy URL.
- Validate or do not claim it: `npx -y amphtml-validator page_amp.html` must print PASS.

### Nama file final menentukan canonical

Kalau hasil dikirim sebagai `index.html` + `index_amp.html`, maka `canonical`, `<link rel="amphtml">`, dan
`og:url` harus menunjuk nama itu — bukan nama deskriptif dari generator (`lp_<brand>.html`). Betulkan di
generator (satu sumber) lalu render ulang, dan assert hasilnya: `grep -o 'rel="canonical" href="[^"]*"'`
harus `index.html` di KEDUA file. Menambal HTML hasil bikin dua file menyimpang pada render berikutnya.

### Pitfall — "file baru" yang sebenarnya hasil lama

Generator yang menulis ke dua tempat (mis. `out/` dan `artifacts/`) bisa meninggalkan salinan lama; menyalin
`artifacts/*` di atas output baru mengembalikan versi lama **tanpa error apa pun**, kadang dengan ukuran byte
identik. Setelah regenerate, buktikan ISI-nya, bukan ukurannya: `grep` penanda perubahan (mis. `min-width:900px`,
`canonical" href="index.html"`) plus `ls -l` mtime. Penanda tidak ada = generator belum jalan, bukan "aman".

## Step 6 — image assets: inline, and check resolution BEFORE placing

Read a brand logo into the page as a base64 `<img>` rather than a gradient-text wordmark — a
`background-clip:text` element renders `color:transparent` and reads as blank in screenshots,
so it can neither be verified nor used as an `<amp-img>`.

```python
import base64
b64 = base64.b64encode(open('/opt/data/brain-vault-git/assets/brand-logos/<brand>.jpg','rb').read()).decode()
# <img src="data:image/jpeg;base64,{b64}" width="150" height="46" alt="<BRAND>">
```

**Measure the asset before deciding how large to show it:**
```python
from PIL import Image; w, h = Image.open(path).size      # e.g. 281x101
```
Keep the rendered width at **≤ 50% of the source width** or it will look soft on a retina
screen. Brand logos at 262–516px wide are therefore header-only (130–250px); a hero or banner
needs a higher-resolution source, not upscaling.

## Step 7 — report honestly

State separately what passed and what is still open (missing AMP variant, placeholder assets,
unresolved design nits). A checklist claiming everything is clean while a CTA is dead costs
far more than listing the gap.

## Reusable probe

`scripts/verify_html.py` runs steps 1–2 against any HTML file:
```
python3 scripts/verify_html.py /path/to/page.html
```
Exits non-zero when an anchor has no target, a tag is unbalanced, or suspected literal markup
is found — safe to run before every send/deploy.
