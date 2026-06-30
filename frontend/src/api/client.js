import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const DEFAULT_USER_ID = import.meta.env.VITE_DEFAULT_USER_ID || "00000000-0000-0000-0000-000000000000";
const PIPELINE_API_KEY = import.meta.env.VITE_PIPELINE_API_KEY || "super-secret-key-123";

const client = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  // Fetch latest jobs
  getLatestJobs: async (limit = 20) => {
    const response = await client.get(`/jobs/latest?limit=${limit}`);
    return response.data;
  },

  // Fetch evaluated job matches for user
  getJobMatches: async (userId = DEFAULT_USER_ID, recommendation = "") => {
    const url = `/jobs/matches/${userId}${recommendation ? `?recommendation=${recommendation}` : ""}`;
    const response = await client.get(url);
    return response.data;
  },

  // Get job aggregation statistics
  getJobStats: async () => {
    const response = await client.get("/jobs/stats");
    return response.data;
  },

  // Get user profile details
  getUserProfile: async (userId = DEFAULT_USER_ID) => {
    const response = await client.get(`/users/{user_id}/profile`.replace("{user_id}", userId));
    return response.data;
  },

  // Update user preferences
  updateUserPreferences: async (userId = DEFAULT_USER_ID, data = {}) => {
    const response = await client.put(`/users/{user_id}/profile`.replace("{user_id}", userId), data);
    return response.data;
  },

  // Register new user profile
  registerUser: async (userData = {}) => {
    const response = await client.post("/users/register", userData);
    return response.data;
  },

  // Trigger scraper and match pipeline manually (requires Auth API key)
  triggerPipeline: async () => {
    const response = await client.post("/jobs/run-pipeline", {}, {
      headers: {
        "X-API-Key": PIPELINE_API_KEY,
      },
    });
    return response.data;
  },

  // Get alert history logs for user
  getAlertHistory: async (userId = DEFAULT_USER_ID, days = 7) => {
    const response = await client.get(`/alerts/history/${userId}?days=${days}`);
    return response.data;
  },

  // NEW Phase 5 Endpoints (AI Tools)
  tailorResume: async (jobDescription, currentBullets, userSkills = []) => {
    const response = await client.post("/tools/tailor-resume", {
      job_description: jobDescription,
      current_bullets: currentBullets,
      user_skills: userSkills,
    });
    return response.data;
  },

  generateCoverLetter: async (company, title, jdSummary, userProfile = {}, extraNotes = "") => {
    const response = await client.post("/tools/generate-cover-letter", {
      company,
      title,
      jd_summary: jdSummary,
      user_profile: userProfile,
      extra_notes: extraNotes,
    });
    return response.data;
  },

  getSkillGaps: async () => {
    const response = await client.get("/tools/skill-gaps");
    return response.data;
  },
};

export default client;
