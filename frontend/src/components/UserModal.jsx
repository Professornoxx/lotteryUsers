import { useState, useEffect } from "react";
import { X } from "lucide-react";

const SECTIONS = [
  {
    title: "Basic Profile",
    fields: [
      { key: "username",     label: "Username",       type: "text" },
      { key: "phone",        label: "Phone",          type: "text" },
      { key: "email",        label: "Email",          type: "email" },
      { key: "gender",       label: "Gender",         type: "select", options: [{ v: 0, l: "Male" }, { v: 1, l: "Female" }] },
      { key: "birth_date",   label: "Birth Date",     type: "datetime-local" },
      { key: "city",         label: "City",           type: "text" },
      { key: "register_ip",  label: "Register IP",    type: "text" },
      { key: "user_status",  label: "User Status",    type: "select", options: [{ v: 0, l: "Active" }, { v: 1, l: "Banned" }] },
      { key: "is_test",      label: "Account Type",   type: "select", options: [{ v: 0, l: "Real" }, { v: 1, l: "Test" }] },
      { key: "reg_source",   label: "Register Source",type: "select", options: [{ v: "Android", l: "Android" }, { v: "h5", l: "H5 / Web" }] },
      { key: "reg_channel",  label: "Register Channel", type: "select", options: [{ v: "Organic", l: "Organic" }, { v: "AppShare", l: "AppShare" }, { v: "Promotion", l: "Promotion" }] },
      { key: "app_version",  label: "App Version",    type: "text" },
      { key: "reg_version",  label: "Reg Version",    type: "text" },
      { key: "package_id",   label: "Package ID",     type: "number" },
      { key: "mark",         label: "Mark / Note",    type: "textarea" },
      { key: "tag",          label: "Tag",            type: "text" },
    ],
  },
  {
    title: "Financials",
    fields: [
      { key: "balance",           label: "Balance",            type: "number" },
      { key: "user_balance",      label: "User Balance",       type: "number" },
      { key: "total_deposits",    label: "Total Deposits",     type: "number" },
      { key: "total_withdrawals", label: "Total Withdrawals",  type: "number" },
      { key: "frozen_amount",     label: "Frozen Amount",      type: "number" },
      { key: "withdraw_limit",    label: "Withdraw Limit",     type: "number" },
      { key: "recharge_count",    label: "Recharge Count",     type: "number" },
    ],
  },
  {
    title: "Agent / Referral",
    fields: [
      { key: "agent_status",   label: "Agent Status", type: "select", options: [
          { v: "", l: "None" }, { v: 0, l: "Not Applied" }, { v: 1, l: "Pending" },
          { v: 2, l: "Rejected" }, { v: 3, l: "Approved" }] },
      { key: "agent_user_id",  label: "Agent User ID",   type: "number" },
      { key: "parent_user_id", label: "Parent User ID",  type: "number" },
      { key: "direct_parent",  label: "Direct Parent",   type: "number" },
      { key: "agent_level1",   label: "Agent Level 1",   type: "number" },
      { key: "agent_level2",   label: "Agent Level 2",   type: "number" },
      { key: "agent_level3",   label: "Agent Level 3",   type: "number" },
      { key: "agent_level4",   label: "Agent Level 4",   type: "number" },
      { key: "agent_level",    label: "Agent Level",     type: "number" },
      { key: "inviter_user_id",label: "Inviter User ID", type: "number" },
      { key: "member_level",   label: "Member Level",    type: "number" },
    ],
  },
  {
    title: "Device",
    fields: [
      { key: "register_device",    label: "Register Device",    type: "text" },
      { key: "login_device",       label: "Login Device",       type: "text" },
      { key: "last_login_device",  label: "Last Login Device",  type: "text" },
      { key: "device_id",          label: "Device ID",          type: "text" },
      { key: "push_token",         label: "Push Token",         type: "text" },
      { key: "last_active_time",   label: "Last Active",        type: "datetime-local" },
    ],
  },
  {
    title: "IM / Chat",
    fields: [
      { key: "im_user_id",    label: "IM User ID",    type: "text" },
      { key: "im_user_status",label: "IM Status",     type: "select", options: [{ v: "0", l: "Offline" }, { v: "1", l: "Online" }] },
      { key: "im_customer",   label: "IM Customer",   type: "text" },
      { key: "group_name",    label: "Group Name",    type: "text" },
      { key: "adjust_adid",   label: "Adjust Ad ID",  type: "text" },
    ],
  },
  {
    title: "Follow-up",
    fields: [
      { key: "flow_up_time",      label: "Follow-up Time",      type: "datetime-local" },
      { key: "next_flow_up_time", label: "Next Follow-up Time", type: "datetime-local" },
    ],
  },
];

const EMPTY = {};
SECTIONS.forEach(s => s.fields.forEach(f => { EMPTY[f.key] = ""; }));

export default function UserModal({ user, onClose, onSave }) {
  const isEdit = !!user;
  const [form, setForm] = useState(isEdit ? { ...EMPTY, ...user } : { ...EMPTY });
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function set(key, val) {
    setForm(f => ({ ...f, [key]: val }));
  }

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      await onSave(form);
      onClose();
    } catch (e) {
      setError(e?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  const section = SECTIONS[tab];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-white font-bold text-lg">{isEdit ? `Edit User #${user.user_id}` : "Add New User"}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X size={20} /></button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-3 border-b border-slate-700 overflow-x-auto">
          {SECTIONS.map((s, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-3 py-2 text-xs rounded-t-lg whitespace-nowrap transition-colors ${
                tab === i ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"}`}>
              {s.title}
            </button>
          ))}
        </div>

        {/* Fields */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {section.fields.map(({ key, label, type, options }) => (
              <div key={key} className={type === "textarea" ? "sm:col-span-2" : ""}>
                <label className="block text-xs text-slate-400 mb-1">{label}</label>
                {type === "select" ? (
                  <select value={form[key] ?? ""} onChange={e => set(key, e.target.value)}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500">
                    <option value="">— Select —</option>
                    {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
                  </select>
                ) : type === "textarea" ? (
                  <textarea value={form[key] ?? ""} onChange={e => set(key, e.target.value)} rows={3}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500 resize-none" />
                ) : (
                  <input type={type} value={form[key] ?? ""} onChange={e => set(key, e.target.value)}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-indigo-500" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-700 flex items-center justify-between">
          {error && <span className="text-red-400 text-sm">{error}</span>}
          <div className="flex gap-3 ml-auto">
            <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white">Cancel</button>
            <button onClick={handleSave} disabled={saving}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg disabled:opacity-50">
              {saving ? "Saving..." : isEdit ? "Save Changes" : "Add User"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
