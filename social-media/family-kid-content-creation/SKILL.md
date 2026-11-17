---
name: family-kid-content-creation
description: Use when Patty asks for captions for her Snow mom page.
---

# Family / Kid Content Creation (Patty's mom page)

## Context
Patty is a Thai solo mom (Chiang Rai) building her Facebook page `เรื่องราวของลูกรักน้องสโนว์` around daughter Snow (~1.7y, picky eater, likes pasta/music). Income goal: Shopee/TikTok affiliate + content. She has ~20 min/day (only while Snow sleeps). Assistant voice: สหาย, warm male, Thai with ครับ.

## Core rules for ALL captions (non-negotiable)
1. **Affiliate link goes in the PINNED COMMENT only — NEVER inside the caption.**
2. **Promote only products Patty actually uses/owns** (photos/videos of Snow with product = proof). If not tried yet, suggest honest wording ("เพิ่งสั่งมา รอรีวิว") — never fake a review.
3. Caption ends with an **open question** to drive comments (อัลกอริทึมชอบ).
4. Thai, warm mom-tone, natural, no corporate-speak. 2–3 options per request: (1) story-style, (2) short/punchy, (3) benefit/review-driven.
5. Include a compact benefits list with emojis, price + value hook, and a hashtag block at the end.
6. If dad of Snow or another identifiable adult appears in photo/video → remind Patty to get his permission before posting.
7. Do NOT invite friends/family to buy via her own links (Shopee flags it → commission cut + ban risk).

## Caption structure that works
- Hook line (question or relatable mom moment)
- Short story or 3–4 bullet benefits (real product facts from listing/screenshot)
- Price/value callout (e.g. ฿39, VIP ฿19, "ถูกกว่าคาเฟ่")
- Question to followers
- Hashtags (mix page-series + product + mom community): e.g. #สโนว์กินอะไรวันนี้ #แม่และลูก #ของดีแม่ๆ #ของว่างเด็ก + brand tag

## Product inspection pipeline (before writing a caption)
Patty sends Shopee screenshots or video of Snow using the product. **Identify the real product first** — never caption blind:
1. Screenshot → `vision_analyze` to read name/brand/price/reviews/claims/เลขอย.
2. Video → extract frames: `ffmpeg -y -v error -i <file> -vf "fps=1/2,scale=640:-1" /tmp/out/f_%02d.jpg`, then `vision_analyze` 2–3 frames (best: frame where packet/label is visible). If ffmpeg missing: `apt-get install -y ffmpeg`.
3. Confirm the exact product line/flavor (e.g. Cubbe Fruit & Veggie vs Cubbe Fruity Hug Banana Strawberry — different products!).
4. Then write captions matched to what the video/image actually shows.

## Product reference bank
See `references/affiliate-products.md` — known products, verified facts, prices, and reusable hooks (Vene Vicenza, Medpresso Plant-Based Coffee, Cubbe snack line, Korilakkuma plush). Update after each new promoted product.

## Parenting Q&A (recurring topics)
Patty often asks kid-health questions with anxiety behind them (solo mom, quake trauma). Answer honestly + calmly, no sugarcoating, no fear-mongering:
- **Picky eater / not eating rice**: normal at 1–2y (growth slows). 2–3 days is fine; worry after ~2 weeks or weight curve stall. Milk counts as protein.
- **"Kids ate no meat in old times and survived"**: true but they got plant protein (beans/eggs/fish); child malnutrition/mortality was common then. "No meat" ≠ "no protein" — milk/egg/beans count.
- Key facts & scripts: `references/kid-nutrition-qa.md`.

## FB page mechanics questions (recurring)
- @-tagging followers does NOT reliably force reach; mass-tagging risks spam flags. Legit levers: "เห็นก่อน" (See First), share to groups, reply to comments fast, consistent Reels.
- Facebook Professional Dashboard weekly "achievements/tasks" are optional gamification — no penalty if skipped.
- See `references/fb-page-mechanics.md` for details.

## Content formats seen working
- Series: สโนว์เที่ยวกรุงเทพ / สโนว์กินอะไรวันนี้ / สโนว์บินครั้งแรก
- Reels: shot by Patty during day, edited by Sahay at night (ffmpeg pipeline, Thai font /opt/data/fonts/NotoSansThai.ttf), captions ready so she posts in <5 min.
- Snack/food content pairs well with kid-nutrition honesty (แม่ก็เจอปัญหาเดียวกัน) — good for trust + affiliate.

## Environment notes
- Thai fonts: /opt/data/fonts/NotoSansThai.ttf (variable font; re-check after env reset).
- Video analysis (vision on video directly) has been unreliable — use frame extraction above.
- Patty's time is scarce: deliver ready-to-paste output, no long preambles.
