# Varian URL & scope

| Varian | URL | Catatan |
|---|---|---|
| US | `https://api.us.elevenlabs.io/v1/mcp` | yang dipakai halaman Hermes resmi mereka |
| Global | `https://api.elevenlabs.io/v1/mcp` | disebut di instruksi Claude Code |

Keduanya balas **POST `401`** tanpa auth (hidup). **Pilih satu, jangan bolak-balik** hanya karena beda 401/405
— probe POST dulu (lihat SKILL.md langkah 2).

Scope OAuth yang diminta server: `convai_read`, `convai_write`, `text_to_speech`, `speech_history_read`,
`flows`, `image_video_generation`, `voice_generation`.

# ⚠️ Dua jebakan khas ElevenLabs (keduanya terlihat seperti "server rusak", padahal bukan)

## 1. `oauth.redirect_port` MEMATIKAN flow-nya

Gejala: `Errno 98 Address already in use` di port callback → kalau di"perbaiki" dengan mengisi
`oauth.redirect_port` di blok server, login langsung gagal:
`Registration failed: 404 {"detail":"Not Found"}`.

Sebab: ElevenLabs memakai **client_id statis** (`nousresearch.github.io/hermes-agent/docs/oauth/client-metadata.json`),
bukan dynamic client registration. Mengganti port memindahkan flow ke jalur DCR yang tidak mereka layani.

**Aturan: JANGAN pernah menyetel `oauth.redirect_port` untuk ElevenLabs.** Biarkan port default.
Kalau `Errno 98` muncul (port masih dipegang proses login sebelumnya), cukup **ulangi perintah login** —
tidak perlu ganti port, tidak perlu ubah config.

## 2. Proses login MATI SENDIRI kalau menunggu terlalu lama

Sesi `hermes mcp login --flow browser` bisa keluar sendiri dalam ~2 menit (kadang dengan pesan `Errno 98`
yang menyesatkan, kadang dengan pesan habis waktu). Kalau itu terjadi SETELAH user menekan Authorize, kode
yang dia bawa sudah tidak ada tujuan — `process(action='submit')` akan balas `already_exited`.

**Aturan untuk minta ke user: authorize DULU, baru paste balikannya — jangan dibuat menunggu.**
Ikuti dengan `process(action='poll')` untuk melihat `Got authorization code from paste — completing flow.`
lalu `✓ Authenticated — N tool(s) available`. Kalau sesi sudah mati: start ulang login, kirim link BARU
(state+PKCE baru), dan minta authorize lagi. Jangan mencoba menempelkan URL lama ke sesi baru.

# Setelah auth sukses: `enabled` masih `false`

Auth berhasil belum berarti aktif. Entry hasil `mcp add` yang connect-nya gagal tersimpan sebagai
`enabled: false`, dan `hermes mcp configure` menolak jalan tanpa terminal interaktif.
Set manual di `config.yaml` (backup dulu): set `enabled: true` pada blok servernya, lalu
`hermes mcp list` harus menampilkan `✓ enabled`.

# Yang didapat setelah tersambung

- **ElevenCreative** — voice, musik, gambar, video lewat 50+ model dalam satu konektor.
- **ElevenAgents** — bikin/ubah voice & chat agent (system prompt, voice, first message), lihat performa dari
  transcript/latensi, duplikat/hapus agent, estimasi biaya LLM, ambil widget config & share link.
- Akses bisa dibatasi: dari *read-only monitoring* sampai *full agent management*.
- Jumlah tool yang benar-benar terdaftar bisa **lebih banyak dari yang diiklankan**: `agents_*` mendominasi
  (puluhan tool), `creative_*` belasan, plus `get_more_tools`. **Laporkan hasil `tools/list` yang diamati**,
  jangan mengutip angka dari dokumentasi.

# Penting: jangan dicampur dengan TTS yang sudah jalan

Stack kita sudah punya `ELEVENLABS_API_KEY` di `.env` untuk TTS/STT dan JARVIS (voice Andi). MCP ini pakai
**OAuth**, bukan key itu — jangan menyuntikkan `Authorization` header dari key lama ke server MCP ini, dan
jangan mengganti key itu karena MCP sudah tersambung.

# Klien lain (referensi cepat)

- Claude Code: `claude mcp add --transport http elevenlabs https://api.elevenlabs.io/v1/mcp` lalu `/mcp` di
  dalam sesi untuk login.
- ChatGPT / Claude / Cursor / GrokBot: install dari direktori plugin masing-masing, sekali OAuth, tanpa API key.

