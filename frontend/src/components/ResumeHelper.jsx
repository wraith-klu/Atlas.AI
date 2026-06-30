import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import { Sparkles, Copy, Check, Info } from "lucide-react";
import toast from "react-hot-toast";

export default function ResumeHelper({ selectedJob }) {
  const [jobDescription, setJobDescription] = useState("");
  const [currentBullets, setCurrentBullets] = useState(
    "- Developed full-stack web applications using React and Node.js.\n" +
    "- Designed database architectures and wrote SQL queries for data aggregation.\n" +
    "- Deployed machine learning models and NLP components to production environments."
  );
  const [tailoredBullets, setTailoredBullets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);

  // Pre-fill JD if a job was selected from Feed
  useEffect(() => {
    if (selectedJob) {
      setJobDescription(
        `Role: ${selectedJob.title}\nCompany: ${selectedJob.company}\n\n${
          selectedJob.description || selectedJob.jd_summary || ""
        }`
      );
    }
  }, [selectedJob]);

  const handleTailor = async () => {
    if (!jobDescription.trim()) {
      toast.error("Please provide a job description.");
      return;
    }
    if (!currentBullets.trim()) {
      toast.error("Please provide your current resume bullet points.");
      return;
    }

    setLoading(true);
    setTailoredBullets([]);
    try {
      const parsedBullets = currentBullets
        .split("\n")
        .map((b) => b.replace(/^[-\*\s•]+/, "").trim())
        .filter((b) => b.length > 0);

      const result = await api.tailorResume(jobDescription, parsedBullets, []);
      if (Array.isArray(result)) {
        setTailoredBullets(result);
        toast.success("Resume bullets tailored successfully!");
      } else {
        throw new Error("Invalid response format from AI backend");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to tailor resume bullets. Verify backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const originalList = currentBullets
    .split("\n")
    .map((b) => b.replace(/^[-\*\s•]+/, "").trim())
    .filter((b) => b.length > 0);

  return (
    <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
      <div>
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" /> AI Resume Tailoring
        </h3>
        <p className="text-slate-400 text-xs mt-1">
          Optimize your resume achievements to highlight keywords and matching skills in the target JD.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Input Fields */}
        <div className="space-y-4">
          <div>
            <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">
              Job Description
            </label>
            <textarea
              rows={6}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the target job description here..."
              className="w-full bg-slate-900 border border-slate-850 p-4 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">
              Your Current Resume Bullet Points (One per line)
            </label>
            <textarea
              rows={6}
              value={currentBullets}
              onChange={(e) => setCurrentBullets(e.target.value)}
              placeholder="- Developed frontend..."
              className="w-full bg-slate-900 border border-slate-850 p-4 rounded-xl text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            onClick={handleTailor}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-bold rounded-xl shadow-lg transition duration-150 disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>Generating tailored bullet points...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" /> Tailor Resume Bullets
              </>
            )}
          </button>
        </div>

        {/* Right Output View */}
        <div className="space-y-4">
          <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">
            Tailored Result Preview
          </label>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 animate-pulse space-y-2">
                  <div className="h-4 bg-slate-800 rounded w-5/6"></div>
                  <div className="h-3 bg-slate-800 rounded w-2/3"></div>
                </div>
              ))}
            </div>
          ) : tailoredBullets.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
              <Info className="w-8 h-8 text-slate-600 mb-2" />
              <p className="text-sm text-slate-500">Provide inputs on the left and click Tailor to see results.</p>
            </div>
          ) : (
            <div className="space-y-4 max-h-[460px] overflow-y-auto pr-2">
              {tailoredBullets.map((bullet, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900 border border-slate-850 p-4 rounded-xl space-y-3 relative group shadow-md"
                >
                  {/* Original Bullet */}
                  {originalList[idx] && (
                    <div className="text-[11px] text-slate-500 border-b border-slate-850 pb-2">
                      <span className="font-extrabold uppercase text-slate-600">Original:</span> "{originalList[idx]}"
                    </div>
                  )}

                  {/* Tailored Bullet */}
                  <div className="text-sm text-slate-200 pr-8 font-medium">
                    • {bullet}
                  </div>

                  {/* Copy Button */}
                  <button
                    onClick={() => handleCopy(bullet, idx)}
                    className="absolute top-3 right-3 p-1.5 bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-white rounded-lg transition"
                  >
                    {copiedIdx === idx ? <Check className="w-4 h-4 text-applyGreen" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
