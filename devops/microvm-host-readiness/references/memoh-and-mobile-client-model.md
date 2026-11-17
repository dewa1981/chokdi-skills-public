# Memoh / agent-platform resource model + the Dawarich mobile-client pattern

Two things that repeatedly come up when sizing a host for an agent platform, kept here because the
platform-specific skills for Dawarich are user-owned and cannot be curated.

---

## 1. Memoh container model (jawab "cukup nggak server ini?")

Bedakan **stack platform** dari **tambahan per-agent** — ini yang bikin perkiraan RAM sering salah:

| Platform | Container | Butuh KVM? |
|---|---|---|
| **Memoh** (self-host) | **6 stack inti** (server, web, Postgres, pgvector, migrate, channel worker) **+ 1 per bot** | ❌ (containerd biasa) |
| **Hermes / OpenClaw** | 1 proses agent kuat; isolasi di level proses/file | ❌ |
| **OpenBot / FireClaw** | 1 microVM Firecracker **per agent** | ✅ wajib |

- **Sandbox di dalam bot TIDAK menambah container.** Sandbox Memoh itu layer di dalam container bot
  (namespace/cgroups/chroot). Jadi 6 stack + 5 bot = **11 container** — bukan 16, bukan 6+5+5.
  Salah di sini bikin over-estimasi resource ke owner.
- Memoh: **minimum 4 GB RAM** (stack idle 2-3 GB), nyaman 8 GB begitu bot mulai buka browser/desktop.
- **Verifikasi jumlah bot dari DB, bukan dari tebakan.** Bot disimpan sebagai baris tabel, satu baris
  bot = satu container workspace status `running`:
  ```bash
  docker exec <pg_container> psql -U memoh -d memoh -c "select id, name, status from bots;"
  docker exec <pg_container> psql -U memoh -d memoh -c "select id, bot_id, status from containers;"
  ```
  Nama user/DB bukan `postgres` — ambil dari `config.toml` / blok `POSTGRES_*` di compose.
- Container pendukung yang sering ikut jalan dan tidak boleh dihitung sebagai "bot":
  `openviking` (memory backend), `portainer`, `searxng`, `lightpanda`, `playwright-mcp`.
- **Jangan pakai jumlah container yang sedang jalan sebagai bukti kapasitas microVM** — untuk kapasitas,
  yang menentukan tetap `/dev/kvm` + RAM + disk.

### Memoh SSH
Port SSH bisa **bukan 22** dan port 22 di Tailscale IP bisa `Connection refused` sementara port lain
terbuka. Scan port sebelum menyimpulkan host mati:
```bash
for p in 22 22022 2222; do timeout 5 bash -c "echo > /dev/tcp/<ip>/$p" 2>/dev/null && echo "OPEN $p"; done
```

---

## 2. Pola "app mobile → API server sendiri" (dipakai Dawarich, berlaku umum)

Untuk app yang di-connect ke instance self-hosted (Dawarich, Immich, dsb), urutan yang benar saat owner
lapor "kok belum ada data?" — **jangan tebak, buktikan berlapis**:

1. **Jumlah record di DB** (pool sisi server).
2. **Log request masuk** — ini bukti terkuat client↔server sehat. Terlihat `GET/PATCH
   /api/v1/settings/mobile` → `200` berarti: client konek, API key BENAR, setting tersimpan.
   Log JSON Rails sering biner → **pipe `strings` dulu**, kalau tidak `grep` balas
   "binary file matches" dan isinya tidak kelihatan.
3. **Tes jalur tulis dari server** (POST satu record dummy pakai API key owner). `200` + id = jalur
   tulis hidup, terbukti terlepas dari HP. **Hapus record tes itu setelahnya.**
4. Baru simpulkan.

**Kesimpulan yang paling sering benar untuk app location tracking: client PAUSE update saat device diam**
("paused updates while still") dan menunggu batch penuh. Device diam di rumah = 0 record itu **NORMAL,
BUKAN bug** — yang perlu dilakukan owner: **bawa device gerak 200-300 m**. Jangan mengubah setting
berkali-kali atau restart server selama log masih 200.

### API key yang disimpan sebagai kolom, bukan tabel relasi
Sebagian app (mis. Dawarich) menyimpan API key sebagai **kolom di tabel user**, bukan tabel `api_keys`
terpisah. `user.api_keys.create!(...)` gagal `NoMethodError: undefined method 'api_keys'`. Pola aman:
```bash
docker exec <app> bash -lc 'cat > /tmp/k.rb <<"RUBY"
puts User.find(<id>).api_key.to_s
RUBY
cd /var/app && bin/rails runner /tmp/k.rb'
```
Tulis script **ke file di dalam container** — `runner 'puts ...'` inline sering bikin
`unexpected EOF while looking for matching` lewat SSH bertingkat.
Key-nya dikirim ke **DM owner**, jangan ke grup/log/commit.

### Donasi/patreon app open-source: cek dulu sebelum menyuruh owner bayar
Halaman "support us" (Patreon/Ko-fi/Sponsors) biasanya cuma menjual **versi cepat dari fitur yang sudah
ada**. Contoh: reverse geocoding Dawarich jalan tanpa donasi lewat **gem `geocoder` di dalam app** dengan
cache (`STORE_GEODATA=true`) — **tidak ada container geocoding terpisah**, jadi jangan cari
Nominatim/Photon. Cek `.env` + folder `app/services/` dulu; baru simpulkan.

### Jangan login ke akun pribadi owner untuk menarik data
Kalau data ada di akun cloud pribadi (Google Timeline, dsb), **jangan** login otomatis dengan kredensial
owner: login berbasis automation berisiko memicu penguncian akun, dan owner bisa pernah menerima
peringatan "aplikasi diblokir karena mengakses informasi sensitif". Jalur benar: owner ekspor sendiri
(atau agent ambil dari storage yang sudah diberi akses), lalu agent mengolah. Sebutkan **alasan
risikonya**, bukan cuma "tidak bisa".
