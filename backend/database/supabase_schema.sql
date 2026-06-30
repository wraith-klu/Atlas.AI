-- database/supabase_schema.sql
-- Database Schema for AI Job Search Agent Cloud Migration (Supabase Postgres)

-- 1. Users table (multi-user capability)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  whatsapp_number TEXT UNIQUE NOT NULL,
  batch INT,
  cgpa FLOAT,
  skills JSONB DEFAULT '[]'::jsonb,
  target_companies JSONB DEFAULT '[]'::jsonb,
  target_locations JSONB DEFAULT '[]'::jsonb,
  target_roles JSONB DEFAULT '[]'::jsonb,
  experience_max INT DEFAULT 1,
  alert_mode TEXT DEFAULT 'digest',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- 2. Jobs table (shared across all users)
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id TEXT UNIQUE NOT NULL,
  company TEXT NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  experience_required TEXT,
  apply_link TEXT NOT NULL,
  description TEXT,
  jd_summary TEXT,
  date_found TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  is_new BOOLEAN DEFAULT TRUE,
  raw_data JSONB DEFAULT '{}'::jsonb
);

-- 3. Job Matches table (associative table linking users to jobs with scores)
CREATE TABLE IF NOT EXISTS job_matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
  match_score FLOAT DEFAULT 0.0,
  match_reason TEXT,
  missing_skills JSONB DEFAULT '[]'::jsonb,
  matching_skills JSONB DEFAULT '[]'::jsonb,
  recommendation TEXT,
  quick_tip TEXT,
  scored_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  UNIQUE(user_id, job_id)
);

-- 4. Alerts Sent table (pre-user notification logging)
CREATE TABLE IF NOT EXISTS alerts_sent (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
  alert_type TEXT DEFAULT 'whatsapp',
  sent_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  UNIQUE(user_id, job_id)
);

-- 5. Scraper Logs table (tracks runs of corporate scrapers)
CREATE TABLE IF NOT EXISTS scrape_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company TEXT NOT NULL,
  status TEXT NOT NULL,
  jobs_found INT DEFAULT 0,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
  error_message TEXT
);

-- 6. Remote Error Logs table (for centralized logging and monitoring)
CREATE TABLE IF NOT EXISTS error_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  level TEXT NOT NULL,
  module TEXT NOT NULL,
  message TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Optimization indexes for rapid lookups and filtering
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_is_new ON jobs(is_new);
CREATE INDEX IF NOT EXISTS idx_matches_user ON job_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_matches_recommendation ON job_matches(recommendation);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts_sent(user_id);
