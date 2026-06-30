# GitHub Repository Secrets Setup Guide

To run the job search agent automatically on GitHub Actions, you must store your secret API keys and credentials as Repository Secrets. This keeps them encrypted and prevents credentials from leaking in public code commits.

---

## Instructions

1. Go to your repository on **[github.com](https://github.com)**.
2. Click on the **Settings** tab (the gear icon on the top tab navigation bar).
3. In the left-hand sidebar, scroll down to **Security** → click on **Secrets and variables** → choose **Actions**.
4. Click the green **New repository secret** button.
5. Add the following secrets one by one:

---

## Required Secrets List

| Secret Name | Description / Source Value |
|-------------|----------------------------|
| `SUPABASE_URL` | Your Supabase Project API URL (starts with `https://`) |
| `SUPABASE_ANON_KEY` | Your Supabase public/anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service_role key (required to bypass DB RLS) |
| `OPENROUTER_API_KEY` | Your OpenRouter LLM API key |
| `WHATSAPP_API_TOKEN` | Your Meta Cloud API Access Token *or* Twilio Sandbox token |
| `WHATSAPP_PHONE_ID` | Your Meta Phone Number ID (leave empty/dummy if using Twilio) |
| `ALERT_WHATSAPP_TO` | Recipient WhatsApp number (e.g. `919792453534`) |
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID (if using Twilio Sandbox) |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token (if using Twilio Sandbox) |
| `TWILIO_WHATSAPP_FROM` | Twilio sandbox sending number (e.g. `whatsapp:+14155238886`) |

---

## Triggering Manually

Once secrets are saved:
1. Go to the **Actions** tab in your GitHub repository.
2. Click on the **Daily Job Search Agent** workflow in the left sidebar list.
3. Click the **Run workflow** dropdown on the right side.
4. Select the branch and click the green **Run workflow** button.
