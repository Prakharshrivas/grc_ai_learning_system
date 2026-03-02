interface HeaderProps {
  title: string;
  completionPct: number;
  roles: string[];
  selectedRole: string;
  onRoleChange: (role: string) => void;
}

export default function Header({
  title,
  completionPct,
  roles,
  selectedRole,
  onRoleChange,
}: HeaderProps) {
  return (
    <header className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
            G
          </div>
          <span className="text-slate-400 text-sm font-medium">GRC Learn</span>
        </div>
        <div className="h-5 w-px bg-slate-700" />
        <h1 className="text-white font-semibold text-sm truncate max-w-md">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-xs">Progress</span>
          <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(completionPct, 100)}%` }}
            />
          </div>
          <span className="text-slate-300 text-xs font-mono">
            {Math.round(completionPct)}%
          </span>
        </div>

        <select
          value={selectedRole}
          onChange={(e) => onRoleChange(e.target.value)}
          className="bg-slate-800 text-slate-300 text-xs border border-slate-600 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {roles.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}
