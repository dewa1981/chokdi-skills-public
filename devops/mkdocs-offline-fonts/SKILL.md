---
name: mkdocs-offline-fonts
description: "Use when mkdocs site loads slow due to Google Fonts CDN."
version: 1.0.0
metadata:
  hermes:
    tags: [mkdocs, fonts, offline, performance, static-site]
    category: devops
---

# MkDocs-Material Offline Fonts

## Problem
mkdocs-material loads Google Fonts from `fonts.googleapis.com` and `fonts.gstatic.com`. On slow/mobile/Tailscale connections, this causes pages to hang waiting for CDN.

## Fix: Local Font Hosting (proven 2026-08-22)

### Step 1: Download all woff2 files
```bash
SITE="/path/to/site"  # mkdocs build output dir
FONTS="$SITE/assets/fonts"
mkdir -p "$FONTS"

# Get CSS with modern browser UA (forces woff2 format)
CSS=$(curl -sL -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" \
  "https://fonts.googleapis.com/css?family=Roboto:300,300i,400,400i,700,700i|Roboto+Mono:400,400i,700,700i&display=swap")

# Extract and download all woff2 files
echo "$CSS" | grep -oP 'url\(\K[^)]+' | grep woff2 | sort -u | while read url; do
  fname=$(echo "$url" | sed 's|.*/||')
  curl -sL "$url" -o "$FONTS/$fname"
done
```

### Step 2: Create local-fonts.css
```css
@font-face{font-family:'Roboto';font-style:italic;font-weight:400;font-display:swap;src:url(KFO5...woff2) format('woff2')}
@font-face{font-family:'Roboto';font-style:normal;font-weight:400;font-display:swap;src:url(KFO7...woff2) format('woff2')}
@font-face{font-family:'Roboto';font-style:normal;font-weight:700;font-display:swap;src:url(KFO7...woff2) format('woff2')}
@font-face{font-family:'Roboto Mono';font-style:normal;font-weight:400;font-display:swap;src:url(L0x5...woff2) format('woff2')}
@font-face{font-family:'Roboto Mono';font-style:normal;font-weight:700;font-display:swap;src:url(L0x7...woff2) format('woff2')}
```

### Step 3: Replace Google Fonts links in all HTML files
```bash
# Replace external font CSS link with local
find "$SITE" -name '*.html' -exec sed -i \
  's|<link rel="stylesheet" href="https://fonts.googleapis.com/css[^"]*">|<link rel="stylesheet" href="PATH_TO/local-fonts.css">|g' {} +

# Remove any remaining fonts.gstatic.com refs in CSS files
find "$SITE/assets" -name '*.css' -exec sed -i 's|https://fonts.gstatic.com|..|g' {} +
```

### Step 4: Fix relative paths
The `PATH_TO` depends on HTML file depth:
- Root HTML (`index.html`): `assets/fonts/local-fonts.css`
- 1 level deep (`sub/index.html`): `../assets/fonts/local-fonts.css`
- 2 levels deep (`sub/sub2/index.html`): `../../assets/fonts/local-fonts.css`

### Step 5: Verify
```bash
# No more external font refs
grep -rl 'fonts.googleapis.com' "$SITE" | wc -l  # should be 0
grep -rl 'fonts.gstatic.com' "$SITE" | wc -l     # should be 0

# Local font CSS accessible
curl -s -o /dev/null -w '%{http_code}' "URL/assets/fonts/local-fonts.css"  # should be 200
```

## Pitfalls
- Must use **modern browser User-Agent** header when fetching Google Fonts CSS — without it, Google returns TTF format instead of woff2
- Relative paths in local-fonts.css must match HTML file depth — `url(filename.woff2)` (same dir) not `url(../fonts/filename.woff2)`
- Font file names are long hashes — don't rename them, keep original names
- Total size ~776KB for Roboto + Roboto Mono (30 files, all subsets)
- This is a one-time operation — fonts rarely change
