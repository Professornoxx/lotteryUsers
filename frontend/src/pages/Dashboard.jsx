import { useQuery } from "@tanstack/react-query";
import api from "../utils/api";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Users, TrendingUp, Wallet, UserCheck, Shield, Snowflake, Activity, RefreshCw } from "lucide-react";
import { format } from "date-fns";

const COLORS = ["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#84cc16"];

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">{label}</span>
        <div className={`p-2 rounded-lg ${color}`}><Icon size={16} className="text-white" /></div>
      </div>
      <div className="text-2xl font-bold text-white">{value ?? "—"}</div>
    </div>
  );
}

function ChartCard({ title, children, span = 1 }) {
  return (
    <div className={`bg-slate-900 border border-slate-700 rounded-xl p-5 ${span === 2 ? "lg:col-span-2" : ""}`}>
      <h3 className="text-white font-semibold mb-4">{title}</h3>
      {children}
    </div>
  );
}

const fmt = (n) => (n != null ? `₹${Number(n).toLocaleString()}` : "—");
const fmtN = (n) => (n != null ? Number(n).toLocaleString() : "—");

export default function Dashboard() {
  const q = (key, url) =>
    useQuery({ queryKey: [key], queryFn: () => api.get(url).then((r) => r.data) });

  const { data: s } = q("summary", "/dashboard/summary");
  const { data: reg = [] } = q("registrations", "/dashboard/registrations-over-time");
  const { data: cities = [] } = q("cities", "/dashboard/top-cities");
  const { data: memberLevels = [] } = q("member-levels", "/dashboard/member-levels");
  const { data: platforms = [] } = q("platforms", "/dashboard/platform-split");
  const { data: channels = [] } = q("channels", "/dashboard/channel-split");
  const { data: agentFunnel = [] } = q("agent-funnel", "/dashboard/agent-funnel");
  const { data: balanceDist = [] } = q("balance-dist", "/dashboard/balance-distribution");
  const { data: depositDist = [] } = q("deposit-dist", "/dashboard/deposit-distribution");
  const { data: dau = [] } = q("dau", "/dashboard/daily-active-users");
  const { data: imStatus = [] } = q("im-status", "/dashboard/im-status");

  const fmtDate = (d) => { try { return format(new Date(d), "MMM d"); } catch { return d; } };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Dashboard Overview</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users}     label="Total Users"       value={fmtN(s?.total_users)}       color="bg-indigo-600" />
        <StatCard icon={UserCheck} label="Active Users"      value={fmtN(s?.active_users)}      color="bg-emerald-600" />
        <StatCard icon={Shield}    label="Approved Agents"   value={fmtN(s?.approved_agents)}   color="bg-violet-600" />
        <StatCard icon={Activity}  label="Total Recharges"   value={fmtN(s?.total_recharges)}   color="bg-cyan-600" />
        <StatCard icon={Wallet}    label="Total Deposits"    value={fmt(s?.total_deposits)}     color="bg-amber-600" />
        <StatCard icon={TrendingUp}label="Total Withdrawals" value={fmt(s?.total_withdrawals)}  color="bg-rose-600" />
        <StatCard icon={Snowflake} label="Frozen Amount"     value={fmt(s?.total_frozen)}       color="bg-sky-600" />
        <StatCard icon={RefreshCw} label="Avg Deposit/User"  value={fmt(s?.avg_deposit)}        color="bg-fuchsia-600" />
      </div>

      {/* Registrations Over Time */}
      <ChartCard title="Registrations Over Time" span={2}>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={reg.map(r => ({ ...r, date: fmtDate(r.date) }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
            <Area type="monotone" dataKey="count" stroke="#6366f1" fill="#6366f122" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Daily Active Users */}
        <ChartCard title="Daily Active Users (Last 30 Days)">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={dau.map(r => ({ ...r, date: fmtDate(r.date) }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Area type="monotone" dataKey="count" stroke="#10b981" fill="#10b98122" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Top Cities */}
        <ChartCard title="Top Cities by Users">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={cities} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis dataKey="city" type="category" stroke="#64748b" tick={{ fontSize: 11 }} width={100} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Platform Split */}
        <ChartCard title="Platform Split (Android / H5)">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={platforms} dataKey="count" nameKey="platform" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {platforms.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Registration Channel */}
        <ChartCard title="Registration Channels">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={channels} dataKey="count" nameKey="channel" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {channels.map((_, i) => <Cell key={i} fill={COLORS[(i + 2) % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Agent Funnel */}
        <ChartCard title="Agent Application Funnel">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={agentFunnel}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="status" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Member Levels */}
        <ChartCard title="Member Level Distribution">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={memberLevels}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="level" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Balance Distribution */}
        <ChartCard title="Balance Distribution">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={balanceDist}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="range" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Deposit Distribution */}
        <ChartCard title="Deposit Distribution">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={depositDist}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="range" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
              <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* IM Status */}
        <ChartCard title="IM / Chat Status">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={imStatus} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {imStatus.map((_, i) => <Cell key={i} fill={COLORS[(i + 4) % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

      </div>
    </div>
  );
}
