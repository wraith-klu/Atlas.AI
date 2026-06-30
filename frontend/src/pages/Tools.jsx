import React from "react";
import ResumeHelper from "../components/ResumeHelper";
import CoverLetterGenerator from "../components/CoverLetterGenerator";
import SkillGapChart from "../components/SkillGapChart";

export default function Tools({ selectedJob }) {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">AI Tools</h1>
        <p className="text-gray-400 text-sm mt-1">
          Use AI-powered helpers to tailor your resume, generate cover letters, and identify skill gaps.
        </p>
      </div>

      <ResumeHelper selectedJob={selectedJob} />
      <CoverLetterGenerator selectedJob={selectedJob} />
      <SkillGapChart />
    </div>
  );
}
