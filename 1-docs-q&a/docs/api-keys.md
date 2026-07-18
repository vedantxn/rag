# API Keys

API keys authenticate requests to Acme Cloud.

## Create a key

1. Open **Settings → API Keys**
2. Click **Create key**
3. Copy the key once — it is shown only at creation time

Keys look like: `acme_live_xxxxxxxx`

## Reset or rotate a key

1. Open **Settings → API Keys**
2. Select the key
3. Click **Rotate**
4. Update your app with the new key
5. Revoke the old key after you confirm the new one works

Rotating a key does not change your project ID.

## Revoke a key

Revoked keys stop working immediately. This cannot be undone.
Create a new key if you still need access.

## Permissions

- `read` — list resources
- `write` — create and update resources
- `admin` — manage keys and billing links
