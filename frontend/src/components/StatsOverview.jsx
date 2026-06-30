import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Briefcase, CheckCircle, AlertTriangle, XOctagon } from "lucide-react";

export default function StatsOverview({ stats, matches = [] }) {
  // Aggregate stats from matching data if stats not fully resolved
  const applyCount = matches.filter((m) => m.recommendation === "APPLY").length;
  const stretchCount = matches.filter((m) => m.recommendation === "STRETCH").length;
  const skipCount = matches.filter((m) => m.recommendation === "SKIP").length;
  const totalScored = matches.length;

  const totalJobs = stats?.total_jobs || totalScored || 0;

  // Chart data
  const companyData = Object.entries(stats?.by_company || {}).map(([name, value]) => ({
    name,
    count: value,
  }));

  const cardData = [
    {
      title: "Total Scraped Jobs",
      value: totalJobs,
      icon: <Briefcase className="w-6 h-6 text-blue-400" />,
      bg: "bg-blue-500/10 border-blue-500/20",
    },
    {
      title: "APPLY Matches",
      value: applyCount,
      icon: <CheckCircle className="w-6 h-6 text-applyGreen" />,
      bg: "bg-applyGreen/10 border-applyGreen/20",
    },
    {
      title: "STRETCH Matches",
      value: stretchCount,
      icon: <AlertTriangle className="w-6 h-6 text-stretchYellow" />,
      bg: "bg-stretchYellow/10 border-stretchYellow/20",
    },
    {
      title: "SKIP Evaluated",
      value: skipCount,
      icon: <XOctagon className="w-6 h-6 text-skipRed" />,
      bg: "bg-skipRed/10 border-skipRed/20",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {cardData.map((card, idx) => (
          <div
            key={idx}
            className={`p-6 rounded-2xl border ${card.bg} flex items-center justify-between shadow-xl backdrop-blur-md`}
          >
            <div>
              <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider">
                {card.title}
              </p>
              <h3 className="text-3xl font-extrabold mt-1 text-white">{card.value}</h3>
            </div>
            <div className="p-3 bg-slate-800/80 rounded-xl">{card.icon}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      {companyData.length > 0 && (
        <div className="bg-cardBg p-6 rounded-2xl border border-slate-800 shadow-2xl">
          <h4 className="text-base font-bold text-white mb-4">Job Distribution by Company</h4>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={companyData}>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    borderColor: "#334155",
                    borderRadius: "12px",
                    color: "#f8fafc",
                  }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
