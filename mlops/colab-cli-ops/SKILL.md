---
name: colab-cli-ops
description: Use when running GPU/TPU jobs on Google Colab from a server.
version: 1.0.0
author: chokdi_staging
license: MIT
metadata:
  hermes:
    tags: [colab, google, gpu, a100, training, cli, headless]
    related_skills: [local-llm-serving, huggingface-hub]
---

# Colab CLI — GPU/TPU headless dari server (TERBUKTI 10-Okt-2026)

Menjalankan job di GPU Google Colab **tanpa browser** — cocok untuk server headless.
Terbukti: CPU VM jalan (`python 3.13.16`, `torch 2.11.0+cpu`, RAM 13.6 GB), provision →
eksekusi → teardown otomatis.

## When to Use

- Bang minta training/fine-tune model di GPU, atau "pakai Colab-nya Bang".
- Butuh GPU (T4/L4/A100/H100) tanpa sewa VPS GPU.
- Analisis data besar / batch job sekali jalan.

## Pilih tool yang BENAR (jangan salah pilih)

| Tool | Arsitektur | Cocok? |
|---|---|---|
| **`google-colab-cli`** | **headless, jalan di server** | ✅ **PAKAI INI** |
| `colab-mcp` | butuh agent **lokal** + Colab di browser | ❌ server kita headless |
| CDP browser (vdesk) | kendali UI manual | ⚠️ plan B saja |

README `colab-mcp` menyebut *"requires the client to be running locally on your device"* —
**jangan** pasang itu untuk server.

## Install & authorize (sekali saja)

```bash
export PATH="/root/.local/bin:$PATH"
uv tool install "git+https://github.com/googlecolab/google-colab-cli"
colab version           # → 0.7.5.dev3+v...
colab sessions          # pertama kali → cetak URL OAuth
```

### 🔴 PITFALL: kode OAuth HARUS dari sesi yang SEDANG JALAN

`colab sessions` pertama kali mencetak URL, minta kode, lalu **abort** kalau tidak dijawab.
Kode yang dibuat dari URL sesi yang sudah mati → `InvalidGrantError: (invalid_grant) Invalid code verifier`.

**Alur yang benar:**
1. Jalankan interaktif dengan **pty** di background:
   `terminal(background=true, pty=true)` → `colab sessions`
2. Ambil URL dari output, kirim ke Bang.
3. Bang approve → dapat kode → **submit ke proses YANG SAMA**
   (`process(action="submit", session_id=..., data="<kode>\n")`).
4. **Jangan** tulis ke `/dev/pts/N` pakai `cat` — tidak masuk ke stdin proses yang di-pipe.

Kalau salah: ulangi dari langkah 1 (URL + kode baru). Token tersimpan di
`~/.config/colab-cli/token.json` setelah sukses.

## Perintah harian

```bash
colab run [--gpu T4|L4|G4|A100|H100] [--high-mem] SCRIPT.py [ARGS]   # ephemeral: buat-eksekusi-hapus
colab new --gpu A100 -s nama       # sesi persisten
colab exec -f local.py             # kirim & jalankan file lokal di kernel
colab exec < script.py             # dari stdin
colab ls / upload / download / rm  # file di VM
colab install -r requirements.txt  # pakai uv (fallback pip)
colab ssh                          # SSH ke runtime (bisa jadi ProxyCommand IDE)
colab drivemount                   # mount Google Drive (/content/drive)
colab auth                         # kredensial GCP (BigQuery/GCS) di VM
colab status | sessions | stop     # lifecycle
colab url --open                   # URL sesi (untuk debug visual)
```

**`colab run` argumennya FILE, bukan string kode.** `colab run "print(1)"` →
`Script not found`. Tulis dulu ke file.

## Biaya — kuota Compute Units (CU)

Bang punya **Google AI Pro = 200 CU/bulan**. Kecepatan bakar:

| GPU | CU/jam | Jam per 200 CU |
|---|---|---|
| T4 | ~1.19 | ~168 jam |
| L4 | ~1.71 | ~117 jam |
| A100 40GB | ~5.40 | ~37 jam |
| A100 80GB | ~7.52 | ~26 jam |
| G4 (RTX Pro 6000 96GB) | ~8.71 | ~23 jam |

**Aturan: mulai dari T4 untuk tes, naik ke A100 hanya kalau perlu.** Tambahan CU = $9.99/100 CU.
`colab run` sudah auto-teardown — jangan tinggalkan sesi persisten tanpa perlu (CU tetap terbakar).

## Verifikasi

1. `colab sessions` → tidak error (login valid).
2. `colab run /tmp/test.py` → output kode kita (bukan error auth).
3. `~/.config/colab-cli/token.json` ada, mode 600.
4. Untuk GPU: jalankan `nvidia-smi` / `torch.cuda.get_device_name(0)` di VM dan **tunjukkan
   outputnya** — jangan klaim GPU dari nama flag saja.

## Keamanan

- Token OAuth = akses ke akun Google Bang → simpan mode 600, jangan cetak, jangan commit.
- Kode OAuth boleh lewat chat (sekali pakai, terikat sesi) tapi **jangan** simpan ke file/log
  permanen; hapus file temp setelah dipakai.
