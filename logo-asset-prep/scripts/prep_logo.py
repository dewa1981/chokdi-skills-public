#!/usr/bin/env python3
"""Prep a logo for web use: circle-crop a badge to transparency, export 512 PNG / 192 WebP / OG 1200.

Usage:
    python3 prep_logo.py <input.jpg|png> [outdir] [--radius-percentile 99.9] [--no-circle]

Outputs (default: ./prepped beside the input):
    logo_512.png   RGBA master
    logo_192.webp  small inline asset (quality 92)
    og_logo.png    1200 px
    _preview_white.jpg / _preview_dark.jpg   sanity composites

Notes:
  * Circle mode assumes a round badge on a dark/plain background. If the badge touches the frame edge,
    lower --radius-percentile (e.g. 99.5) or pass --no-circle to keep the full rectangle.
  * PIL MaxFilter/MinFilter only accept ODD sizes >= 3 (otherwise: "bad filter size").
"""
import argparse
import io
import os

import numpy as np
from PIL import Image, ImageFilter


def odd(n):
    n = int(n)
    return n if n % 2 == 1 else n + 1


def clean(mask, close=5, open_=3):
    img = Image.fromarray((mask * 255).astype(np.uint8))
    if close and close > 1:
        k = odd(close)
        img = img.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    if open_ and open_ > 1:
        k = odd(open_)
        img = img.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    return np.array(img) > 127


def circle_alpha(im, pct=99.9, feather=1.8, thresh=70):
    a = np.array(im).astype(int)
    bright = a.max(axis=2)
    ys, xs = np.where(bright > thresh)
    if len(xs) == 0:
        raise SystemExit("nothing bright enough to detect a badge; try --no-circle")
    cy, cx = ys.mean(), xs.mean()
    r = float(np.percentile(np.hypot(ys - cy, xs - cx), pct))
    H, W = im.height, im.width
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.hypot(xx - cx, yy - cy)
    alpha = np.clip((r - dist) / feather, 0, 1)
    box = (max(0, int(cx - r - 4)), max(0, int(cy - r - 4)),
           min(W, int(cx + r + 4)), min(H, int(cy + r + 4)))
    return (alpha * 255).astype(np.uint8), box, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("outdir", nargs="?", default=None)
    ap.add_argument("--radius-percentile", type=float, default=99.9)
    ap.add_argument("--no-circle", action="store_true")
    args = ap.parse_args()

    outdir = args.outdir or os.path.join(os.path.dirname(os.path.abspath(args.src)), "prepped")
    os.makedirs(outdir, exist_ok=True)

    im = Image.open(args.src).convert("RGB")
    if args.no_circle:
        rgba = im.convert("RGBA")
    else:
        alpha, box, r = circle_alpha(im, args.radius_percentile)
        rgba = im.convert("RGBA")
        rgba.putalpha(Image.fromarray(alpha))
        rgba = rgba.crop(box)
        print(f"circle: r={r:.1f}px crop={rgba.size}")

    # square canvas keeps header/footer sizing predictable
    side = max(rgba.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2), rgba)

    p512 = sq.resize((512, 512), Image.LANCZOS)
    p512.save(os.path.join(outdir, "logo_512.png"))

    p192 = sq.resize((192, 192), Image.LANCZOS)
    buf = io.BytesIO()
    p192.save(buf, "WEBP", quality=92, method=6)
    open(os.path.join(outdir, "logo_192.webp"), "wb").write(buf.getvalue())

    sq.resize((1200, 1200), Image.LANCZOS).save(os.path.join(outdir, "og_logo.png"))

    for name, bg in (("white", (255, 255, 255)), ("dark", (17, 19, 21))):
        canvas = Image.new("RGBA", p512.size, bg + (255,))
        canvas.alpha_composite(p512)
        canvas.convert("RGB").save(os.path.join(outdir, f"_preview_{name}.jpg"), quality=93)

    for f in ("logo_512.png", "logo_192.webp", "og_logo.png"):
        p = os.path.join(outdir, f)
        print(f"{f:16s} {os.path.getsize(p)/1024:7.1f} KB")
    print("done ->", outdir)


if __name__ == "__main__":
    main()
