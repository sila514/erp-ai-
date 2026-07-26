import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { fetchProducts, fetchStockRisk } from "@/lib/api/endpoints";
import StatusBadge, { type StatusTone } from "@/components/ui/StatusBadge";
import { formatCurrency } from "@/lib/format";

function stockTone(stock: number, reorder: number): { tone: StatusTone; label: string } {
  if (stock <= reorder * 0.5) return { tone: "critical", label: "Kritik stok" };
  if (stock <= reorder) return { tone: "warning", label: "Düşük stok" };
  return { tone: "good", label: "Normal" };
}

const SERVICE_LEVELS = [0.9, 0.95, 0.99];

export default function InventoryPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [serviceLevel, setServiceLevel] = useState(0.95);
  const { data: products, isLoading } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const stockRisk = useQuery({
    queryKey: ["stock-risk", selectedId, serviceLevel],
    queryFn: () => fetchStockRisk(selectedId!, serviceLevel),
    enabled: !!selectedId,
  });

  if (isLoading) return <p className="text-sm text-slate-500">Yükleniyor...</p>;

  const selectedProduct = products?.find((p) => p.id === selectedId);

  return (
    <div className="space-y-4">
      <div className="card-dark overflow-visible">
        <table className="w-full text-left text-[12px]">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
              <th className="pb-2 pl-1">SKU</th>
              <th className="pb-2">Ürün</th>
              <th className="pb-2">Kategori</th>
              <th className="pb-2">Stok</th>
              <th className="pb-2">Eşik</th>
              <th className="pb-2">Birim Fiyat</th>
              <th className="pb-2">Durum</th>
              <th className="pb-2 pr-1">ML Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sky-400/[0.07]">
            {products?.map((p) => {
              const { tone, label } = stockTone(p.stock_quantity, p.reorder_level);
              return (
                <tr key={p.id} className="hover:bg-sky-400/[0.04]">
                  <td className="py-2 pl-1 font-mono text-[10px] text-sky-400/50">{p.sku}</td>
                  <td className="py-2 text-sky-100/80">{p.name}</td>
                  <td className="py-2 text-slate-500">{p.category ?? "-"}</td>
                  <td className="py-2 text-sky-100/80">{p.stock_quantity}</td>
                  <td className="py-2 text-slate-500">{p.reorder_level}</td>
                  <td className="py-2 text-slate-500">{formatCurrency(p.unit_price)}</td>
                  <td className="py-2">
                    <StatusBadge tone={tone} label={label} />
                  </td>
                  <td className="py-2 pr-1">
                    <button
                      onClick={() => setSelectedId(p.id)}
                      className="flex items-center gap-1 rounded-md border border-sky-400/20 bg-sky-400/5 px-2 py-1 text-[10px] text-sky-300 transition-colors hover:border-sky-400/50"
                    >
                      <Search size={10} />
                      Sorgula
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {selectedId && (
        <div className="card-dark">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-[13px] font-semibold text-sky-100/90">
              Stok Tükenme Riski — {selectedProduct?.name}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
              Servis seviyesi
              <select
                value={serviceLevel}
                onChange={(e) => setServiceLevel(Number(e.target.value))}
                className="rounded-md border border-sky-400/20 bg-navy-950/60 px-2 py-1 text-[11px] text-sky-200 focus:outline-none"
              >
                {SERVICE_LEVELS.map((lvl) => (
                  <option key={lvl} value={lvl}>
                    %{(lvl * 100).toFixed(0)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {stockRisk.isLoading && <p className="text-xs text-slate-500">ML servisinden alınıyor...</p>}
          {stockRisk.error && (
            <p className="text-xs text-rose-400">Risk hesaplanamadı. ML servisi çalışıyor mu?</p>
          )}
          {stockRisk.data && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div>
                <div className="text-[10px] text-sky-400/40">Mevcut Stok</div>
                <div className="text-lg font-bold text-sky-300">{stockRisk.data.current_stock}</div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Günlük Tahmini Talep (± σ)</div>
                <div className="text-lg font-bold text-sky-300">
                  {stockRisk.data.predicted_daily_demand.toFixed(1)}
                  <span className="ml-1 text-[11px] font-normal text-slate-500">
                    ± {stockRisk.data.daily_demand_sigma.toFixed(1)}
                  </span>
                </div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Tükenmeye Kalan Gün</div>
                <div className="text-lg font-bold text-sky-300">
                  {stockRisk.data.days_until_stockout?.toFixed(0) ?? "-"}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Risk Seviyesi</div>
                <StatusBadge
                  tone={
                    stockRisk.data.risk_level === "high"
                      ? "critical"
                      : stockRisk.data.risk_level === "medium"
                        ? "warning"
                        : "good"
                  }
                  label={stockRisk.data.risk_level}
                />
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Güvenlik Stoğu</div>
                <div className="text-lg font-bold text-sky-300">{stockRisk.data.safety_stock.toFixed(0)}</div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Yeniden Sipariş Noktası</div>
                <div className="text-lg font-bold text-sky-300">{stockRisk.data.reorder_point.toFixed(0)}</div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Önerilen Sipariş Miktarı</div>
                <div className="text-lg font-bold text-sky-300">
                  {stockRisk.data.recommended_reorder_quantity}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-sky-400/40">Belirsizlik Kaynağı</div>
                <div className="text-[11px] font-medium text-slate-400">
                  {stockRisk.data.uncertainty_source === "quantile_forecast"
                    ? "Quantile tahmin (p10/p90)"
                    : "Fallback (%30 CV varsayımı)"}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
