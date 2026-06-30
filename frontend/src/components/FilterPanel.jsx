import React from "react";
import { Search } from "lucide-react";

export default function FilterPanel({
  searchTerm,
  setSearchTerm,
  selectedCompany,
  setSelectedCompany,
  selectedRecommendation,
  setSelectedRecommendation,
  sortBy,
  setSortBy,
  companies = [],
}) {
  return (
    <div className="bg-cardBg border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col md:flex-row gap-4 items-center justify-between">
      {/* Search Input */}
      <div className="relative w-full md:w-1/3">
        <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="w-5 h-5 text-gray-400" />
        </span>
        <input
          type="text"
          placeholder="Search by role, skill, description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full bg-slate-900 border border-slate-850 pl-10 pr-4 py-2.5 rounded-xl text-sm text-slate-100 placeholder-gray-400 focus:outline-none focus:border-blue-500 transition duration-150"
        />
      </div>

      {/* Select Filters */}
      <div className="flex flex-wrap md:flex-nowrap gap-3 w-full md:w-auto items-center">
        {/* Company Filter */}
        <select
          value={selectedCompany}
          onChange={(e) => setSelectedCompany(e.target.value)}
          className="bg-slate-900 border border-slate-850 px-4 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-blue-500 cursor-pointer"
        >
          <option value="">All Companies</option>
          {companies.map((co) => (
            <option key={co} value={co}>
              {co}
            </option>
          ))}
        </select>

        {/* Recommendation Filter */}
        <select
          value={selectedRecommendation}
          onChange={(e) => setSelectedRecommendation(e.target.value)}
          className="bg-slate-900 border border-slate-850 px-4 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-blue-500 cursor-pointer"
        >
          <option value="">All Recommendations</option>
          <option value="APPLY">✅ APPLY</option>
          <option value="STRETCH">⚠️ STRETCH</option>
          <option value="SKIP">❌ SKIP</option>
        </select>

        {/* Sorting Dropdown */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="bg-slate-900 border border-slate-850 px-4 py-2.5 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-blue-500 cursor-pointer"
        >
          <option value="score_desc">Match Score: High to Low</option>
          <option value="score_asc">Match Score: Low to High</option>
          <option value="date_desc">Found Date: Newest First</option>
        </select>
      </div>
    </div>
  );
}
