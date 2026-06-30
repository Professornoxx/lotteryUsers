import { useQuery } from "@tanstack/react-query";
import api from "../utils/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function useReport(key, url) {
  return useQuery({ queryKey: [key], queryFn: () => api.get(url).then((r) => r.data) });
}

function Table({ title, data = [], columns, keys }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-700">
        <h3 className="text-white font-semibold">{title}</h3>
        <span className="text-slate-500 text-xs">{data.length} records</span>
      </div>
      <div className="overflow-x-auto max-h-80">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-900">
            <tr className="border-b border-slate-700 text-slate-400 text-left">
              {columns.map((c) => <th key={c} className="px-4 py-3">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={columns.length} className="px-4 py-6 text-center text-slate-500">No data</td></tr>
            ) : data.map((row, i) => (
              <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                {keys.map((k) => (
                  <td key={k} className="px-4 py-3 text-slate-300">
                    {k.includes("deposit") || k.includes("withdraw") || k === "balance" || k.includes("amount")
                      ? row[k] != null ? `₹${Number(row[k]).toLocaleString()}` : "—"
                      : row[k] ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Reports() {
  const { data: topDep = [] }     = useReport("top-dep",     "/reports/top-depositors");
  const { data: topWith = [] }    = useReport("top-with",    "/reports/top-withdrawals");
  const { data: inactive = [] }   = useReport("inactive",    "/reports/inactive-users");
  const { data: agents = [] }     = useReport("agents",      "/reports/agent-performance");
  const { data: channels = [] }   = useReport("ch-perf",     "/reports/channel-performance");
  const { data: zeroDep = [] }    = useReport("zero-dep",    "/reports/zero-deposit-users");
  const { data: highBal = [] }    = useReport("high-bal",    "/reports/high-balance-users");
  const { data: cityFin = [] }    = useReport("city-fin",    "/reports/city-financials");
  const { data: newUsers = [] }   = useReport("new-users",   "/reports/new-users-summary");

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Reports</h2>

      {/* Channel Performance Chart */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4">Channel Performance — Total Deposits</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={channels}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="channel" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "none" }}
              formatter={(v) => [`₹${Number(v).toLocaleString()}`]} />
            <Bar dataKey="total_deposits" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* City Financials Chart */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4">City Financials — Top 20 Cities</h3>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={cityFin} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} />
            <YAxis dataKey="city" type="category" stroke="#64748b" tick={{ fontSize: 11 }} width={110} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "none" }}
              formatter={(v) => [`₹${Number(v).toLocaleString()}`]} />
            <Bar dataKey="total_deposits" fill="#10b981" name="Deposits" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Table title="Top Depositors" data={topDep}
          columns={["User ID", "Username", "Phone", "City", "Total Deposits", "Recharges", "Balance"]}
          keys={["user_id", "username", "phone", "city", "total_deposits", "recharge_count", "balance"]} />

        <Table title="Top Withdrawals" data={topWith}
          columns={["User ID", "Username", "Phone", "City", "Total Withdrawals", "Total Deposits"]}
          keys={["user_id", "username", "phone", "city", "total_withdrawals", "total_deposits"]} />

        <Table title="High Balance Users" data={highBal}
          columns={["User ID", "Username", "Phone", "City", "Balance", "Deposits", "Withdrawals"]}
          keys={["user_id", "username", "phone", "city", "balance", "total_deposits", "total_withdrawals"]} />

        <Table title="Zero Deposit Users" data={zeroDep}
          columns={["User ID", "Username", "Phone", "City", "Channel", "Registered"]}
          keys={["user_id", "username", "phone", "city", "reg_channel", "create_time"]} />

        <Table title="Inactive Users (7+ days)" data={inactive}
          columns={["User ID", "Username", "Phone", "City", "Last Active", "Balance"]}
          keys={["user_id", "username", "phone", "city", "last_active_time", "balance"]} />

        <Table title="Agent Performance" data={agents}
          columns={["Agent ID", "Username", "City", "Level", "Referrals", "Referred Deposits"]}
          keys={["agent_id", "username", "city", "agent_level", "referrals", "referred_deposits"]} />

        <Table title="Channel Performance" data={channels}
          columns={["Channel", "Users", "Total Deposits", "Avg Deposit", "Avg Balance", "Deposited"]}
          keys={["channel", "user_count", "total_deposits", "avg_deposit", "avg_balance", "deposited_users"]} />

        <Table title="New Users Daily Summary" data={newUsers}
          columns={["Date", "New Users", "Deposited", "Total Deposits"]}
          keys={["date", "new_users", "deposited", "total_deposits"]} />
      </div>
    </div>
  );
}
