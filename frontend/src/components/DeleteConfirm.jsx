export default function DeleteConfirm({ user, onClose, onConfirm, loading }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-slate-900 border border-red-800 rounded-2xl p-6 w-full max-w-sm">
        <h3 className="text-white font-bold text-lg mb-2">Delete User</h3>
        <p className="text-slate-400 text-sm mb-6">
          Are you sure you want to delete <span className="text-white font-medium">{user.username}</span> (ID: {user.user_id})?
          <br /><span className="text-red-400">This cannot be undone.</span>
        </p>
        <div className="flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white">Cancel</button>
          <button onClick={onConfirm} disabled={loading}
            className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-medium rounded-lg disabled:opacity-50">
            {loading ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}
