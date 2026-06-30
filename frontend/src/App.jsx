import React, { useState } from "react";
import Dashboard from "./pages/Dashboard";
import JobFeed from "./pages/JobFeed";
import Tools from "./pages/Tools";
import Preferences from "./pages/Preferences";
import { LayoutDashboard, Briefcase, Sparkles, Settings, Menu, X } from "lucide-react";
import { Toaster } from "react-hot-toast";

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedJob, setSelectedJob] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "jobs", label: "Job Feed", icon: Briefcase },
    { id: "tools", label: "AI Tools", icon: Sparkles },
    { id: "preferences", label: "Preferences", icon: Settings },
  ];

  const renderPage = () => {
    switch (activePage) {
      case "dashboard":
        return <Dashboard setActivePage={setActivePage} setSelectedJob={setSelectedJob} />;
      case "jobs":
        return <JobFeed setActivePage={setActivePage} setSelectedJob={setSelectedJob} />;
      case "tools":
        return <Tools selectedJob={selectedJob} />;
      case "preferences":
        return <Preferences />;
      default:
        return <Dashboard setActivePage={setActivePage} setSelectedJob={setSelectedJob} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col md:flex-row">
      <Toaster position="top-right" toastOptions={{
        style: {
          background: "#1e293b",
          color: "#f8fafc",
          border: "1px solid #334155"
        }
      }} />

      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex flex-col w-64 bg-slate-900 border-r border-slate-850 p-6 space-y-8 shrink-0">
        <div className="flex items-center gap-2 px-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white text-lg">
            A
          </div>
          <span className="font-extrabold text-lg text-white tracking-wider">JOB AGENT</span>
        </div>

        <nav className="flex-1 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActivePage(item.id);
                  if (item.id !== "tools") setSelectedJob(null);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? "bg-blue-600 text-white shadow-md shadow-blue-500/10"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="pt-6 border-t border-slate-800 text-center text-xs text-slate-500">
          AI Job Agent v1.0.0
        </div>
      </aside>

      {/* Mobile Top Header */}
      <header className="md:hidden bg-slate-900 border-b border-slate-850 px-6 py-4 flex items-center justify-between z-50">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white text-base">
            A
          </div>
          <span className="font-extrabold text-md text-white tracking-wider">JOB AGENT</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 text-slate-400 hover:text-white transition"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 top-[60px] bg-slate-950/95 z-40 p-6 flex flex-col space-y-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActivePage(item.id);
                  if (item.id !== "tools") setSelectedJob(null);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-bold transition ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:bg-slate-800"
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-10 overflow-y-auto max-w-7xl mx-auto w-full">
        {renderPage()}
      </main>
    </div>
  );
}
