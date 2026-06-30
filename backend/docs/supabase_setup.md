# Supabase Setup Guide — AI Job Agent

This guide outlines how to set up a free Supabase cloud database to persist jobs, users, matches, alerts, and scrape logs.

---

## 1. Sign Up & Create Project
1. Go to **[supabase.com](https://supabase.com)** and sign up or sign in.
2. Click **New Project** and select your organization.
3. Configure your project:
   - **Name**: `AI Job Agent`
   - **Database Password**: *Save this password securely*
   - **Region**: Choose a region close to your location (e.g., `Singapore` or `Mumbai` if available, to minimize latency to India).
   - **Pricing Plan**: Select the **Free Tier**.
4. Click **Create new project** and wait for the database hosting to provision (typically takes 1-2 minutes).

---

## 2. Retrieve API Credentials
1. Once provisioning completes, go to **Project Settings** (gear icon in the bottom-left sidebar).
2. Click on the **API** tab under the Settings menu.
3. Locate and copy the following credentials:
   - **Project URL** (under URL)
   - **anon/public API key** (this is safe to client-expose)
   - **service_role key** (this key bypasses Row Level Security. Keep it private. We will use this in the backend/runners to write data).

---

## 3. Configure Local Environment File
Add the copied keys to your local `.env` file in the root of the project:

```dotenv
# ==== Cloud DB Configuration ====
USE_CLOUD_DB=true
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_public_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

---

## 4. Run Migration Schema Script
1. In the Supabase left sidebar, click on **SQL Editor** (the terminal console icon).
2. Click **New query** (or choose the `Quickstart` script templates).
3. Paste the contents of `database/supabase_schema.sql` into the SQL editor window.
4. Click the **Run** button (or press `Ctrl + Enter` / `Cmd + Enter`).
5. Verify that all tables (`users`, `jobs`, `job_matches`, `alerts_sent`, `scrape_logs`, `error_logs`) and indexes are created successfully.
