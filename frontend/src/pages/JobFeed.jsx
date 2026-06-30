import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import FilterPanel from "../components/FilterPanel";
import JobCard from "../components/JobCard";
import toast from "react-hot-toast";

export default function JobFeed({ setSelectedJob, setActivePage }) {
  const [jobs, setJobs] = useState([]);
  const [filteredJobs, setFilteredJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCompany, setSelectedCompany] = useState("");
  const [selectedRecommendation, setSelectedRecommendation] = useState("");
  const [sortBy, setSortBy] = useState("score_desc");

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        // Fetch matches for the default user
        const data = await api.getJobMatches();
        setJobs(data);
        setFilteredJobs(data);
      } catch (err) {
        console.error(err);
        toast.error("Failed to load job matches.");
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, []);

  // Filtering + Sorting Effect
  useEffect(() => {
    let result = [...jobs];

    // 1. Text Search Filter
    if (searchTerm.trim() !== "") {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (j) =>
          j.title.toLowerCase().includes(term) ||
          j.company.toLowerCase().includes(term) ||
          (j.description && j.description.toLowerCase().includes(term)) ||
          (j.matching_skills && j.matching_skills.toLowerCase().includes(term))
      );
    }

    // 2. Company Filter
    if (selectedCompany) {
      result = result.filter((j) => j.company.toLowerCase() === selectedCompany.toLowerCase());
    }

    // 3. Recommendation Filter
    if (selectedRecommendation) {
      result = result.filter(
        (j) => j.recommendation && j.recommendation.toUpperCase() === selectedRecommendation.toUpperCase()
      );
    }

    // 4. Sort
    if (sortBy === "score_desc") {
      result.sort((a, b) => floatValue(b.match_score) - floatValue(a.match_score));
    } else if (sortBy === "score_asc") {
      result.sort((a, b) => floatValue(a.match_score) - floatValue(b.match_score));
    } else if (sortBy === "date_desc") {
      result.sort((a, b) => new Date(b.date_found) - new Date(a.date_found));
    }

    setFilteredJobs(result);
  }, [searchTerm, selectedCompany, selectedRecommendation, sortBy, jobs]);

  const floatValue = (v) => {
    return parseFloat(v) || 0.0;
  };

  // Extract unique companies for filter dropdown
  const companies = Array.from(new Set(jobs.map((j) => j.company)));

  const handleTailorResume = (job) => {
    setSelectedJob(job);
    setActivePage("tools");
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-14 bg-slate-800 rounded-xl animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-72 bg-slate-800 rounded-2xl animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Job Feed</h1>
        <p className="text-gray-400 text-sm mt-1">
          Showing {filteredJobs.length} matches sorted by match percentage.
        </p>
      </div>

      {/* Filter Component */}
      <FilterPanel
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        selectedCompany={selectedCompany}
        setSelectedCompany={setSelectedCompany}
        selectedRecommendation={selectedRecommendation}
        setSelectedRecommendation={setSelectedRecommendation}
        sortBy={sortBy}
        setSortBy={setSortBy}
        companies={companies}
      />

      {/* Listings */}
      {filteredJobs.length === 0 ? (
        <div className="text-center py-20 bg-cardBg border border-slate-800 rounded-2xl shadow-xl">
          <p className="text-gray-400 text-base">No matches found matching the specified filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredJobs.map((job) => (
            <JobCard key={job.job_id} job={job} onTailorResume={handleTailorResume} />
          ))}
        </div>
      )}
    </div>
  );
}
