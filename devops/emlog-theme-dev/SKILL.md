---
name: emlog-theme-dev
description: Use when building or fixing Emlog themes and posts.
---

# Emlog (Pro) theme dev & content seeding

Emlog Pro (1Panel, `emlog/emlog:pro-latest-php*-nginx`) — bikin/poles tema + isi artikel langsung via DB.
Teruji di `1panel-142` / `emlog142.sayasuka99.com` (21-Okt-2026) → tema "TBP" dark-luxury + 6 artikel.

## 1. Struktur path (1Panel)
```
/opt/1panel/apps/emlog/<app>/data/          # = EMLOG_ROOT (= /app di container)
  config.php                                # DB creds (host 'mysql', user emlog_X, DB emlog_Y)
  content/templates/<tema>/                 # index.php, log_list.php, echo_log.php, header.php, footer.php
  content/cache/                            # WAJIB dihapus setelah ubah config/tema/DB
```
Container: `docker exec <emlog-ct> php -l /app/content/templates/<tema>/x.php` untuk lint.

## 2. Template mana dipanggil kapan (INI PENENTU, jangan tebak)
Emlog modern TIDAK memakai `index.php` untuk home. Controller `Log_Controller::index()`:
```php
include View::getView('header');
include View::getView('log_list');   // <-- HOME = log_list.php, BUKAN index.php
```
Single post → `echo_log.php`. Jadi untuk redesign home, **edit `log_list.php`**.

- `header.php` WAJIB ada & berisi DOCTYPE+head (dipakai semua halaman, dan `Template_Model::getTemplates()`
  menganggap folder tanpa `header.php` sebagai tema tidak valid → tidak muncul di admin).
  Minimal isi komentar metadata: `Template Name:` / `Description:` / `Version:`.
- Nav/footer: tulis penuh di `log_list.php` & `echo_log.php` masing-masing.

## 3. Variabel tema yang benar
| Variabel | Isi | Catatan |
|---|---|---|
| `Option::get('blogname')` | nama situs | **pakai ini**; `$blogtitle` KOSONG di `echo_log.php` → `<title>Judul - </title>` |
| `$log_title`, `$date`, `$views`, `$log_content` | post | hanya di echo_log |
| `$logs` | array artikel home | tersedia di `log_list.php` |
| `TEMPLATE_URL` | URL tema | `https://host/content/templates/<tema>` |
| `BLOG_URL`, `Url::log($gid)` | URL | — |

## 4. Seed artikel via MySQL langsung (paling cepat, tanpa admin)
```bash
MYSQL() { docker exec -i 1Panel-mysql-fQpC sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" emlog_sdek3r' 2>/dev/null; }
```
Kolom `emlog_blog` wajib: `gid,title,date,content,excerpt,cover,alias,author,sortid,type`
+ flag: `hide='n' checked='y' type='blog' allow_remark='y'` (kalau `checked='n'` artikel TIDAK tampil).
`date` = `UNIX_TIMESTAMP()` (detik). `author` = uid 1.

Kategori `emlog_sort` kolomnya: `sid,sortname,alias,taxis,pid,description,kw,title,template,sortimg,page_count,allow_user_post`
— **BUKAN `sortorder`** (error 1054 kalau salah). `taxis` = urutan.

### ⚠️ Kolom `tags` di emlog_blog harus BERISI TID ANGKA, bukan nama tag
Isi `tags='prediksi bola|tips'` → artikel CRASH:
```
SELECT `tid`,`tagname` FROM `emlog_tag` WHERE `tid` IN (prediksi bola|tips)  → error 1064
```
Untuk konten bulk paling aman: `tags=''` (kosong). Kalau mau tag nyata: buat baris di `emlog_tag` dulu, lalu isi `tags` dengan `tid` dipisah koma.

## 5. 🔴 Encoding UTF-8 (mojibake) — diagnosa & fix TERUJI
**Gejala:** halaman menampilkan `â€"`, `âš ï¸`, `â†'`, `âœ…` padahal DB `utf8mb4` dan header `charset=UTF-8`.

**Diagnosa (jangan percaya mata, cek byte):**
```bash
curl -s "http://127.0.0.1:9080/post/<alias>" | grep -o "Kata[^<]*" | head -1 | hexdump -C | head -3
# c3 a2 e2 82 ac e2 80 9d = "â€" (double-encoded em dash)
```
Bandingkan HEX dari DB (`SELECT gid,HEX(content) ...`) — kalau byte identik dengan HTTP, mojibake TERSIMPAN di DB.

**Fix benar:** baca HEX → `raw.decode('utf-8')` → `.encode('cp1252')` → `.decode('utf-8')`:
```python
s = bytes.fromhex(hex_from_db).decode('utf-8','replace')
try:    good = s.encode('cp1252').decode('utf-8')
except: good = s
```
Tulis balik lewat **file SQL + `docker cp` + `mysql < file`** (hindari quoting shell/heredoc).

**Sisa emoji** (`âŒ`, `âœ…`, `âš ï¸`) tidak bisa di-encode cp1252 → fallback map eksplisit:
`{'âŒ':'❌','âœ…':'✅','âš ï¸':'⚠️','â†’':'→','â€"':'—','â€“':'–','â€™':'’'}`
+ regex terakhir `re.sub(r'[âÃ][\u0080-\u00bf\u2018-\u2122]+','',s)` untuk membuang sisa.
Verifikasi: `grep -coE "[âÃ][^a-zA-Z0-9 ]"` per-halaman harus **0**.

⚠️ Nulis konten lewat shell heredoc (SSH) bisa MEMASUKKAN mojibake dari pipe → **cek byte setelah seed**.

## 6. Cache clearing (WAJIB setelah tiap perubahan)
```bash
docker exec <emlog-ct> sh -c 'rm -f /app/content/cache/*.php'
chown -R www-data:www-data /opt/1panel/apps/emlog/<app>/data/content/templates/<tema>; chmod -R 755 ...
```
Tanpa ini Emlog menyajikan `options.php`/`logalias.php` lama → tema baru tidak kelihatan.

## 7. Verifikasi visual (server tanpa browser)
Screenshot headless via SSH tunnel dari staging (URL `127.0.0.1:9080` tidak bisa diakses browser_exec — private address):
```bash
ssh -N -L 19080:127.0.0.1:9080 root@<server> &
CHROME=/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome
$CHROME --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=430,7200 --screenshot=/tmp/mobile.png --virtual-time-budget=10000 http://127.0.0.1:19080/
```
`--window-size` tinggi (7000-9000) untuk full-page; kalau kurang, footer tampak "hilang" di screenshot padahal ada di HTML — verifikasi `curl | grep -c footer` dulu sebelum menyimpulkan rusak.

## 8. Checklist redesign tema blog/judi
- [ ] `header.php` ada + metadata template
- [ ] `log_list.php` = home (hero + brand CTA + daftar artikel)
- [ ] `echo_log.php` = detail (title/date/views/content + CTA box + brand mini)
- [ ] CSS inline (tanpa build step), mobile-first, `overflow-x:hidden` di body
- [ ] CTA brand pakai shortlink `https://tomat.jagungbaru.com/banner/<kode>` (s161/fb99/vip/sb99/hk99/nx)
- [ ] Backup tema lama (`<tema>.bak-<stamp>`) + hapus artikel sampah sebelum seed
- [ ] Cek mojibake byte-level setelah seed
- [ ] Screenshot mobile 430px + desktop 1440px, review per-zona
