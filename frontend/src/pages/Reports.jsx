import { useQuery } from "@tanstack/react-query";
import axios from "axios";

export default function Reports() {
  const { data: topDepositors = [] } = useQuery({
    queryKey: ["top-depositors"],
    queryFn: () => axios.get("/api/reports/top-depositors").then((r) => r.data),
  });

  const { data: channelPerf = [] } = useQuery({
    queryKey: ["channel-performance"],
    queryFn: () => axios.get("/api/reports/channel-performance").then((r) => r.data),
  });

  const { data: agentPerf = [] } = useQuery({
    queryKey: ["agent-performance"],
    queryFn: () => axios.get("/api/reports/agent-performance").then((r) => r.data),
  });

  const { data: inactive = [] } = useQuery({
    queryKey: ["inactive-users"],
    queryFn: () => axios.get("/api/reports/inactive-users").then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-white">Reports</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Depositors */}
        <ReportTable title="Top Depositors" data={topDepositors}
          columns={["User ID", "Username", "Total Deposits", "Recharge Count"]}
          keys={["user_id", "username", "total_deposits", "recharge_count"]} />

        {/* Channel Performance */}
        <ReportTable title="Channel Performance" data={channelPerf}
          columns={["Channel", "Users", "Total Deposits", "Avg Balance"]}
          keys={["channel", "user_count", "total_deposits", "avg_balance"]} />

        {/* Agent Performance */}
        <ReportTable title="Agent Performance" data={agentPerf}
          columns={["Agent ID", "Username", "Referrals", "Agent Level"]}
          keys={["agent_id", "username", "referrals", "agent_level"]} />

        {/* Inactive Users */}
        <ReportTable title="Inactive Users (7+ days)" data={inactive}
          columns={["User ID", "Username", "Last Active", "Balance"]}
          keys={["user_id", "username", "last_active", "balance"]} />
      </div>
    </div>
  );
}

function ReportTable({ title, data, columns, keys }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-700">
        <h3 className="text-white font-semibold">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-slate-400 text-left">
              {columns.map((c) => <th key={c} className="px-4 py-3">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={columns.length} className="px-4 py-6 text-center text-slate-500">No data</td></tr>
            ) : (
              data.map((row, i) => (
                <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/50">
                  {keys.map((k) => <td key={k} className="px-4 py-3 text-slate-300">{row[k] ?? "—"}</td>)}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
