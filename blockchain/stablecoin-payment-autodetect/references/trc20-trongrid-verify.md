# USDT TRC20 On-Chain Verification — TronGrid Public API (no key needed)

Proven 2026-08-13 for auto-verifying TRC20 payments (agent-creator dashboard billing).

## The one endpoint that works
```
GET https://api.trongrid.io/v1/accounts/{ADDRESS}/transactions/trc20?only_to=true&limit=50
```
Lists incoming TRC20 transfers to the address (public, no API key). Each item:
```json
{"transaction_id": "...", "token_info": {"symbol": "USDT", "decimals": 6},
 "from": "...", "to": "...", "value": "200478130", "block_timestamp": 1653761193000}
```
`value` is raw units → divide by 10^decimals (6 for USDT) to get USD amount.

## Pitfall: the endpoint that does NOT work
`GET /v1/transactions/{txid}` does **NOT** return TRC20 transfers — TRC20 moves are internal (TriggerSmartContract) transactions, so txid lookup comes back "Not Found" / empty. Always verify via the account-transactions listing above and match `transaction_id` against the user-submitted TX hash.

## Verify logic (pseudo)
```python
for t in tron_txs(addr):                       # account trc20 list, only_to=true
    if t["transaction_id"] != user_txid: continue
    if t["token_info"]["symbol"] != "USDT": reject
    value = int(t["value"]) / 1e6
    approve if value >= plan_price else keep pending
```
- Also reject outgoing txs (skip entries where `from` == your address — `only_to=true` mostly handles this).
- Custom/negotiated plans: any value ≥ 0 passes, record actual amount.

## Other chains (need API keys — NEXT)
- ERC20: Etherscan API (free key, `Missing/Invalid API Key` without one)
- SOL: Solscan pro-api (401 without token)
