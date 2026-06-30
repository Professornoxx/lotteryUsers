import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Users, TrendingUp, Wallet, UserCheck } from "lucide-react";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">{label}</span>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={16} className="text-white" />
        </div>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const { data: summary } = useQuery({
    queryKey: ["summary"],
    queryFn: () => axios.get("/api/dashboard/summary").then((r) => r.data),
  });

  const { data: registrations = [] } = useQuery({
    queryKey: ["registrations"],
    queryFn: () => axios.get("/api/dashboard/registrations-over-time").then((r) => r.data),
  });

  const { data: cities = [] } = useQuery({
    queryKey: ["cities"],
    queryFn: () => axios.get("/api/dashboard/top-cities").then((r) => r.data),
  });

  const { data: memberLevels = [] } = useQuery({
    queryKey: ["member-levels"],
    queryFn: () => axios.get("/api/dashboard/member-levels").then((r) => r.data),
  });

  const { data: platforms = [] } = useQuery({
    queryKey: ["platforms"],
    queryFn: () => axios.get("/api/dashboard/platform-split").then((r) => r.data),
  });

  const { data: agentFunnel = [] } = useQuery({
    queryKey: ["agent-funnel"],
    queryFn: () => axios.get("/api/dashboard/agent-funnel").then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Dashboard Overview</h2>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Total Users" value={summary?.total_users?.toLocaleString() ?? "—"} color="bg-indigo-600" />
        <StatCard icon={UserCheck} label="Active Users" value={summary?.active_users?.toLocaleString() ?? "—"} color="bg-emerald-600" />
        <StatCard icon={Wallet} label="Total Deposits" value={summary?.total_deposits ? `₹${summary.total_deposits.toLocaleString()}` : "—"} color="bg-violet-600" />
        <StatCard icon={TrendingUp} label="Total Withdrawals" value={summary?.total_withdrawals ? `₹${summary.total_withdrawals.toLocaleString()}` : "—"} color="bg-cyan-600" />
      </div>

      {/* Registrations Over Time */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4">Registrations Over Time</h3>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={registrations}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
            <Area type="monotone" dataKey="count" stroke="#6366f1" fill="#6366f122" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Cities */}
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4">Top Cities</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={cities} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis dataKey="city" type="category" stroke="#64748b" tick={{ fontSize: 11 }} width={90} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Member Levels */}
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4">Member Level Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={memberLevels} dataKey="count" nameKey="level" cx="50%" cy="50%" outerRadius={80} label>
                {memberLevels.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Split */}
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4">Platform Split</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={platforms} dataKey="count" nameKey="platform" cx="50%" cy="50%" outerRadius={80} label>
                {platforms.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Funnel */}
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4">Agent Application Funnel</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={agentFunnel}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="status" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
