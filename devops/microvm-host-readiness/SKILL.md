---
name: microvm-host-readiness
description: "Check if a host can run microVM/Firecracker sandboxes."
version: 1.0.0
---

# MicroVM Host Readiness — bisakah server ini menjalankan sandbox Firecracker?

Dipakai saat pertanyaannya berbentuk **"server ini bisa dipakai nggak buat X?"** di mana X = platform agent
yang mengisolasi tiap agent di VM sendiri (OpenBot, FireClaw, CubeSandbox, atau sandbox buatan sendiri).

Aturan pertama: **jawab dengan probe, bukan spek halaman provider.** RAM 64 GB tidak ada gunanya kalau
`/dev/kvm` tidak ter-expose. Salah di sini bikin janji deploy yang tidak bisa ditepati.

> 📄 `references/memoh-and-mobile-client-model.md` — model resource per platform (Memoh 6+N container,
> sandbox tidak menambah container), cara menghitung bot dari DB, pola diagnosa "app mobile nggak kirim
data", API key sebagai kolom vs tabel, dan aturan jangan-login-akun-pribadi-owner.

## Probe wajib — satu batch, read-only

```bash
ls -l /dev/kvm                                    # KUNCI UTAMA: harus ada (crw-rw---- root kvm)
cat /sys/module/kvm_amd/parameters/nested         # harus 1 (Intel: /sys/module/kvm_intel/parameters/nested)
lsmod | grep kvm                                  # kvm + kvm_amd/kvm_intel ter-load
lscpu | grep -E 'Model name|Virtualization|Hypervisor vendor|Virtualization type'
nproc; free -h; df -h /
command -v qemu-system-x86_64 firecracker node pnpm   # toolchain yang belum ada
systemd-detect-virt                              # 'kvm' = di atas hypervisor; 'lxc'/'openvz' = microVM TIDAK bisa
```

**Ambang keputusan:**

| Temuan | Artinya |
|---|---|
| `/dev/kvm` ada + `nested = 1` | microVM **bisa** jalan |
| `/dev/kvm` ada tapi `nested = 0` | belum bisa — minta provider nyalakan nested virt |
| `/dev/kvm` tidak ada | **tidak bisa**, dan tidak ada cara mengakalinya. Ganti VPS |
| `systemd-detect-virt` = `lxc`/`openvz` | container virtualisasi, bukan KVM — microVM tidak bisa |

## Yang HARUS disampaikan, bukan disembunyikan

1. **Nested KVM lebih lambat dari bare metal.** Untuk eksperimen cukup; untuk produksi banyak agent,
   katakan apa adanya. Jangan jual sebagai setara dedicated.
2. **KVM tersedia ≠ boleh dipakai.** Kalau box itu sudah menjalankan stack lain yang memakai KVM/containerd
   (mis. Memoh dengan embedded containerd + satu container per bot), menambah platform microVM kedua berarti
   **berebut KVM yang sama**. Secara teknis bisa; secara operasional rapuh. Sarankan **direktori terpisah**
   (`/opt/<platform>`), jangan instal ke host yang sama-sama dipakai.
3. **Cek bentrok port** dengan yang sudah jalan sebelum menjanjikan instalasi.
4. **Provider yang meng-expose KVM relatif langka.** Kalau ketemu satu, **catat node + provider-nya** — itu
   aset untuk keputusan pembelian VPS berikutnya.

## Pertanyaan "app-nya jalan di mana?" — pisahkan app dari sandbox

Jangan jawab dengan prosa. Tabel:

| Komponen | Butuh apa | Bisa di Mac? |
|---|---|---|
| **App / UI / orkestrator** (Node + pnpm) | Node 22+, pnpm | ✅ ya, di mana saja |
| **Sandbox microVM (Firecracker)** | Linux + **KVM** | ❌ **tidak** — macOS/Apple Silicon tidak bisa |

Jadi "pasang di Mac Mini" **bukan** opsi untuk komponen sandbox-nya, hanya untuk app/UI-nya. Sebutkan ini
sebelum owner membeli/berencana apa pun.

## Kalau toolchain belum ada

`node`/`pnpm`/`qemu`/`firecracker` yang belum terpasang **bukan** blocker dan **bukan** alasan bilang "tidak
bisa" — itu langkah instalasi biasa. Yang benar-benar blocker hanya `/dev/kvm` + nested virt. Laporkan
pemisahan ini dengan jelas: mana yang tinggal di-install, mana yang mustahil di host itu.

## Model resource per platform (untuk pertanyaan "cukup nggak server ini?")

Bedakan **stack platform** dari **tambahan per-agent** — ini yang bikin perkiraan RAM sering salah:

| Platform | Container | Butuh KVM? |
|---|---|---|
| **Memoh** (self-host) | **6 stack inti** (server, web, Postgres, pgvector, migrate, channel worker) **+ 1 per bot** | ❌ (containerd biasa) |
| **Hermes / OpenClaw** | 1 proses agent kuat; isolasi di level proses/file | ❌ |
| **OpenBot / FireClaw** | 1 microVM Firecracker **per agent** | ✅ wajib |

- **Sandbox di dalam bot TIDAK menambah container.** Sandbox Memoh itu layer di dalam container bot
  (namespace/cgroups/chroot). Jadi 6 stack + 5 bot = **11 container**, bukan 16 dan bukan 6+5+5.
  Salah di sini bikin over-estimasi resource ke owner.
- Memoh: **minimum 4 GB RAM** (stack idle 2-3 GB), nyaman 8 GB begitu bot mulai buka browser/desktop.
- **Verifikasi angka container dari host, bukan dari dokumentasi:** `docker ps -a --format '{{.Names}}|{{.Status}}'`,
  lalu query DB-nya untuk jumlah bot (`bots`, `containers`). Memoh simpan bot sebagai baris tabel, dan
  satu baris bot = satu container workspace dengan status `running`.
- **Jangan pakai jumlah container yang sedang jalan sebagai bukti kapasitas microVM** (lihat Pitfall) —
  tapi jumlah container itu bukti bagus untuk *model resource* platform yang sedang jalan.

## Pitfall

- **Jangan menyimpulkan kemampuan host dari nama/tipe produknya.** Dua VPS dari provider yang sama bisa
  berbeda soal nested virt. Selalu probe host yang benar-benar akan dipakai.
- **Jangan memakai jumlah container yang sedang jalan sebagai bukti kapasitas.** Kapasitas microVM
  ditentukan KVM + RAM + disk, bukan berapa container yang kebetulan hidup.
- **Jangan menawarkan VDesk/browser untuk pekerjaan ini.** Ini murni pemeriksaan host.
- **Sebut efek sampingnya kalau menyarankan co-exist:** dua platform yang sama-sama butuh KVM tidak
  saling merusak secara otomatis, tapi satu yang bikin host goyang akan menjatuhkan yang lain. Sampaikan
  trade-off-nya, jangan cuma bilang "bisa".
