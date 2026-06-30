import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../utils/api";
import { Search } from "lucide-react";

export default function Users() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [city, setCity] = useState("");
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["users", page, search, city, status],
    queryFn: () =>
      api
        .get("/users/", { params: { page, page_size: 50, search, city, status: status || undefined } })
        .then((r) => r.data),
    keepPreviousData: true,
  });

  const users = data?.data ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-white">Users</h2>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search username / phone..."
            className="pl-8 pr-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500 w-64"
          />
        </div>
        <input
          value={city}
          onChange={(e) => { setCity(e.target.value); setPage(1); }}
          placeholder="Filter by city"
          className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Status</option>
          <option value="0">Active</option>
          <option value="1">Banned</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-slate-400 text-left">
              <th className="px-4 py-3">User ID</th>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">Balance</th>
              <th className="px-4 py-3">Deposits</th>
              <th className="px-4 py-3">Withdrawals</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last Active</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-slate-400">Loading...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-slate-400">No users found</td></tr>
            ) : (
              users.map((u) => (
                <tr key={u.user_id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                  <td className="px-4 py-3 text-slate-300">{u.user_id}</td>
                  <td className="px-4 py-3 text-white font-medium">{u.username}</td>
                  <td className="px-4 py-3 text-slate-300">{u.phone}</td>
                  <td className="px-4 py-3 text-slate-300">{u.city}</td>
                  <td className="px-4 py-3 text-emerald-400">₹{u.balance?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-300">₹{u.total_deposits?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-300">₹{u.total_withdrawals?.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${u.status === 0 ? "bg-emerald-900 text-emerald-400" : "bg-red-900 text-red-400"}`}>
                      {u.status === 0 ? "Active" : "Banned"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{u.last_active}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-slate-400">
        <span>Total: {total.toLocaleString()} users</span>
        <div className="flex gap-2">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
            className="px-3 py-1 bg-slate-800 rounded-lg disabled:opacity-40 hover:bg-slate-700">Prev</button>
          <span className="px-3 py-1">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={users.length < 50}
            className="px-3 py-1 bg-slate-800 rounded-lg disabled:opacity-40 hover:bg-slate-700">Next</button>
        </div>
      </div>
    </div>
  );
}
