import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

const ROLE_LABELS: Record<string, string> = {
  admin: "Yönetici",
  manager: "Müdür",
  sales: "Satış",
  inventory: "Stok",
  finance: "Finans",
};

export default function UserMenu() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  if (!user) return null;

  const initials = user.full_name
    ? user.full_name
        .split(" ")
        .map((p) => p[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : user.username.slice(0, 2).toUpperCase();

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="rounded-full bg-gradient-to-br from-sky-400 via-indigo-500 to-fuchsia-500 p-[1.5px] shadow-glow-sm"
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-navy-950 text-[10px] font-bold text-white">
          {initials}
        </div>
      </button>

      {open && (
        <div className="glass absolute right-0 top-11 z-30 w-56 p-2">
          <div className="glass-glow -right-10 -top-10 h-32 w-32 bg-indigo-500/15" />
          <div className="relative z-10 px-2 py-1.5">
            <div className="truncate text-[12.5px] font-semibold text-white">
              {user.full_name || user.username}
            </div>
            <div className="text-[11px] text-slate-500">
              {ROLE_LABELS[user.role] ?? user.role}
            </div>
          </div>
          <div className="relative z-10 my-1 h-px bg-white/[0.06]" />
          <button
            onClick={() => {
              setOpen(false);
              logout();
              navigate("/login", { replace: true });
            }}
            className="relative z-10 flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left text-[12px] text-rose-300 transition-colors hover:bg-white/[0.06]"
          >
            <LogOut size={14} />
            Çıkış yap
          </button>
        </div>
      )}
    </div>
  );
}
