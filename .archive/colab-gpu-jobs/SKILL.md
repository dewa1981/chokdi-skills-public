---
name: colab-gpu-jobs
description: Use when running long GPU jobs or image generation on Colab.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [colab, gpu, timeout, diffusers, image-generation, t4]
    related_skills: [colab-cli-ops, banner-judi-cf, huggingface-hub]
---

# Colab GPU Jobs — menjalankan job panjang tanpa kena timeout

Prosedur untuk menjalankan job GPU/TPU di Google Colab **dari server headless** tanpa
berakhir `TimeoutError: Timeout waiting for reply`.

> Setup/login Colab CLI ada di skill `colab-cli-ops`. Skill ini melanjutkan dari titik itu:
> apa yang boleh dijalankan dalam satu perintah, apa yang harus dipecah, dan bagaimana
> mengambil hasilnya.

## When to Use

- Job GPU di Colab gagal/timeout di tengah, atau diperkirakan butuh waktu lama (download model besar).
- Generate gambar / inference model open-source di Colab T4.
- Perlu mengambil artefak (gambar, bobot model) dari VM Colab sebelum teardown.

## Aturan inti: kernel timeout, bukan GPU-nya

Gejala: perintah tampak jalan normal, lalu berakhir
`jupyter_kernel_client/wsclient.py … TimeoutError: Timeout waiting for reply`.
Itu **bukan** bug Colab dan bukan kekurangan VRAM — kernel berhenti menjawab kalau satu
perintah dijalankan terlalu lama. Obatnya memecah pekerjaan, bukan mengganti GPU.

### Anggaran waktu yang aman (T4 terukur)

| Kerja | Durasi | Aman dalam 1 perintah? |
|---|---|---|
| Download model ~2.5 GB (sd-turbo) | ~35 s | ✅ |
| Inference setelah model siap | 1–4 s | ✅ |
| Download model ~7 GB (SDXL) | ~3 menit+ | ❌ hampir pasti timeout |
| Download model ~12 GB (FLUX penuh) | lebih lama | ❌ timeout |

## Prosedur: pecah download dari inference

1. **Buktikan pipeline dengan model KECIL dulu.** `stabilityai/sd-turbo` (~2.5 GB) cukup untuk
   membuktikan bahwa diffusers + GPU + penulisan file semuanya jalan. Model besar bukan cara
   membuktikan konsep — yang gagal downloadnya, bukan kodenya, dan kegagalan itu tidak
   memberikan informasi apa pun tentang kode kita.
2. **Untuk model besar, buka sesi persisten** (`colab new --gpu T4 -s kerja`) dan unduh model di
   satu perintah terpisah dari langkah inference. Kalau langkah download yang timeout, model
   yang sudah terunduh tetap ada di sesi itu.
3. **Set `HF_TOKEN` di VM** kalau tersedia. Tanpa token, HuggingFace membatasi kecepatan — inilah
   yang membuat jendela timeout terlewati pada model ≥ 7 GB.
4. **Ambil hasil dengan `colab download`, jangan `colab drivemount`.** Mount Drive menunggu
   interaksi sehingga ikut timeout di alur headless. Setelah `colab run` selesai, VM-nya sudah
   dibuang — jadi untuk mengambil file, gunakan sesi persisten (`colab new` + `--keep`).

### Cetak path artefak dari dalam script

```python
img.save("/content/hasil.png")
print("PATH=/content/hasil.png")   # bisa di-parse dari luar
```

## Membandingkan dengan tool yang sudah dipunyai (jangan jual berlebihan)

Sebelum menawarkan Colab untuk text-to-image, cek dulu jalur gratis yang sudah jalan:

| Kebutuhan | Yang benar dipakai |
|---|---|
| Banner/artwork rutin (text-to-image) | **gateway CF FLUX.2 / 9router** — gratis, tanpa download model |
| Latih/fine-tune model sendiri | **Colab** — ini yang benar-benar tidak dimiliki di tempat lain |
| Cadangan saat kuota image harian habis | Colab |

Terukur: sd-turbo di T4 = **3.7 s/gambar**. Cepat, tapi tetap kalah praktis dari gateway karena
setiap sesi baru harus download model lagi. **Colab menang pada training, bukan pada generate.**
Kalau Bang tanya "Colab buat apa?", jawab dengan tabel ini apa adanya — jangan mengarang
justifikasi supaya alat yang baru dipasang terlihat berguna.

## Verifikasi

1. Script VM mencetak nama GPU + `torch.cuda.is_available()` — bukti GPU nyata, bukan nama flag.
2. Ukuran file hasil (`os.path.getsize`) dicetak — memisahkan "generate jalan" dari "file kosong".
3. Setelah `colab download`, cek file ada di sisi server sebelum melaporkan sukses.
