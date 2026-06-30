import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import StatsOverview from "../components/StatsOverview";
import MatchScoreBadge from "../components/MatchScoreBadge";
import { RefreshCw, Play, ArrowRight, Clock, Shield } from "lucide-react";
import toast from "react-hot-toast";

export default function Dashboard({ setActivePage, setSelectedJob }) {
  const [stats, setStats] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, matchesData] = await Promise.all([
        api.getJobStats(),
        api.getJobMatches(),
      ]);
      setStats(statsData);
      setMatches(matchesData);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load dashboard metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    const toastId = toast.loading("Executing scraping + scoring pipeline (approx 45s)...");
    try {
      await api.triggerPipeline();
      toast.success("Job Agent run complete! Scraping & matching updated.", { id: toastId });
      fetchDashboardData();
    } catch (err) {
      console.error(err);
      toast.error("Pipeline trigger failed. Verify backend connectivity and API keys.", { id: toastId });
    } finally {
      setRefreshing(false);
    }
  };

  // Extract top 3 matched jobs
  const topMatches = matches
    .filter((m) => m.recommendation === "APPLY" || m.recommendation === "STRETCH")
    .slice(0, 3);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-slate-800 rounded-xl w-1/4"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-800 rounded-2xl"></div>
          ))}
        </div>
        <div className="h-64 bg-slate-800 rounded-2xl"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            🤖 AI Job Search Agent
          </h1>
          <div className="flex items-center gap-2 text-gray-400 text-sm mt-1">
            <Clock className="w-4 h-4 text-blue-400" />
            <span>
              Last database sync:{" "}
              {stats?.last_scrape_time
                ? new Date(stats.last_scrape_time).toLocaleString("en-IN", { timeZone: "IST" })
                : "No runs logged today"}
            </span>
          </div>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 hover:from-blue-700 hover:to-indigo-700 transition duration-150 disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Refreshing Feed..." : "Refresh Jobs Now"}
        </button>
      </div>

      {/* Stats Cards and Graph */}
      <StatsOverview stats={stats} matches={matches} />

      {/* Top picks preview section */}
      <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            🏆 Top Recommended Matches
          </h3>
          <button
            onClick={() => setActivePage("jobs")}
            className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 text-sm group"
          >
            See Full Feed{" "}
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </button>
        </div>

        {topMatches.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-slate-800 rounded-2xl">
            <p className="text-gray-400">No matching jobs found. Click "Refresh Jobs Now" to trigger a scrape.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {topMatches.map((job) => {
              const matchingSkills = JSON.parse(job.matching_skills || "[]");
              return (
                <div
                  key={job.job_id}
                  className="bg-slate-900 border border-slate-800 p-5 rounded-2xl hover:border-slate-700 transition flex flex-col justify-between"
                >
                  <div className="space-y-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs uppercase font-extrabold text-blue-400">
                          {job.company}
                        </span>
                        <h4 className="font-bold text-white text-base mt-0.5 line-clamp-1">
                          {job.title}
                        </h4>
                      </div>
                      <MatchScoreBadge score={job.match_score} />
                    </div>

                    <div className="text-xs text-gray-400 line-clamp-3">
                      {job.jd_summary || job.description}
                    </div>

                    {matchingSkills.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {matchingSkills.slice(0, 3).map((skill, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] bg-applyGreen/10 text-applyGreen px-2 py-0.5 rounded-full font-semibold"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-800 flex gap-2">
                    <a
                      href={job.apply_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 text-center py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition"
                    >
                      Apply Now
                    </a>
                    <button
                      onClick={() => {
                        setSelectedJob(job);
                        setActivePage("tools");
                      }}
                      className="px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-bold transition"
                    >
                      Tailor
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
