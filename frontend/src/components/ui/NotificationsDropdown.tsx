import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Bell, AlertTriangle, PackageX } from "lucide-react";
import { fetchDashboardOverview } from "@/lib/api/endpoints";

export default function NotificationsDropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { data } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: fetchDashboardOverview,
    refetchInterval: 30_000,
  });

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const items = [
    data && data.low_stock_products > 0
      ? {
          icon: PackageX,
          text: `${data.low_stock_products} ürün düşük stok seviyesinde`,
          to: "/inventory",
          color: "text-amber-300",
        }
      : null,
    data && data.flagged_anomalous_sales > 0
      ? {
          icon: AlertTriangle,
          text: `${data.flagged_anomalous_sales} satış anomali olarak işaretlendi`,
          to: "/sales",
          color: "text-rose-300",
        }
      : null,
  ].filter((x): x is NonNullable<typeof x> => x !== null);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.04] text-slate-400 transition-colors hover:border-sky-400/40 hover:text-sky-300"
      >
        <Bell size={14} />
        {items.length > 0 && (
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-fuchsia-400 shadow-glow-fuchsia" />
        )}
      </button>

      {open && (
        <div className="glass absolute right-0 top-11 z-30 w-72 p-2">
          <div className="glass-glow -right-10 -top-10 h-32 w-32 bg-fuchsia-500/15" />
          <div className="relative z-10 px-2 py-1.5 text-[11px] font-semibold text-slate-400">Bildirimler</div>
          <div className="relative z-10 space-y-1">
            {items.length === 0 && (
              <p className="px-2 py-3 text-[12px] text-slate-500">Yeni bildirim yok.</p>
            )}
            {items.map((item) => (
              <button
                key={item.text}
                onClick={() => {
                  setOpen(false);
                  navigate(item.to);
                }}
                className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left text-[12px] text-slate-200 transition-colors hover:bg-white/[0.06]"
              >
                <item.icon size={14} className={item.color} />
                {item.text}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
