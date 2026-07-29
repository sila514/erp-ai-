import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Wallet,
  Sigma,
  MessageSquareText,
  Sparkles,
} from "lucide-react";
import AuroraBackground from "@/components/ui/AuroraBackground";
import GlobalSearch from "@/components/ui/GlobalSearch";
import NotificationsDropdown from "@/components/ui/NotificationsDropdown";
import UserMenu from "@/components/ui/UserMenu";

const navItems = [
  { to: "/", label: "Genel bakış", icon: LayoutDashboard },
  { to: "/inventory", label: "Stok", icon: Package },
  { to: "/sales", label: "Satış", icon: ShoppingCart },
  { to: "/customers", label: "Müşteriler", icon: Users },
  { to: "/finance", label: "Finans", icon: Wallet },
  { to: "/analytics", label: "Veri Analizi", icon: Sigma },
  { to: "/copilot", label: "AI Copilot", icon: MessageSquareText },
];

export default function DashboardLayout() {
  const location = useLocation();
  const activeItem = navItems.find((item) =>
    item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to)
  );

  return (
    <div className="relative flex h-screen overflow-hidden text-slate-200">
      <AuroraBackground />

      <aside className="relative z-10 m-3 mr-0 flex w-60 flex-col rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-2xl">
        <div className="flex items-center gap-2.5 border-b border-white/[0.06] px-5 py-5">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 via-indigo-500 to-fuchsia-500 text-sm font-extrabold text-white shadow-glow-md">
            E
          </div>
          <div>
            <div className="text-[13px] font-bold tracking-wide text-white">ERP AI</div>
            <div className="text-[10px] text-slate-500">Yönetim Paneli</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-sky-500/20 via-indigo-500/15 to-transparent text-white shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08)]"
                    : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-gradient-to-b from-sky-400 to-fuchsia-500 shadow-glow-sm" />
                  )}
                  <Icon
                    size={17}
                    className={isActive ? "text-sky-300" : "text-slate-500 group-hover:text-slate-300"}
                  />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="m-3 rounded-xl border border-white/[0.08] bg-gradient-to-br from-sky-500/[0.08] to-fuchsia-500/[0.06] p-3">
          <div className="flex items-center gap-2 text-[11px] font-medium text-sky-200/80">
            <Sparkles size={13} className="text-sky-300" />
            AI Copilot hazır
          </div>
          <p className="mt-1 text-[10.5px] leading-relaxed text-slate-500">
            Verilerinle ilgili soru sor, anında yanıt al.
          </p>
        </div>
      </aside>

      <div className="relative z-10 flex flex-1 flex-col p-3">
        <header className="relative z-20 mb-3 flex h-14 flex-shrink-0 items-center gap-4 rounded-2xl border border-white/[0.08] bg-white/[0.03] px-6 backdrop-blur-2xl">
          <h1 className="text-[15px] font-bold text-white">
            <span className="text-gradient">{activeItem?.label ?? "ERP AI"}</span>
          </h1>
          <div className="flex-1" />
          <GlobalSearch />
          <NotificationsDropdown />
          <UserMenu />
        </header>

        <main className="flex-1 overflow-y-auto pb-3 pr-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
