import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Plus, Pencil, Trash2, Download } from "lucide-react";
import api from "../utils/api";
import UserModal from "../components/UserModal";
import DeleteConfirm from "../components/DeleteConfirm";

export default function Users() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [city, setCity] = useState("");
  const [status, setStatus] = useState("");
  const [modal, setModal] = useState(null);      // null | "add" | user object
  const [delUser, setDelUser] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["users", page, search, city, status],
    queryFn: () =>
      api.get("/users/", { params: { page, page_size: 50, search: search || undefined, city: city || undefined, status: status !== "" ? status : undefined } })
         .then(r => r.data),
    keepPreviousData: true,
  });

  const users = data?.data ?? [];
  const total = data?.total ?? 0;

  function refresh() {
    qc.invalidateQueries({ queryKey: ["users"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
  }

  async function handleSave(form) {
    if (modal === "add") {
      await api.post("/users/", form);
    } else {
      await api.put(`/users/${modal.user_id}`, form);
    }
    refresh();
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await api.delete(`/users/${delUser.user_id}`);
      setDelUser(null);
      refresh();
    } finally {
      setDeleting(false);
    }
  }

  async function handleExport() {
    setExporting(true);
    try {
      const res = await api.get("/export/excel", { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lottery_users_${new Date().toISOString().slice(0,10)}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="space-y-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Users</h2>
        <div className="flex gap-2">
          <button onClick={handleExport} disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white text-sm rounded-lg disabled:opacity-50">
            <Download size={14} /> {exporting ? "Exporting..." : "Export Excel"}
          </button>
          <button onClick={() => setModal("add")}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg">
            <Plus size={14} /> Add User
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search username / phone..."
            className="pl-8 pr-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500 w-64" />
        </div>
        <input value={city} onChange={e => { setCity(e.target.value); setPage(1); }}
          placeholder="Filter by city"
          className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500" />
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}
          className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500">
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
              <th className="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={10} className="px-4 py-8 text-center text-slate-400">Loading...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={10} className="px-4 py-8 text-center text-slate-400">No users found</td></tr>
            ) : users.map(u => (
              <tr key={u.user_id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                <td className="px-4 py-3 text-slate-300">{u.user_id}</td>
                <td className="px-4 py-3 text-white font-medium">{u.username}</td>
                <td className="px-4 py-3 text-slate-300">{u.phone}</td>
                <td className="px-4 py-3 text-slate-300">{u.city}</td>
                <td className="px-4 py-3 text-emerald-400">₹{Number(u.balance ?? 0).toFixed(2)}</td>
                <td className="px-4 py-3 text-slate-300">₹{Number(u.total_deposits ?? 0).toFixed(2)}</td>
                <td className="px-4 py-3 text-slate-300">₹{Number(u.total_withdrawals ?? 0).toFixed(2)}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${u.user_status === 0 ? "bg-emerald-900 text-emerald-400" : "bg-red-900 text-red-400"}`}>
                    {u.user_status === 0 ? "Active" : "Banned"}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400 text-xs">{u.last_active_time ? new Date(u.last_active_time).toLocaleDateString() : "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-center gap-2">
                    <button onClick={() => setModal(u)} title="Edit"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-400 hover:bg-slate-700 transition-colors">
                      <Pencil size={14} />
                    </button>
                    <button onClick={() => setDelUser(u)} title="Delete"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-700 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-slate-400">
        <span>Total: {total.toLocaleString()} users</span>
        <div className="flex gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            className="px-3 py-1 bg-slate-800 rounded-lg disabled:opacity-40 hover:bg-slate-700">Prev</button>
          <span className="px-3 py-1">Page {page}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={users.length < 50}
            className="px-3 py-1 bg-slate-800 rounded-lg disabled:opacity-40 hover:bg-slate-700">Next</button>
        </div>
      </div>

      {/* Add / Edit Modal */}
      {modal && (
        <UserModal
          user={modal === "add" ? null : modal}
          onClose={() => setModal(null)}
          onSave={handleSave}
        />
      )}

      {/* Delete Confirm */}
      {delUser && (
        <DeleteConfirm
          user={delUser}
          onClose={() => setDelUser(null)}
          onConfirm={handleDelete}
          loading={deleting}
        />
      )}
    </div>
  );
}
