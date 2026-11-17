---
name: stablecoin-payment-autodetect
description: Use when auto-detecting USDT BSC payments on-chain.
---

# Stablecoin Payment Auto-Detect (USDT BSC/BEP-20)

Pola untuk menerima pembayaran USDT (BSC/BEP-20) dan OTOMATIS mengaktifkan langganan/plan tanpa admin campur tangan. Terbukti di panel Anti-DDoS (payment_monitor.py) — bisa dipakai ulang untuk FastGaji, dashboard, dll.

## Konsep Inti
- Client pilih plan → sistem generate INVOICE dengan **random amount unik** (harga + 0.001–0.999, misal $10 → 10.163) → client transfer PERSIS nominal itu → auto-detect cocokkan amount → PAID.
- Kenapa random amount: BSC **tidak punya memo/tag** (beda XRP/Stellar). 1 wallet untuk semua client → amount unik = cara identifikasi pembayaran. Transfer nominal bulat (10.00) → auto-detect bingung milik siapa.
- Setelah PAID: upgrade plan + expired = **MAX(expired_lama_yang_masih_aktif, hari_ini) + 30 hari** — JANGAN hari_ini+30 (client yang bayar 2x kehilangan sisa hari = komplain!).

## Deteksi On-Chain — WAJIB Alchemy
```python
# ALCHEMY (reliable): alchemy_getAssetTransfers
ALCHEMY_URL = "https://bnb-mainnet.g.alchemy.com/v2/<API_KEY>"
params = {
    "fromBlock": "0x0", "toBlock": "latest",
    "toAddress": WALLET,                 # wallet penerima kita
    "contractAddresses": ["0x55d398326f99059fF775485246999027B3197955"],  # USDT BSC
    "category": ["erc20"], "order": "desc", "maxCount": hex(20),
}
# JSON-RPC: {"jsonrpc":"2.0","method":"alchemy_getAssetTransfers","params":[params],"id":1}
# → result.transfers[].hash / .value / .fromAddress / .metadata.blockTimestamp
```
- Match invoice: `abs(transfer_value - invoice_amount) < 0.001` → mark paid + tx_hash.
- ⚠️ **Public RPC BSC `eth_getLogs` GAGAL untuk USDT** (contract super sibuk → `-32005 limit exceeded` di semua seed: bsc-dataseed, ankr, publicnode). Jangan buang waktu di situ.
- Alchemy key Bang: `alch_KgymfWpXkADRUuQzAtwcD` (ada di `/opt/data/scripts/ambil_transaksi_alchemy.py` dan `fastgaji/fastgaji.py` — BUKAN di .env).

## MULTI-NETWORK (v52+): BEP-20 + ERC-20 + SOLANA + TRC-20
- **EVM address UNIVERSAL**: satu address `0x...` berlaku untuk BSC (BEP-20) DAN ETH (ERC-20) — chain beda, address sama. Tinggal ganti Alchemy URL (`bnb-mainnet` ↔ `eth-mainnet`) + USDT contract (BSC `0x55d398...`, ETH `0xdAC17F958D2ee523a2206206994597C13D831ec7`). Alchemy key SAMA untuk semua chain.
- **SOLANA**: address base58 (bukan 0x). Detect: Alchemy `getSignaturesForAddress` → `getParsedTransaction` (jsonParsed), cari inner instruction type `transfer` dengan `destination == wallet`, amount /10**6. USDT SPL mint `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB`. ⚠️ Kalau Alchemy balas **403 Forbidden** = network Solana BELUM di-enable di dashboard Alchemy (Apps → Networks → + Add → Solana) — bukan bug kode!
- **TRON (TRC-20)**: TronGrid GRATIS tanpa key: `https://api.trongrid.io/v1/accounts/<addr>/transactions/trc20?limit=10` (USDT TRC-20 contract `TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdi`, 6 decimals).
  - ⚠️ **JANGAN pakai `contract_address=` param** — TronGrid balas 400 "A valid contract address is required" (bug aneh mereka). Scan SEMUA trc20 → filter di kode: `t.token_info.address.lower() == USDT.lower()`.
  - ⚠️ **JANGAN pakai `order_by=block_timestamp,desc`** — juga 400. TronGrid default sudah sorted desc; cukup `?limit=N`.
  - Field respons: `transaction_id`, `value` (raw, /10**6), `from`, `to`, `token_info.address`, `block_timestamp`.
- **UI /pay multi-network**: tab pilih jaringan (BEP-20/ERC-20/SOLANA/TRC-20) → JS ganti pane → address + QR + warning sesuai network. Wallet config: `PAYMENT_WALLETS = {bep20, erc20, sol, trc20}` dict. Client pilih network saat bayar; monitor scan SEMUA chain tiap cron → match invoice.
  - ⚠️ **Flask f-string gotcha**: define the network-tab `<script>showNet()</script>` as a variable AND interpolate it into the returned f-string (`{net_js}` before `</body>`) — forgetting the interpolation renders the buttons dead (clicking does nothing). Symptom: tabs render, styling correct, but no switching.

## Fallback Tanpa API Key — Balance Delta
`eth_call balanceOf` (selector `0x70a08231` + address padded 64 hex) ke USDT CA — TIDAK kena limit RPC publik.
- Simpan `last_balance` di state file; delta = balance - last → transfer masuk.
- Match delta ke invoice pending; delta tanpa invoice cocok → notif admin "cek manual".
- Kelemahan: 2 transfer bersamaan dalam 1 interval = delta gabungan (gak match) — ok untuk bisnis kecil.

## QR Code Payment — MATRIKS KOMPATIBILITAS (penting!)
| QR berisi | Trust Wallet | SafePal | OKX/Binance |
|---|---|---|---|
| EIP-681 URI (`ethereum:0x..@56?token=..&uint256=10.227`) | ✅ auto-fill | ❌ paste `0x..@56` → "Invalid address"! | ✅ |
| Trust Wallet deep link (`link.trustwallet.com/send?...`) | ❌ error sendiri! | ❌ | ❌ |
| **ALAMAT DOANG (plain address)** | ✅ | ✅ | ✅ |

→ **Solusi final: 1 QR berisi alamat doang (UNIVERSAL)** + tombol "📋 Salin Alamat" + tombol "📋 Salin Nominal" (biar client paste nominal, gak ketik). Nominal tampil BESAR di atas + warning "WAJIB BEP-20 (BSC), jangan TRC-20 — dana bisa HILANG!" (client sering punya USDT TRC20 juga).

## File & Cron Layout
- `payments.json`: `{invoice_id: {client, plan, amount_usdt, status: pending/paid, tx_hash, paid_at}}`
- `bot_token.txt` di VPS (chmod 600) — jangan hardcode token di script; baca dari file (VPS tidak punya /opt/data/.env Hermes!)
- Cron VPS: `/etc/cron.d/antiddos-payment` → `*/10 * * * * root cd /opt/antiddos && python3 payment_monitor.py >> payment.log 2>&1`

## Pitfalls
- **Expired salah hitung**: mark paid pakai `now()+30` padahal client masih punya sisa 13 hari → kehilangan 14 hari → komplain. Rumus benar: `base = max(parse(expired_lama), now()); new = base + 30`.
- **1 bulan = 30 hari TETAP** (keputusan bisnis Bang) — bukan bulan kalender (Februari 28 hari bikin ribet).
- Token Telegram client: bisa MULTI (list tg_id) — 1 ID = 1 client (unique check saat add, tolak ID yang sudah dipakai user lain).
- Notif ke client saat lock: "bisa login lagi 15 menit" — biar client gak panik & admin gak dibangunin tengah malam.
- Verified end-to-end: transfer 10.227 + 10.918 USDT terdeteksi & auto-aktif dalam ±10 menit.

## Verifikasi
- Generate invoice → cek payments.json status pending.
- `alchemy_getAssetTransfers` manual → transfer Bang muncul dengan amount persis.
- Setelah cron jalan: status paid + expired bertambah + notif Telegram client/admin masuk.
