import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Search, Package, User } from "lucide-react";
import { fetchCustomers, fetchProducts } from "@/lib/api/endpoints";

export default function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const products = useQuery({ queryKey: ["products"], queryFn: fetchProducts, enabled: open });
  const customers = useQuery({ queryKey: ["customers"], queryFn: fetchCustomers, enabled: open });

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const q = query.trim().toLowerCase();

  const matchedProducts = useMemo(
    () =>
      q.length === 0
        ? []
        : (products.data ?? [])
            .filter((p) => p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q))
            .slice(0, 5),
    [products.data, q]
  );
  const matchedCustomers = useMemo(
    () =>
      q.length === 0
        ? []
        : (customers.data ?? []).filter((c) => c.name.toLowerCase().includes(q)).slice(0, 5),
    [customers.data, q]
  );

  const hasResults = matchedProducts.length > 0 || matchedCustomers.length > 0;

  return (
    <div className="relative" ref={ref}>
      <div
        className="flex cursor-text items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs text-slate-500 transition-colors hover:border-white/[0.15] focus-within:border-sky-400/40"
        onClick={() => setOpen(true)}
      >
        <Search size={13} />
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Ürün veya müşteri ara..."
          className="w-40 bg-transparent text-slate-200 placeholder:text-slate-500 focus:outline-none"
        />
      </div>

      {open && q.length > 0 && (
        <div className="glass absolute left-0 top-11 z-30 w-80 p-2">
          <div className="glass-glow -right-10 -top-10 h-32 w-32 bg-sky-500/15" />
          <div className="relative z-10 max-h-80 space-y-1 overflow-y-auto">
            {!hasResults && (
              <p className="px-2 py-3 text-[12px] text-slate-500">Sonuç bulunamadı.</p>
            )}
            {matchedProducts.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setOpen(false);
                  setQuery("");
                  navigate("/inventory");
                }}
                className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left text-[12px] text-slate-200 transition-colors hover:bg-white/[0.06]"
              >
                <Package size={14} className="text-sky-300" />
                <span className="flex-1">{p.name}</span>
                <span className="font-mono text-[10px] text-slate-500">{p.sku}</span>
              </button>
            ))}
            {matchedCustomers.map((c) => (
              <button
                key={c.id}
                onClick={() => {
                  setOpen(false);
                  setQuery("");
                  navigate("/customers");
                }}
                className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-left text-[12px] text-slate-200 transition-colors hover:bg-white/[0.06]"
              >
                <User size={14} className="text-violet-300" />
                <span className="flex-1">{c.name}</span>
                {c.email && <span className="text-[10px] text-slate-500">{c.email}</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
