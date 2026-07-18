# Error Codes

Common Acme Cloud error codes.

## E_4010 — Invalid API key

The key is missing, malformed, or revoked.
Fix: create or rotate a key under Settings → API Keys.

## E_4022 — Payment declined

The card on file was declined.
Fix: update billing details and retry payment.
See Billing docs for the failed-payment steps.

## E_4290 — Rate limit

Too many requests in a short window.
Fix: retry with backoff, or upgrade plan.

## E_5001 — Internal error

Something failed on Acme's side.
Fix: retry later; contact support if it persists.
