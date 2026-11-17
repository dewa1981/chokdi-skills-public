---
name: ms-access-db-reading
description: "Read MS Access .accdb/.mdb DBs on Linux, encrypted OK."
---

# MS Access (.mdb/.accdb) di Linux — baca & dump

Pakai saat user upload DB Access (mis. `FastBetSalaryDB.accdb` — payroll exe lama,
terenkripsi password) dan isinya harus dibaca/di-import. JANGAN upload ke converter
online (data payroll sensitif).

## Kenali file dulu
- `file x.accdb` → "Microsoft Access Database"; header `00 01 00 00` + `Standard ACE DB`
  = Access 2007+ (.accdb). `Standard Jet DB` = .mdb lama.
- Bytes setelah header tampak acak = DB dienkripsi password → butuh stack Jackcess di bawah.

## Stack yang TERBUKTI (5-Sep-2026, FastBetSalaryDB.accdb 2.4MB terenkripsi)
- **mdbtools TIDAK bisa .accdb** (`mdb-tables` → "Page 2 ... is not a valid table
definition page / File does not appear to be an Access database") — hanya .mdb.
- Yang jalan: **Jackcess (Java)** + jackcess-encrypt + BouncyCastle:
  - `apt-get install -y openjdk-17-jre-headless` (cukup JRE — jalankan `.java`
    source-mode langsung: `java File.java args`, TANPA javac)
  - Jar dari Maven Central ke `/opt/jackcess/`: `jackcess-4.0.5.jar`,
    `jackcess-encrypt-4.0.3.jar` (versi TERAKHIR 4.0.3 — jangan tebak 4.0.5, 404),
    `commons-logging-1.2.jar`, `commons-lang3-3.14.0.jar`, `bcprov-jdk18on-1.78.1.jar`
    (NoClassDefFoundError org/bouncycastle… / org/apache/commons/lang3… = jar kurang).
- Versi Jackcess dari repo1.maven.org: cek `maven-metadata.xml` dulu kalau ragu.

## Cara pakai
```bash
cd /opt/jackcess
java -cp jackcess.jar:jackcess-encrypt.jar:commons-logging.jar:commons-lang3.jar:bcprov.jar \
  AccessDump.java <file.accdb> "<password>" > /tmp/dump.tsv 2>/tmp/err.txt
# output: DB_OK / TABLE<TAB>nama / HEADER<TAB>kolom... / ROW<TAB>nilai...
```
Template dump siap pakai: `scripts/AccessDump.java` (copy ke /opt/jackcess/).

## Pitfalls (semua kena 5-Sep-2026)
- API Jackcess 4: `DatabaseBuilder.open(File)` TIDAK terima password → pakai
  `new DatabaseBuilder(file).setReadOnly(true).setCodecProvider(new CryptCodecProvider(pwd)).open()`
  (`com.healthmarketscience.jackcess.crypt.CryptCodecProvider`, ctor `(String)`).
- `Cursor` di Jackcess 4 BUKAN AutoCloseable — jangan try-with-resources; iterasi:
  `Cursor cur = t.getDefaultCursor(); while (cur.moveToNextRow()) { Row r = cur.getCurrentRow(); }`
  (method `t.getCursor()` TIDAK ADA; `getDefaultCursor()`/`newCursor()` yang ada).
- `javap` cuma ada di JDK, bukan JRE — kalau mau introspeksi API, install
  `openjdk-17-jdk-headless` atau pakai source-mode + print method via reflection.
- Kolom Date ke-dump sebagai ISO (mis. `2013-01-15T02:56:57`), angka ilmiah (`5.0E7`),
  byte[] → hex. Tab/newline di value di-strip (lihat template).
- Value dengan spasi/tab kosong di tengah → saat parse TSV, jangan andalkan jumlah
  kolom tetap; pad `while len(v) < n`. Baris dimulai `ROW\t`.
- Data Access payroll legacy sering MESSY: satu kolom campur nominal USDT & IDR,
  notes berisi campur tx-hash/recipient, tanggal salah tulis. SEBELUM import ke sistem
  lain: cocokkan by txid/chain dulu — chain (BscScan/Alchemy) lebih akurat dari catatan
  exe. Lihat skill `fastgaji-app-dev` untuk contoh banding Access vs histori MariaDB.
