---
name: football-flags
description: Flag emoji database for football club/national team reports.
---

# Football Flags Database (bendera klub & tim nasional)

Skill referensi bendera emoji untuk laporan sepak bola (dipakai cron **Jadwal Bola Harian** b0fa69e1a2c4 dan laporan skor manual). Cron me-load skill ini dengan `references/club-flags.md` — kalau skill ini hilang, cron warning *"Skill(s) not found and skipped: football-flags"*.

## Cara pakai
1. Load `references/club-flags.md` dari skill ini (atau dari skill `football-score-reports` yang punya salinan identik).
2. Bendera klub = bendera NEGARA asal klub. JANGAN tebak, JANGAN pakai bendera sama untuk semua klub.
3. Liga → bendera liga: 🇬🇧 Premier League, 🇩🇪 Bundesliga, 🇪🇸 La Liga, 🇮🇹 Serie A, 🇫🇷 Ligue 1, 🇪🇺 UEFA (UCL/UEL/UNL).

## Ringkasan cepat (detail lengkap di references/club-flags.md)
- Semua klub Inggris (Arsenal, Liverpool, Man City, Chelsea, Spurs, Newcastle, dll) = 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (England)
- Semua klub Jerman = 🇩🇪, Spanyol = 🇪🇸, Italia = 🇮🇹, Prancis = 🇫🇷, Portugal = 🇵🇹, Belanda = 🇳🇱, Turki = 🇹🇷, Belgia = 🇧🇪
- Skotlandia (Celtic, Rangers) = 🏴󠁧󠁢󠁳󠁣󠁴󠁿 — BUKAN bendera Inggris
- Wales = 🏴󠁧󠁢󠁷󠁬󠁳󠁿, Irlandia Utara = 🇬🇧/🏴󠁧󠁢󠁮󠁩󠁲󠁿

## Pitfalls
- Bendera England vs Skotlandia sering ketuker — cek tag sequence-nya.
- Klub di luar daftar: cek negara asal dulu (Wikipedia) sebelum pasang bendera.
- Jangan pernah pakai satu bendera untuk semua klub di satu laporan.

## Files
- `references/club-flags.md` — tabel lengkap klub → bendera negara.
