import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import { Save, Settings, Check } from "lucide-react";
import toast from "react-hot-toast";

const COMPANY_OPTIONS = ["IBM", "Infosys", "Genpact", "Delhivery", "Zscaler"];
const LOCATION_OPTIONS = ["Bangalore", "Hyderabad", "Mumbai", "Delhi/NCR", "Pune", "Noida", "Chennai", "Remote"];
const ROLE_OPTIONS = ["Software Engineer", "AI/ML Engineer", "Data Scientist", "Backend Developer", "Full Stack Developer", "DevOps Engineer", "Cloud Engineer"];

export default function Preferences() {
  const [targetCompanies, setTargetCompanies] = useState([]);
  const [targetLocations, setTargetLocations] = useState([]);
  const [targetRoles, setTargetRoles] = useState([]);
  const [experienceMax, setExperienceMax] = useState(1);
  const [alertMode, setAlertMode] = useState("digest");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profile = await api.getUserProfile();
        if (profile) {
          setTargetCompanies(profile.target_companies || []);
          setTargetLocations(profile.target_locations || []);
          setTargetRoles(profile.target_roles || []);
          setExperienceMax(profile.experience_max || 1);
          setAlertMode(profile.alert_mode || "digest");
        }
      } catch (err) {
        console.log("Could not load existing preferences:", err.message);
      } finally {
        setLoaded(true);
      }
    };
    loadProfile();
  }, []);

  const toggleItem = (list, setList, item) => {
    if (list.includes(item)) {
      setList(list.filter((i) => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateUserPreferences(undefined, {
        target_companies: targetCompanies,
        target_locations: targetLocations,
        target_roles: targetRoles,
        experience_max: experienceMax,
        alert_mode: alertMode,
      });
      toast.success("Preferences saved! Changes take effect on next pipeline run.");
    } catch (err) {
      console.error(err);
      toast.error("Failed to save preferences.");
    } finally {
      setSaving(false);
    }
  };

  if (!loaded) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-slate-800 rounded-xl w-1/4"></div>
        <div className="h-96 bg-slate-800 rounded-2xl"></div>
      </div>
    );
  }

  const CheckboxGroup = ({ label, options, selected, setSelected }) => (
    <div>
      <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-3">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const isActive = selected.includes(opt) || selected.includes(opt.toLowerCase());
          return (
            <button
              key={opt}
              onClick={() => toggleItem(selected, setSelected, opt)}
              className={`px-4 py-2 rounded-xl text-sm font-semibold border transition duration-150 ${
                isActive
                  ? "bg-blue-600/20 border-blue-500/40 text-blue-300"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
              }`}
            >
              {isActive && <Check className="w-3.5 h-3.5 inline mr-1" />}
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-8 h-8 text-slate-400" /> Preferences
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Customize your job search targets. Changes apply on the next daily pipeline run.
        </p>
      </div>

      <div className="bg-cardBg border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-8">
        <CheckboxGroup
          label="Target Companies"
          options={COMPANY_OPTIONS}
          selected={targetCompanies}
          setSelected={setTargetCompanies}
        />

        <CheckboxGroup
          label="Preferred Locations"
          options={LOCATION_OPTIONS}
          selected={targetLocations}
          setSelected={setTargetLocations}
        />

        <CheckboxGroup
          label="Target Roles"
          options={ROLE_OPTIONS}
          selected={targetRoles}
          setSelected={setTargetRoles}
        />

        {/* Experience Slider */}
        <div>
          <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-3">
            Max Experience Required: <span className="text-blue-400 text-base">{experienceMax} year{experienceMax !== 1 ? "s" : ""}</span>
          </label>
          <input
            type="range"
            min={0}
            max={5}
            value={experienceMax}
            onChange={(e) => setExperienceMax(Number(e.target.value))}
            className="w-full max-w-md accent-blue-500"
          />
          <div className="flex justify-between text-xs text-slate-500 max-w-md mt-1">
            <span>Fresher</span>
            <span>5 years</span>
          </div>
        </div>

        {/* Alert Mode Toggle */}
        <div>
          <label className="block text-slate-300 text-xs font-bold uppercase tracking-wider mb-3">Alert Mode</label>
          <div className="flex gap-3">
            {["digest", "instant"].map((mode) => (
              <button
                key={mode}
                onClick={() => setAlertMode(mode)}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold border transition ${
                  alertMode === mode
                    ? "bg-blue-600/20 border-blue-500/40 text-blue-300"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                {mode === "digest" ? "📋 Daily Digest (8 AM IST)" : "⚡ Instant Alerts"}
              </button>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center justify-center gap-2 px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold rounded-xl shadow-lg transition duration-150 disabled:opacity-50"
        >
          {saving ? (
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          ) : (
            <Save className="w-5 h-5" />
          )}
          {saving ? "Saving..." : "Save Preferences"}
        </button>
      </div>
    </div>
  );
}
