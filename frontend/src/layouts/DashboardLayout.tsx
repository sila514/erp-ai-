import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Wallet,
  MessageSquareText,
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
  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-60 border-r border-gray-200 bg-white flex flex-col">
        <div className="px-5 py-4 border-b border-gray-100">
          <span className="text-lg font-semibold text-brand-700">ERP AI</span>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-600 hover:bg-gray-100"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
