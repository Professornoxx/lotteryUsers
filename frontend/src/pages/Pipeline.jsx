import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../utils/api";

const STEPS = [
  {
    id: 1, icon: "🔗", title: "External APIs",
    desc: "Deposit, Withdrawal & Wallet links",
    color: "from-blue-600 to-blue-800", border: "border-blue-500",
    items: ["Deposit Link", "Withdrawal Link", "Wallet Details", "Package ID=10"],
  },
  {
    id: 2, icon: "⚙️", title: "FastAPI Backend",
    desc: "Fetch, parse & upsert every 20 min",
    color: "from-purple-600 to-purple-800", border: "border-purple-500",
    items: ["Validate & clean data", "ON CONFLICT upsert", "Auto-scheduler 20 min", "Render.com hosting"],
  },
  {
    id: 3, icon: "🗄️", title: "Supabase Database",
    desc: "PostgreSQL — all tables live here",
    color: "from-green-600 to-green-800", border: "border-green-500",
    items: ["users (55,040 rows)", "user_financials", "deposits", "withdrawals"],
  },
  {
    id: 4, icon: "📊", title: "Dashboard",
    desc: "React frontend — auto-refresh 20 min",
    color: "from-yellow-600 to-yellow-800", border: "border-yellow-500",
    items: ["KPI Cards", "Charts & Reports", "User CRUD", "Export Excel"],
  },
];

const LINKS = [
  { label: "Dashboard", url: "https://projectzerofive.vercel.app", icon: "📊", color: "bg-yellow-600 hover:bg-yellow-500" },
  { label: "Backend API", url: "https://project05-babt.onrender.com/docs", icon: "⚙️", color: "bg-purple-600 hover:bg-purple-500" },
  { label: "Supabase DB", url: "https://supabase.com/dashboard", icon: "🗄️", color: "bg-green-600 hover:bg-green-500" },
  { label: "GitHub Repo", url: "https://github.com/Professornoxx/lotteryUsers", icon: "💻", color: "bg-gray-600 hover:bg-gray-500" },
];

export default function Pipeline() {
  const [token, setToken] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const { data: summary } = useQuery({
    queryKey: ["pipeline-summary"],
    queryFn: () => api.get("/dashboard/summary/").then(r => r.data),
    refetchInterval: 60000,
  });

  const { data: pipelineStatus, refetch: refetchStatus } = useQuery({
    queryKey: ["pipeline-status"],
    queryFn: () => api.get("/pipeline/status/").then(r => r.data),
    refetchInterval: 30000,
  });

  async function saveToken(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/pipeline/token/", { bearer_token: token });
      setSaved(true);
      setToken("");
      setTimeout(() => { setSaved(false); refetchStatus(); }, 3000);
    } catch {
      setSaved(false);
    }
    setSaving(false);
  }

  async function manualSync() {
    try {
      await api.post("/pipeline/sync/");
      setTimeout(refetchStatus, 5000);
    } catch {}
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-1">Pipeline Management</h1>
          <p className="text-slate-400">Data flow: External APIs → Backend → Database → Dashboard</p>
        </div>

        {/* DB Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Users", value: summary?.total_users ?? "—" },
            { label: "Total Deposits", value: summary?.total_deposits ? `₹${Number(summary.total_deposits).toLocaleString()}` : "—" },
            { label: "Total Withdrawals", value: summary?.total_withdrawals ? `₹${Number(summary.total_withdrawals).toLocaleString()}` : "—" },
            { label: "Total Balance", value: summary?.total_balance ? `₹${Number(summary.total_balance).toLocaleString()}` : "—" },
          ].map(s => (
            <div key={s.label} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
              <p className="text-slate-400 text-xs mb-1">{s.label}</p>
              <p className="text-white text-xl font-bold">{s.value}</p>
            </div>
          ))}
        </div>

        {/* Pipeline Steps */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-300 mb-4">Pipeline Steps</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {STEPS.map((step, idx) => (
              <div key={step.id} className="relative">
                <div className={`bg-slate-800 border ${step.border} rounded-xl p-5 h-full`}>
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${step.color} flex items-center justify-center text-xl mb-3`}>
                    {step.icon}
                  </div>
                  <div className="text-xs text-slate-500 font-mono mb-1">STEP {step.id}</div>
                  <h3 className="text-white font-semibold mb-1">{step.title}</h3>
                  <p className="text-slate-400 text-xs mb-3">{step.desc}</p>
                  <ul className="space-y-1">
                    {step.items.map(item => (
                      <li key={item} className="text-slate-300 text-xs flex items-center gap-1">
                        <span className="text-green-400">✓</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
                {idx < STEPS.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-3 z-10 text-slate-500 text-xl">→</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Sync Status */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-4 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`w-2 h-2 rounded-full ${pipelineStatus?.has_token ? "bg-green-400" : "bg-red-400"}`}></span>
              <span className="text-white font-medium text-sm">
                {pipelineStatus?.has_token ? "Token configured ✓" : "No token set"}
              </span>
            </div>
            <p className="text-slate-400 text-xs">
              Last sync: {pipelineStatus?.last_sync ? new Date(pipelineStatus.last_sync).toLocaleString() : "Never"}<br/>
              {pipelineStatus?.last_status && <span className="text-slate-500">{pipelineStatus.last_status}</span>}
            </p>
          </div>
          <button onClick={manualSync}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            🔄 Sync Now
          </button>
        </div>

        {/* Bearer Token Config */}
        <div className="bg-slate-800 border border-blue-500 rounded-xl p-6 mb-8">
          <h2 className="text-lg font-semibold text-white mb-1">🔑 Update Bearer Token</h2>
          <p className="text-slate-400 text-sm mb-4">
            Paste a new token → system immediately fetches all APIs and updates the dashboard automatically every 20 minutes
          </p>
          <form onSubmit={saveToken} className="flex gap-3">
            <input
              type="text"
              value={token}
              onChange={e => setToken(e.target.value)}
              placeholder="Paste new Bearer token here..."
              className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={saving || !token}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
            >
              {saving ? "Saving..." : saved ? "✓ Syncing!" : "Save & Sync"}
            </button>
          </form>
        </div>

        {/* Quick Links */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-slate-300 mb-4">Quick Links</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {LINKS.map(link => (
              <a
                key={link.label}
                href={link.url}
                target="_blank"
                rel="noreferrer"
                className={`${link.color} text-white rounded-xl p-4 flex items-center gap-3 transition-colors`}
              >
                <span className="text-2xl">{link.icon}</span>
                <span className="font-medium text-sm">{link.label}</span>
              </a>
            ))}
          </div>
        </div>

        {/* API Endpoints */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">📡 Configured API Endpoints</h2>
          <div className="space-y-3">
            {[
              { method: "POST", url: "https://api.rumanagers.online/prod-api/business/water/export", label: "Deposit Export", color: "bg-green-700" },
              { method: "POST", url: "https://api.rumanagers.online/prod-api/business/withdraw/export", label: "Withdrawal Export", color: "bg-red-700" },
              { method: "POST", url: "https://api.rumanagers.online/prod-api/business/detail/export", label: "Wallet Details Export", color: "bg-blue-700" },
            ].map(ep => (
              <div key={ep.url} className="flex items-center gap-3 bg-slate-900 rounded-lg px-4 py-3">
                <span className={`${ep.color} text-white text-xs font-bold px-2 py-1 rounded`}>{ep.method}</span>
                <div className="flex-1">
                  <div className="text-white text-xs font-medium">{ep.label}</div>
                  <div className="text-slate-500 text-xs font-mono truncate">{ep.url}</div>
                </div>
                <span className="text-xs text-slate-500">packageId=10</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
