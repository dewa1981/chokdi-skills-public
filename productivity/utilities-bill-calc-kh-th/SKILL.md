---
name: utilities-bill-calc-kh-th
description: Use when hitung/bayar tagihan listrik Kamboja (Poipet).
---

# Hitung & Bayar Tagihan Listrik Kamboja / Thailand

Dipakai kalau Bang kirim foto tagihan listrik (biasanya Poipet/Kamboja) atau tanya "per kWh berapa", tarif rumah Kamboja vs Thailand, atau cara bayar. Lihat juga skill `xlsx` untuk bikin file Excel-nya.

## 1. Alur kerja
1. Baca tagihan dengan `vision_analyze` (angka Khmer sering terpisah: `4980-A 88 105 40 680 7301 496,400 ៛` = box, reading, faktor, **kWh**, tarif, total).
2. Cek silang: `kWh x tarif == TOTAL DUE`. Kalau tidak pas, tarifnya salah baca.
3. Ambil kurs live (`https://open.er-api.com/v6/latest/USD` → KHR & THB), jangan pakai kurs hafalan.
4. Hitung dengan rumus tier (pola MIN/MAX, lihat §3), lalu bandingkan vs Thailand.
5. Bikin Excel berumus (bukan angka mati) supaya Bang bisa ganti kWh/kurs sendiri.

## 2. Tarif referensi (dicek Okt 2026)
**Kamboja — rumah (EAC/EDC, progresif):** 1–10 kWh = 380 ៛ · 11–50 = 480 ៛ · 51–200 = 610 ៛ · >200 = 730 ៛ /kWh.
Bisnis/industri flat: komersial MV 540 ៛ · 22 kV 636 ៛ · industri 22 kV 440 ៛.

**Thailand — rumah (PEA/MEA, tarif mulai tagihan Sep 2026, mosi ERC 5 Agu 2026):**
- Tipe 1.1.2 (>150 unit/bln): 1–200 = 3,0000 · 201–400 = **4,1584** · 401+ = **4,3583** ฿/unit; service 24,62 ฿
- Tipe 1.1.1 (≤150 unit): 1–15 = 2,3488 · 16–25 = 2,9882 · 26–200 = 3,0000 · 201–400 = 4,1584 · 401+ = 4,3583; service 8,19 ฿
- Semua: **+ Ft 0,1623 ฿/unit (Sep–Des 2569) + VAT 7%**. "4 baht" yang Bang ingat = blok 201–400.

**Konteks Bang:** meter Poipet = bisnis (TF160kVA, 3 fasa, faktor 40) dari **ABC Electricity / ANCO BROTHERS**, tarif 730 ៛ flat → ≈6,05 ฿/kWh, ±40% lebih mahal dari tarif rumah Thailand (±4,4 ฿/kWh efektif). Akun 0101-042729, box 4980-A, invoice CINV26-330673.

## 3. Rumus tier (pakai di sel Excel)
```
Kamboja EDC : =MIN(A6,10)*380+MAX(0,MIN(A6,50)-10)*480+MAX(0,MIN(A6,200)-50)*610+MAX(0,A6-200)*730
Thailand 1.1.2: =(MIN(A6,200)*3+MAX(0,MIN(A6,400)-200)*4.1584+MAX(0,A6-400)*4.3583+A6*0.1623+24.62)*1.07
```
Kirim formula hidup (number_format `#,##0" ៛"`, `#,##0.00" ฿"`), sheet: Ringkasan · Tarif Kamboja · Tarif Thailand · Simulasi Banding · Sumber.

## 4. Bayar tagihan Poipet
- Tagihan ABC sendiri mencantumkan kanal: **ABA, Wing, ACLEDA**, app **Quick Wallet / Wing App / ACLEDA App** (tanpa QR; ada barcode 1D atas-bawah).
- ABA Mobile: Payments → Utilities → Electricity → **EDC**, cabang **Banteay Meanchey** (Poipet), atau scan barcode / input nomor pelanggan. Gratis.
- **PITFALL:** daftar biller listrik ABA = **EDC saja**; ABC/ANCO (lisensi swasta) belum tentu ada. Kalau tidak muncul → ACLEDA Mobile → Electricity → **"Private company"**, Wing App, Quick Wallet, atau bayar tunai di kantor ABC Poipet (Sen–Jum 07:00–15:30, tel 092 838 788 / 077 784 544). Tagihan tidak mencetak nomor rekening: minta rekening perusahaan via kantor kalau mau transfer.
- Jatuh tempo lewat → bunga + biaya tambahan. Ingatkan Bang cek status "paid" sebelum bayar ulang di kanal lain.

## 5. Artefak & pitfall
- Builder: `/opt/data/cache/scratch/build_listrik_xlsx.py` (openpyxl; helper `put()` — pastikan panjang `fmts` = `vals`, kalau tidak: IndexError).
- Hasil kirim ke Bang: `/opt/data/reports/tarif-listrik-kamboja-vs-thailand-2026-10-07.xlsx`.
- **LibreOffice/`soffice` TIDAK terpasang di host ini** → `xlsx_recalc.py` gagal, formula tidak bisa dimaterialisasi. Verifikasi = dump formula pakai openpyxl (`if str(c.value).startswith('='): print(c.coordinate, c.value)`), hitung ulang ekspresi sama di Python, dan pastikan tiap referensi sel menunjuk sel yang benar (mis. `B12=B10*B11`, `$B$6` = kurs THB→KHR).
