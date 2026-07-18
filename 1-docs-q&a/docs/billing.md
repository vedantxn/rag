# Billing

Acme Cloud bills monthly based on usage.

## Plans

- **Starter** — free tier, limited requests
- **Pro** — pay as you go after free quota
- **Enterprise** — custom contract

## How usage is counted

API requests and Worker run-minutes are metered.
Unused free quota does not roll over to the next month.

## Invoices

Invoices appear under **Settings → Billing** on the 1st of each month.
Download PDF invoices from the same page.

## Failed payments

If a payment fails:

1. Update the card under **Settings → Billing**
2. Click **Retry payment**
3. Services stay active for 3 days, then pause

Error code for a declined card is **E_4022**.
