# Analisis Export Usage DeepSeek Platform (proven 2026-08-15)

Bang kirim export ZIP dari platform.deepseek.com (Usage → Export) dan minta analisis biaya.
File: zip berisi 2 CSV:
- `cost-YYYY-MM-DD_YYYY-MM-DD.csv` — baris per jam: cost USD, input/cache-hit/cache-miss/output tokens
- `amount-YYYY-MM-DD_YYYY-MM-DD.csv` — jumlah request per jam

## Langkah
1. Extract zip dengan `zipfile` (unzip CLI tidak selalu ada):
   `python3 -c "import zipfile; z=zipfile.ZipFile('<file>.zip'); z.extractall('/tmp/usage_ds')"`
2. Parse CSV (`csv.DictReader`, encoding `utf-8-sig` — BOM!): per jam → cost, tokens.
3. Aggregate: total cost, total request, total token, split cache-hit vs cache-miss vs output.
4. Print jam puncak (top 3-5 cost/jam) — pola beban harian.

## Insight yang TERBUKTI berguna (contoh real: 2026-08-15, key "cumi")
- **Cost $6.83/hari = ±$205/bln** — jauh di bawah estimasi kasar Bang (10-20 USD/hari = 300-600/bln).
  Selalu hitung dari data export, bukan tebakan.
- **Cache hit 81%** (184.9jt dari 227.5jt token) = prompt berulang (system prompt sama) → hemat 10x
  (cache $0.0028/M vs miss $0.14/M di DeepSeek).
- **Biaya terbesar = input cache-MISS 40jt token = $5.6 (82% dari total)** — bukan output (2.4jt = $0.69, murah).
- Cara tekan biaya: naikkan cache hit → pakai prompt template konsisten (jangan gonta-ganti system
  prompt per call); audit siapa request 2,971×/hari (retry loop / cron nyangkut = boros).
- Pisah key per proyek (pola key "cumi" = proyek Shendy/Cakra) biar attribution jelas.

## Pitfall
- CSV pakai BOM (`utf-8-sig` wajib, kalau `utf-8` nama kolom pertama jadi `\ufeffcost`).
- Kolom jam = string ISO; sort string aman (format konsisten).
- Export "Today" cuma 1 hari — minta range lebih panjang kalau mau tren bulanan.
- Hermes masking: jangan print token/key ke stdout saat analisis — cukup metrik agregat.
