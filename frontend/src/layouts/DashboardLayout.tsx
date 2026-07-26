import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Wallet,
  MessageSquareText,
  Search,
  Bell,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Genel bakış", icon: LayoutDashboard },
  { to: "/inventory", label: "Stok", icon: Package },
  { to: "/sales", label: "Satış", icon: ShoppingCart },
  { to: "/customers", label: "Müşteriler", icon: Users },
  { to: "/finance", label: "Finans", icon: Wallet },
  { to: "/copilot", label: "AI Copilot", icon: MessageSquareText },
];

export default function DashboardLayout() {
  const location = useLocation();
  const activeItem = navItems.find((item) =>
    item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to)
  );

  return (
    <div className="relative flex h-screen overflow-hidden bg-navy-950 text-slate-200">
      <div className="pointer-events-none fixed -left-40 -top-64 h-[600px] w-[600px] rounded-full bg-sky-500/[0.05] blur-3xl" />
      <div className="pointer-events-none fixed -right-24 -bottom-52 h-[500px] w-[500px] rounded-full bg-fuchsia-500/[0.04] blur-3xl" />

      <aside className="relative z-10 flex w-56 flex-col border-r border-sky-400/10 bg-gradient-to-b from-navy-900 to-navy-950">
        <div className="flex items-center gap-2 border-b border-sky-400/10 px-5 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-blue-600 text-sm font-bold text-white shadow-glow-sm">
            E
          </div>
          <span className="text-sm font-semibold tracking-wide text-sky-100">ERP AI</span>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors ${
                  isActive
                    ? "bg-sky-400/10 text-sky-300 shadow-[inset_2px_0_0_0_#00b4ff]"
                    : "text-slate-400 hover:bg-sky-400/5 hover:text-sky-200"
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 flex-shrink-0 items-center gap-4 border-b border-sky-400/10 bg-navy-950/90 px-6 backdrop-blur">
          <h1 className="text-sm font-semibold text-sky-100">{activeItem?.label ?? "ERP AI"}</h1>
          <div className="flex-1" />
          <div className="flex items-center gap-2 rounded-lg border border-sky-400/15 bg-sky-400/5 px-2.5 py-1.5 text-xs text-slate-500">
            <Search size={13} />
            <span>Ara...</span>
          </div>
          <button className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-sky-400/15 bg-sky-400/5 text-slate-400 transition-colors hover:border-sky-400/40 hover:text-sky-300">
            <Bell size={14} />
          </button>
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-fuchsia-500 text-[10px] font-semibold text-white shadow-glow-sm">
            EA
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
