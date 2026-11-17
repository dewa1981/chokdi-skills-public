# Ringkasan katalog Composio (hasil query REST, bukan tebakan)

Sumber: `GET https://backend.composio.dev/api/v3/toolkits` header `x-user-api-key`, 2 halaman
(`limit=1000` + `next_cursor`). Total saat diukur: **1.742 toolkit, ±83.300 tool**.
Angka bergerak seiring waktu — kalau butuh presisi, query ulang; file ini untuk menjawab cepat
"ada app apa saja" dan memilih kandidat.

## 30 toolkit teratas menurut jumlah tool

microsoft_365 1167 · ambiguous_mcp 945 · infisical 905 · github 883 · datarobot 836 · posthog 686 ·
send_pulse 616 · workday 588 · servicetitan 585 · canvas 573 · highlevel_location 554 ·
zoho_projects 542 · googlesuper 541 · tik_hub 515 · active_campaign 499 · mongodb 496 · zendesk 480 ·
getanyapi 477 · clickfunnels 476 · twilio 452 · deel 436 · tableau 436 · stripe 428 ·
salesforce_data_360 424 · linode 418 · databricks 410 · pipedrive 403 · tiktok_ads 400 ·
vercel 399 · elevenlabs 396

## Yang relevan untuk kerjaan kita (dengan jumlah tool)

- **Scraping / riset**: firecrawl 245, apify 184, exa 64, serpapi 59, perplexityai 28, tavily 5
  (browserbase ada sebagai `browserbase_tool` / `browserbase_mcp`)
- **Google / dokumen**: googlesuper 541, googledrive 92, googlesheets 50, googlecalendar 47,
  googledocs 46, googletasks 16, airtable 26, notion 57
- **Email**: sendgrid 359, outlook 317, gmail 61, resend 113, mailchimp 275, postmark 46, brevo 62
- **Ads (judi/promo)**: tiktok_ads 400, metaads 99, reddit_ads 83, googleads 78, linkedin_ads 28
  (facebook_ads & snapchat_ads TIDAK ada sebagai slug terpisah)
- **Sosial / chat**: slack 165, whatsapp 127, twitter 84, facebook 72, youtube 67, instagram 33,
  linkedin 29, discord 23, telegram 18
- **AI media**: elevenlabs 396, openai 128, heygen 78, replicate 33, runway 22, deepgram 17
  (fal ada sebagai `fal_ai`; stabilityai tidak ada)
- **Deploy / infra**: github 883, linode 418, vercel 399, gitlab 317, render 216, cloudflare 149
- **Database**: mongodb 496, planetscale 245, supabase 230, neon 106, snowflake 16
  (postgres/mysql/redis TIDAK ada sebagai slug terpisah — pakai supabase/neon/planetscale)
- **CRM / support**: zendesk 480, pipedrive 403, hubspot 354, trello 329, asana 247, jira 166,
  clickup 163, intercom 138, monday 122, linear 47
- **Payment**: stripe 428, paypal 81, quickbooks 114, xero 74, plaid 70, coinbase 28, wise 9
  → stripe/paypal **jangan** dipakai untuk judi (risiko ban akun).

## Toolkit yang no-auth (bisa langsung dipakai tanpa link)

Saat diukur lewat CLI: `composio` (17 tool) dan `composio_search` (21 tool). Selain itu semua
butuh `composio link <app>`.

## Catatan

- `composio dev toolkits list` default hanya 30 baris; angka di file ini dari API, bukan dari CLI.
- Field yang berguna per item: `slug`, `name`, `meta.tools_count`, `meta.triggers_count`,
  `meta.is_no_auth`.
