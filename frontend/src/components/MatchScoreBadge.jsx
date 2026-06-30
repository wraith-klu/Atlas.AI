import React from "react";

export default function MatchScoreBadge({ score }) {
  const parsedScore = Math.round(Number(score || 0));

  const getColor = (s) => {
    if (s >= 80) return "text-applyGreen bg-applyGreen/10 border-applyGreen/20";
    if (s >= 50) return "text-stretchYellow bg-stretchYellow/10 border-stretchYellow/20";
    return "text-skipRed bg-skipRed/10 border-skipRed/20";
  };

  return (
    <span
      className={`inline-flex items-center justify-center px-2.5 py-1 text-xs font-black rounded-lg border uppercase tracking-wider ${getColor(
        parsedScore
      )}`}
    >
      🎯 {parsedScore}% Match
    </span>
  );
}
