# Deploying FastAPI to Render — Free Web Service

This guide explains how to deploy the FastAPI backend to Render's free tier. 

---

## 1. Prepare Code Repo
Ensure your code is pushed to a GitHub repository (public or private). Render will link directly to this repo.

---

## 2. Create Render Service
1. Sign up or log in at **[render.com](https://render.com)**.
2. Click **New +** (top-right) and choose **Web Service**.
3. Select **Build and deploy from a Git repository** → click **Next**.
4. Connect your GitHub account and select your job search agent repository.

---

## 3. Configuration Properties

| Property | Value |
|----------|-------|
| **Name** | `ai-job-agent-backend` |
| **Region** | Choose one closest to India (e.g., `Singapore`) |
| **Branch** | `main` (or your active development branch) |
| **Runtime** | `Python3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn api.main_api:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** ($0/month) |

---

## 4. Set Environment Variables
Click the **Advanced** dropdown (or navigate to the **Environment** tab after creation) and add the following keys from your `.env` file:

```dotenv
USE_CLOUD_DB=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
API_KEY=your-chosen-secret-x-api-key
OPENROUTER_API_KEY=your_openrouter_api_key
WHATSAPP_API_TOKEN=your_whatsapp_token
ALERT_WHATSAPP_TO=919792453534
# Add Twilio vars if using Twilio sandbox fallback:
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## 5. Free Tier Constraints
- **Idle Sleep**: Render free instances automatically spin down (sleep) after 15 minutes of inactivity.
- **Cold Starts**: If the instance is asleep, the first HTTP request will trigger a wake-up cycle that takes **30–50 seconds** to complete. Subsequent requests will be instant.
- **Independent Pipeline**: Note that your daily pipeline runs independently inside GitHub Actions; it does not depend on this FastAPI instance being awake to run its daily cron.
