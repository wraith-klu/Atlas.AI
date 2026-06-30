import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { TrendingUp, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";

const LEARNING_LINKS = {
  docker: "https://docs.docker.com/get-started/",
  kubernetes: "https://kubernetes.io/docs/tutorials/",
  aws: "https://aws.amazon.com/free/",
  azure: "https://learn.microsoft.com/en-us/training/azure/",
  gcp: "https://cloud.google.com/training/free",
  jenkins: "https://www.jenkins.io/doc/tutorials/",
  linux: "https://linuxjourney.com/",
  spark: "https://spark.apache.org/docs/latest/quick-start.html",
  "ci/cd": "https://www.atlassian.com/continuous-delivery",
  typescript: "https://www.typescriptlang.org/docs/",
  "node.js": "https://nodejs.org/en/learn",
  mongodb: "https://university.mongodb.com/",
  redis: "https://redis.io/docs/get-started/",
  go: "https://go.dev/tour/",
  scala: "https://docs.scala-lang.org/getting-started/",
  python: "https://docs.python.org/3/tutorial/",
  react: "https://react.dev/learn",
  sql: "https://sqlbolt.com/",
  pytorch: "https://pytorch.org/tutorials/",
  tensorflow: "https://www.tensorflow.org/tutorials",
};

const COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"];

export default function SkillGapChart() {
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGaps = async () => {
      try {
        const data = await api.getSkillGaps();
        if (Array.isArray(data)) {
          setGaps(data.slice(0, 8));
        }
      } catch (err) {
        console.error(err);
        toast.error("Failed to load skill gap data.");
      } finally {
        setLoading(false);
      }
    };
    fetchGaps();
  }, []);

  const handleBarClick = (entry) => {
    const skillName = entry?.skill || entry?.name || "";
    const key = skillName.toLowerCase();
    const url = LEARNING_LINKS[key] || `https://www.google.com/search?q=learn+${encodeURIComponent(skillName)}+free+course`;
    window.open(url, "_blank");
  };

  if (loading) {
    return (
      <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl animate-pulse">
        <div className="h-6 w-1/3 bg-slate-800 rounded mb-6"></div>
        <div className="h-64 bg-slate-800 rounded-xl"></div>
      </div>
    );
  }

  if (gaps.length === 0) {
    return (
      <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl text-center py-12">
        <TrendingUp className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <p className="text-slate-400 text-sm">No skill gap data available. Run the pipeline first to generate match data.</p>
      </div>
    );
  }

  const chartData = gaps.map((g) => ({
    name: g.skill || g.name,
    count: g.count || g.frequency || 1,
  }));

  return (
    <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
      <div>
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          📊 Skills That Could Unlock More Matches
        </h3>
        <p className="text-slate-400 text-xs mt-1">
          Most frequently missing skills across all your scored jobs. Click a bar to find free learning resources.
        </p>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 10 }}>
            <XAxis type="number" stroke="#64748b" fontSize={12} tickLine={false} />
            <YAxis
              dataKey="name"
              type="category"
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              width={100}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1e293b",
                borderColor: "#334155",
                borderRadius: "12px",
                color: "#f8fafc",
              }}
              formatter={(value) => [`${value} jobs`, "Mentioned in"]}
            />
            <Bar
              dataKey="count"
              radius={[0, 6, 6, 0]}
              barSize={28}
              cursor="pointer"
              onClick={(data) => handleBarClick(data)}
            >
              {chartData.map((_, idx) => (
                <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="text-[11px] text-slate-500 flex items-center gap-1">
        <ExternalLink className="w-3 h-3" /> Click any bar to open a free learning resource for that skill.
      </p>
    </div>
  );
}
