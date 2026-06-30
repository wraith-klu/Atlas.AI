import React from "react";
import MatchScoreBadge from "./MatchScoreBadge";
import { ExternalLink, Award, Sparkles, MapPin, Building } from "lucide-react";

export default function JobCard({ job, onTailorResume }) {
  const companyEmojiMap = {
    ibm: "🔵",
    infosys: "🟢",
    genpact: "🟠",
    delhivery: "📦",
    zscaler: "🛡️",
  };

  const getCompanyEmoji = (co) => {
    return companyEmojiMap[co.toLowerCase().trim()] || "🏢";
  };

  // Safe parse for lists
  const parseList = (raw) => {
    if (!raw) return [];
    if (Array.isArray(raw)) return raw;
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch {
      return [raw];
    }
  };

  const matchingSkills = parseList(job.matching_skills);
  const missingSkills = parseList(job.missing_skills);

  return (
    <div className="bg-cardBg border border-slate-800 p-6 rounded-2xl shadow-xl hover:border-slate-700 transition duration-150 flex flex-col justify-between space-y-6">
      <div className="space-y-4">
        {/* Header section */}
        <div className="flex justify-between items-start gap-4">
          <div className="space-y-1">
            <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-blue-400 uppercase tracking-widest">
              <span role="img" aria-label="company logo">
                {getCompanyEmoji(job.company)}
              </span>
              {job.company}
            </span>
            <h3 className="text-xl font-bold text-white tracking-tight">{job.title}</h3>
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-slate-400 text-xs mt-1">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                {job.location || "Remote / Office"}
              </span>
              {job.experience_required && (
                <span className="flex items-center gap-1">
                  <Building className="w-3.5 h-3.5 text-slate-500" />
                  Exp: {job.experience_required}
                </span>
              )}
            </div>
          </div>

          <MatchScoreBadge score={job.match_score} />
        </div>

        {/* Skills Section */}
        <div className="space-y-2.5 pt-2">
          {matchingSkills.length > 0 && (
            <div className="flex flex-wrap gap-1 items-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 mr-1.5">Matching:</span>
              {matchingSkills.map((skill, idx) => (
                <span
                  key={idx}
                  className="text-[10px] bg-applyGreen/10 text-applyGreen border border-applyGreen/20 px-2 py-0.5 rounded-full font-bold"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}

          {missingSkills.length > 0 && (
            <div className="flex flex-wrap gap-1 items-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 mr-2.5">Missing:</span>
              {missingSkills.map((skill, idx) => (
                <span
                  key={idx}
                  className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700/60 px-2 py-0.5 rounded-full font-semibold"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* AI Summary bullets */}
        {job.jd_summary && (
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 space-y-2">
            <span className="text-xs font-extrabold text-blue-400 flex items-center gap-1 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" /> Summary
            </span>
            <p className="text-xs text-slate-300 leading-relaxed italic">
              "{job.jd_summary}"
            </p>
          </div>
        )}

        {/* AI match Tip */}
        {job.quick_tip && (
          <div className="text-xs text-slate-400 flex items-start gap-1.5">
            <Award className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <p>
              <strong className="text-slate-300">Agent tip:</strong> {job.quick_tip}
            </p>
          </div>
        )}
      </div>

      {/* Footer controls */}
      <div className="pt-4 border-t border-slate-800/80 flex gap-3">
        <a
          href={job.apply_link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold transition duration-150"
        >
          Apply Now <ExternalLink className="w-4 h-4" />
        </a>
        <button
          onClick={() => onTailorResume(job)}
          className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-750 rounded-xl text-sm font-bold transition duration-150"
        >
          Tailor Resume
        </button>
      </div>
    </div>
  );
}
