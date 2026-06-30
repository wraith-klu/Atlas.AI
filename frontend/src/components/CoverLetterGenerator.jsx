import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import { FileText, Copy, Check, Download, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

export default function CoverLetterGenerator({ selectedJob }) {
  const [company, setCompany] = useState("");
  const [title, setTitle] = useState("");
  const [jdSummary, setJdSummary] = useState("");
  const [extraNotes, setExtraNotes] = useState("");
  const [generatedLetter, setGeneratedLetter] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (selectedJob) {
      setCompany(selectedJob.company || "");
      setTitle(selectedJob.title || "");
      setJdSummary(selectedJob.jd_summary || selectedJob.description || "");
    }
  }, [selectedJob]);

  const handleGenerate = async () => {
    if (!company.trim() || !title.trim()) {
      toast.error("Company and role title are required.");
      return;
    }

    setLoading(true);
    setGeneratedLetter("");
    try {
      const result = await api.generateCoverLetter(
        company,
        title,
        jdSummary,
        {},
        extraNotes
      );
      if (typeof result === "string") {
        setGeneratedLetter(result);
      } else if (result?.cover_letter) {
        setGeneratedLetter(result.cover_letter);
      } else {
        setGeneratedLetter(JSON.stringify(result));
      }
      toast.success("Cover letter generated!");
    } catch (err) {
      console.error(err);
      toast.error("Failed to generate cover letter.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedLetter);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([generatedLetter], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cover_letter_${company.replace(/\s+/g, "_")}_${title.replace(/\s+/g, "_")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Downloaded as .txt file!");
  };

  return (
    <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
      <div>
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-violet-400" /> AI Cover Letter Generator
        </h3>
        <p className="text-slate-400 text-xs mt-1">
          Generate a tailored, professional cover letter for any role in seconds.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Inputs */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">Company</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Zscaler"
                className="w-full bg-slate-900 border border-slate-850 px-4 py-2.5 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">Role Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. AI Engineer"
                className="w-full bg-slate-900 border border-slate-850 px-4 py-2.5 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">Job Summary / Description</label>
            <textarea
              rows={5}
              value={jdSummary}
              onChange={(e) => setJdSummary(e.target.value)}
              placeholder="Paste the job description or a brief summary..."
              className="w-full bg-slate-900 border border-slate-850 p-4 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">
              Extra Notes <span className="text-slate-500 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={extraNotes}
              onChange={(e) => setExtraNotes(e.target.value)}
              placeholder='e.g. "Mention my hackathon win and ToxiGuard project"'
              className="w-full bg-slate-900 border border-slate-850 px-4 py-2.5 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500"
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-bold rounded-xl shadow-lg transition duration-150 disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Generating cover letter...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" /> Generate Cover Letter
              </>
            )}
          </button>
        </div>

        {/* Right: Output */}
        <div className="space-y-3">
          <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-2">Generated Cover Letter</label>

          {loading ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 animate-pulse space-y-3 min-h-[300px]">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-4 bg-slate-800 rounded" style={{ width: `${90 - i * 8}%` }}></div>
              ))}
            </div>
          ) : generatedLetter ? (
            <div className="relative">
              <textarea
                rows={14}
                value={generatedLetter}
                onChange={(e) => setGeneratedLetter(e.target.value)}
                className="w-full bg-slate-900 border border-slate-850 p-4 rounded-xl text-sm text-slate-200 leading-relaxed focus:outline-none focus:border-violet-500 resize-none"
              />
              <div className="flex gap-2 mt-3">
                <button
                  onClick={handleCopy}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-bold transition"
                >
                  {copied ? <Check className="w-4 h-4 text-applyGreen" /> : <Copy className="w-4 h-4" />}
                  {copied ? "Copied!" : "Copy"}
                </button>
                <button
                  onClick={handleDownload}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-bold transition"
                >
                  <Download className="w-4 h-4" /> Download .txt
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
              <FileText className="w-8 h-8 text-slate-600 mb-2" />
              <p className="text-sm text-slate-500">Fill in the fields on the left and click Generate.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
