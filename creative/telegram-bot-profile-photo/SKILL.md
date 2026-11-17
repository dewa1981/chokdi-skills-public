---
name: telegram-bot-profile-photo
description: "Use when setting a Telegram bot profile photo."
version: 1.0.0
author: chokdi_staging
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [telegram, bot, profile, photo, avatar, nanobanana]
---

# Ganti Foto Profil Bot Telegram

Set foto profil bot lewat Bot API. Dipakai untuk `teamrambo2` / `teamrambo3` (30-Sep-2026).

## When to Use
- User minta "bikin/ganti foto profil bot <nama>" atau avatar bot Telegram.
- Bot baru selesai di-deploy dan perlu avatar biar tidak polos.
- Ganti avatar bot lama ke gambar baru.

## Yang BENAR (satu-satunya cara via API)
```bash
# 1. FOTO WAJIB .JPG — bukan PNG! (PNG ditolak "photo isn't specified")
python3 -c "
from PIL import Image
Image.open('gambar.png').convert('RGB').save('gambar.jpg','JPEG',quality=92)
"

# 2. Kirim sebagai InputProfilePhotoStatic via multipart
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/setMyProfilePhoto" \
  -F 'photo={"type":"static","photo":"attach://file0"};type=application/json' \
  -F 'file0=@gambar.jpg;type=image/jpeg'
# sukses -> {"ok":true,"result":true}
```

## Yang SALAH (jangan dicoba lagi — sudah kena)
| Cara | Hasil |
|---|---|
| `setChatPhoto` + `chat_id=<bot_id>` | ❌ `can't change private chat photo` — itu untuk grup/chat, bukan profil bot |
| `setMyProfilePhoto -F 'photo=@x.png'` | ❌ `photo isn't specified` — bukan form-file, harus JSON `InputProfilePhoto` |
| PNG sebagai `file0` | ❌ format static **harus JPG** (animasi pakai MPEG4) |

Catatan: `setMyProfilePhoto` = **Bot API 9.4+**. Kalau endpoint tidak dikenal, error-nya
berbeda (`not found`), bukan `Bad Request`. Kalau muncul `"photo isn't specified"` berarti
endpoint-nya ADA, cuma payload-nya salah — perbaiki payload, jangan ganti endpoint.

## Verifikasi
- Jawaban sukses = `{"ok":true,"result":true}`. **Itu bukti utama.**
- `getUserProfilePhotos?user_id=<bot_id>` **TIDAK bisa** dipakai bot untuk melihat fotonya
  sendiri (`user not found`) — jangan simpulkan "gagal" dari situ.
- Konfirmasi visual terakhir dari sisi user (buka bot di Telegram), atau kirim gambarnya ke chat.

## Bikin gambarnya
- **NanoBanana** (`api.nanobananaapi.ai`) — resep lengkap di skill `nanobanana-image-api`.
  `image_size: 1:1`, dan untuk avatar pakai prompt "upper body portrait facing forward,
  centered composition, clean solid dark background, no text, no watermark, avatar profile
  picture". Hasilnya 1024x1024 — sudah pas (Telegram minimal 320x320, square).
- Kalau bikin beberapa bot sekaligus, **bedakan atribut visual** (mis. warna bandana / senjata)
  biar avatar tidak kembar. Untuk batch, lihat `scripts/nanobanana_batch.sh`.
- **Cek dulu gambarnya pakai `vision_analyze` sebelum dikirim** — pastikan tidak ada teks/watermark
  yang rusak dan karakternya sesuai; jangan percaya prompt saja.
- Simpan hasil (JPG+PNG) di disk sebelum upload: URL NanoBanana (`tempfile.aiquickdraw.com`)
  bersifat sementara — download dulu.
