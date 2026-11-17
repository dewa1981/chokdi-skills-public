---
name: travel-trip-prep
description: "Use when a trip is announced: entry rules, eSIM, reminders."
version: 1.0.0
metadata:
  hermes:
    tags: [travel, visa, esim, reminders, thailand, malaysia, toddler]
    category: productivity
---

# Trip Preparation (outbound travel)

Class of task: the user says "พรุ่งนี้ฉันจะไป …" / announces travel — deliver a
verified entry-rule set, a visa-day deadline, the flags that actually block
boarding, a connectivity plan that preserves OTP, a reminder ladder, and a Thai
.docx checklist. Patty travels as a solo mom with a toddler (Snow ~1.7y), so keep
the tone warm but lead with practical safety rather than reassurance.

## Procedure

1. **Pin the facts that change the answer.** Re-run `date` first, then ask only:
departure date+time, mode (fly vs drive), travellers, estimated length, return
booked or not. "Tomorrow" is relative to when the user *sent* the message — if
messages resume hours later the trip may already be *today*. Re-check the clock
and correct your own earlier framing out loud instead of quietly.

2. **Verify entry rules at the OFFICIAL source, never from blog summaries.**
Search to find the official domain, then state the rule with its window (e.g.
Malaysia MDAC: mandatory for every foreign traveller incl. infants, filed within
3 days before arrival, screenshot the QR). Affiliate/blog pages routinely carry
stale fees, windows and nationality exceptions.

3. **Count visa days from the entry stamp, not from the plan.** Visa-exempt
stays start on the arrival date: state the LAST SAFE EXIT DATE with a 1–2 day
buffer and the overstay penalty regime, and tell the user to read the actual
stamp on arrival and count from it.

4. **No return ticket = boarding risk — flag it unprompted.** Airlines and
immigration may demand proof of onward travel on a visa-free one-way booking.
Advise buying the cheapest throwaway/refundable onward hop before the flight.
This is the highest-value catch in the checklist: raise it the moment the user
says they have no return plan, even if they did not ask.

5. **Toddler flying rules.** Baby milk/food is allowed above the 100 ml liquid
limit but must be declared at the security tray; feed or offer water at takeoff
and landing to prevent ear pain; strollers usually gate-check free; power banks
are carry-on only (≤100 Wh, ≤2 units, never charged on board — Thai CAAT rule);
allow 4h+ for a self-transfer between Don Mueang and Suvarnabhumi.

6. **Connectivity plan that keeps OTP alive.** She must receive SMS OTP from Thai
banks, Shopee affiliate and Bitkub:
- travel eSIM (data-only, no number) in the destination + **keep the home SIM
  installed**; data → eSIM line, calls/SMS pinned to the home line, **Data
  Roaming ON for the travel eSIM** (counter-intuitive, but required), Low Data
  Mode on.
- install the eSIM **before departure while home Wi-Fi is available**; top up the
  home SIM's validity to cover the whole trip so OTP keeps arriving.
- local prepaid SIM is the fallback when data runs out and is usually far cheaper
  per GB than any travel eSIM.

7. **Quote quotas as days-of-use, not GB.** GB ÷ days ≈ MB/day, then price the
user's real habits (per-activity MB table in
`references/malaysia-entry-esim.md`). A content creator who uploads daily *and*
streams cartoons for a toddler burns a 10 GB/30-day plan: recommend 20–30 GB (or
a big local SIM) and tell them to upload only over accommodation Wi-Fi.

8. **Set the reminder ladder** with `cronjob_manage` — deliver='origin',
attach_to_session=true, one-shot ISO timestamps: night before → ~3h before
departure → mid-trip check → visa-deadline warning (~7 days out). Cron prompts
run in a fresh session with no chat context, so each must carry the date,
travellers and exactly what to check.

9. **Deliverable**: a Thai `.docx` checklist/guide under /opt/data/, sent as
`MEDIA:/opt/data/<file>.docx`. Build it with python-docx and set the font on both
`w:ascii` and `w:cs` rFonts (Sarabun) or Thai renders as tofu; numbered steps +
short bullets beat prose.

10. **Audit the ticket the moment the user sends the itinerary** — don't just
congratulate; read every line and check:
- **date vs the last-safe-exit date** (arrival day = day 1).
- **each passenger's DOB against the airline's fare-class age rule.** AirAsia: an
  *infant* must be **under 24 months on the date of the FIRST flight**; past that
  the passenger needs a **child fare with a seat**. Zooming the crop does NOT
  make the month trustworthy — see the low-resolution-date pitfall below. Say the
  date you read out loud, have the user confirm it against the passport, and only
  then compute the age at the travel date; if it is over, tell the user to contact
  the airline **before** the travel day — an airport upgrade costs
  far more or is refused, and even a no-refund/no-change ticket still allows a
  paid fare-class correction. A DOB that does not match the passport must be
  corrected with the airline too. Hand the user a ready-to-send support message
  quoting the booking reference, flight, passenger number and the DOB.
- **baggage per passenger** — an infant's allowance is typically 0 kg, so the
  child's luggage eats the adult allowance; tell them to weigh bags at home.
- **international + infant ⇒ counter check-in** to verify the child's documents
  (online check-in does not finish the job) — so keep the 3-hour airport buffer
  and the id/birth-certificate/house-registration copies in hand.
- a toddler's milk/food passes the 100 ml liquid rule but must be **declared** at
  security, and strollers gate-check free.

## Pitfalls
- **Never conclude a date from a low-resolution screenshot — the Thai month
  abbreviations are visually confusable** (ธ.ค. / ส.ค. / ก.ค. / พ.ค. / มี.ค. differ
  by one glyph). Zooming does not fix it: a 5× LANCZOS crop plus a fresh vision
  read still returned the wrong month, twice, and produced a confident but wrong
  "your ticket is invalid" warning. State the date and the month letter you saw,
  ask the user to confirm from the passport/booking, and only then compute any
  consequence from it. The user's own document knowledge beats OCR, and a
  retracted alarm costs more trust than a 30-second check.
- Ask the handset model before writing dual-SIM/Data-Saver steps — iPhone and
  Android menu paths differ, and wrong steps waste the user's last pre-flight
  hours.
- Never stack a second reminder on a moment an existing cron already covers:
  list jobs first and update rather than duplicate.
- **When the user's own action invalidates a standing reminder, retire it out
  loud.** A reminder telling them to do a border run is wrong the moment they
  book the return flight: say "the earlier advice is cancelled", confirm the job's
  status (one-shots report `completed` and never fire again — nothing to delete),
  and re-point the ladder at the new plan. Stale advice left standing in the chat
  gets acted on.
- For hazard anxiety (quake/flood) give the factual risk picture and what to do
  on arrival; "อย่ากังวล" alone does not land.
- Mark eSIM/SIM prices as "verify at purchase" — they move.
- Confirm the entitlement against the **airline's own nationality list** before
  telling anyone they are visa-free: the carrier decides boarding, and free
  visa-on-arrival rosters are short (UAE gives it to Malaysia/Brunei/Singapore —
  not Indonesia). A nationality freshly added to a government "entry visa for
  nationals of certain countries" scheme gets a **paid, pre-arranged** visa gated
  on holding a residence permit from a listed third country — residence in a
  non-listed country (e.g. a Thai Non-B) never qualifies, even when the
  traveller's own nationality is on the scheme.
- Check what "visa on arrival" actually means before promising airport issuance:
  the same scheme is usually applied for online in advance and pre-approved via
  the airline or the UAE host, so it must be filed *before* flying.
- Treat long-stay asks ("mau tinggal lebih dari sebulan") as an extension problem,
  not a visa problem: pick the longest single-entry visa that fits the trip, then
  count the in-country extension blocks and their max total days — never propose a
  border run as the default answer.
- **The arrival day counts as day 1.** A 30-day visa-exempt stay entered on the
  20th expires on the 18th–19th, not the 20th: quote the last-safe-exit date as
  entry + 29 days. If the user books a flight ON the last day, tell them to clear
  immigration before midnight and to keep the boarding pass plus any airline delay
  notice as evidence if a late departure pushes them past it.
- **Never let an external problem become the reason to overstay.** A leaky rental,
  an unfinished renovation, a repairman's schedule: handle the stay legally and the
  problem on its own track — the fine and the blacklist outlive the problem, and
  the problem can be chased by chat from anywhere. Say this out loud; a stressed
  user is looking for permission to wait.
- **Resolve the entry date from EVIDENCE, not the user's recollection.** The user
  says "kemarin saya ke Penang tanggal 20 September" three weeks after the fact,
  and a long session can span days. Before quoting any deadline, reconcile the
  boarding pass/arrival time with the chat record (query the message DB for the
  user's own "sudah di <kota>" message — recipe in `session-history-recall`
  step 3b) and with the system clock; two independent sources that agree is the
  only basis for a last-safe-exit date.
- **Do not offer the state immigration office as the first fix.** Malaysia's JIM
  extension of a social visit pass is "special consideration" only (illness /
  accident / war, with evidence), applied **in person with the passport, Form
  IMM.55 and a CONFIRMED return/onward ticket** — and those counters close around
  17:30 on weekdays, so an extension attempt on the expiry day itself is almost
  always too late. Willingness to stay longer, a home repair or a sightseeing plan
  gets refused — lead with a border run done 2–4 days before expiry, or simply
  flying home.

## Support Files
- `references/malaysia-entry-esim.md` — Malaysia/Penang entry and stay rules
  (incl. the extension-vs-border-run decision and the Sadao / Bukit Kayu Hitam
  road routes from Penang), eSIM vs local-SIM comparison, network notes, and the
  MB-per-activity data budget table.
- `references/uae-dubai-visa-id.md` — UAE/Dubai entry routes for an Indonesian
  passport: free-VoA rosters, the paid ICP 14/60-day route and who qualifies,
  airline/agency visa channels with fees, in-country extensions, 5-year
  multi-entry, transit visas, overstay fines, and the official source URLs.
