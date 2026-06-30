# Gmail API Setup Guide — AI Job Agent

This guide walks you through setting up free Gmail API access so the
agent can send email alerts from your own Gmail account.

**Time required:** ~10 minutes (one-time setup)

---

## Step 1 — Create a Google Cloud Project

1. Go to **[Google Cloud Console](https://console.cloud.google.com)**
2. Click the project dropdown (top-left) → **New Project**
3. Name it: `AI Job Agent` (or anything you like)
4. Click **Create** and wait a few seconds

---

## Step 2 — Enable the Gmail API

1. In the Cloud Console, go to **APIs & Services → Library**
   (or search "Gmail API" in the top search bar)
2. Click **Gmail API**
3. Click the blue **Enable** button
4. Wait until the dashboard shows "Gmail API — Enabled ✅"

---

## Step 3 — Configure OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** user type → click **Create**
3. Fill in:
   - App name: `AI Job Agent`
   - User support email: your Gmail address
   - Developer contact email: your Gmail address
4. Click **Save and Continue** through the remaining steps
   (Scopes, Test Users — you can skip adding test users for now)
5. Click **Back to Dashboard**

---

## Step 4 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: `AI Job Agent Desktop`
5. Click **Create**
6. A dialog will show your Client ID and Client Secret
7. Click **Download JSON** (the download button / icon)
8. Save the downloaded file as:
   ```
   config/gmail_credentials.json
   ```
   (inside your project's `config/` folder)

---

## Step 5 — First-Run Authorization

The very first time you run Phase 3 (or the test script), a
browser window will open asking you to sign in with your
Google account and grant the app permission to send email.

1. Sign in with `2300039cseh2@gmail.com`
2. Click **Continue** (you may see "Google hasn't verified this app"
   — click **Advanced → Go to AI Job Agent (unsafe)** — this is
   safe because YOU created the app)
3. Grant "Send email on your behalf" permission
4. The browser will show "Authentication successful" and close

A `config/gmail_token.json` file is automatically created. This
token refreshes itself, so you won't need to repeat this step
unless you revoke access.

---

## Step 6 — Verify

Run the test:
```bash
python -m tests.test_phase3
```

If everything is set up correctly, you'll receive a test email
at `2300039cseh2@gmail.com`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Access Denied" error | Make sure you enabled the Gmail API (Step 2) |
| Token expired | Delete `config/gmail_token.json` and re-run — it will re-authorize |
| "App not verified" warning | Click Advanced → Go to AI Job Agent (unsafe) |
| `FileNotFoundError: gmail_credentials.json` | Download the OAuth JSON again (Step 4) and place it in `config/` |

---

## Security Notes

- **Never commit** `gmail_credentials.json` or `gmail_token.json`
  to Git — they are already in `.gitignore`.
- The app only requests `gmail.send` scope (cannot read your inbox).
- You can revoke access anytime at
  [myaccount.google.com/permissions](https://myaccount.google.com/permissions).
