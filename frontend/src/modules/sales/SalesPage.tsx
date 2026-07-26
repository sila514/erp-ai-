import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSales } from "@/lib/api/endpoints";
import StatusBadge from "@/components/ui/StatusBadge";
import { formatCurrency } from "@/lib/format";

const statusLabel: Record<string, string> = {
  pending: "Beklemede",
  completed: "Tamamlandı",
  cancelled: "İptal",
};

export default function SalesPage() {
  const [onlyFlagged, setOnlyFlagged] = useState(false);
  const { data: sales, isLoading } = useQuery({ queryKey: ["sales"], queryFn: fetchSales });

  const rows = useMemo(() => {
    const all = [...(sales ?? [])].sort((a, b) => b.created_at.localeCompare(a.created_at));
    return onlyFlagged ? all.filter((s) => s.is_flagged_anomaly) : all;
  }, [sales, onlyFlagged]);

  if (isLoading) return <p className="text-sm text-slate-500">Yükleniyor...</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setOnlyFlagged(false)}
          className={`badge ${!onlyFlagged ? "badge-neutral" : "border-sky-400/10 bg-transparent text-slate-500"}`}
        >
          Tümü ({sales?.length ?? 0})
        </button>
        <button
          onClick={() => setOnlyFlagged(true)}
          className={`badge ${onlyFlagged ? "badge-critical" : "border-sky-400/10 bg-transparent text-slate-500"}`}
        >
          Sadece anomali ({sales?.filter((s) => s.is_flagged_anomaly).length ?? 0})
        </button>
      </div>

      <div className="card-dark">
        <table className="w-full table-fixed text-left text-[12px]">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
              <th className="w-32 pb-2 pl-1">ID</th>
              <th className="pb-2">Tarih</th>
              <th className="pb-2">Kalem Sayısı</th>
              <th className="pb-2">Tutar</th>
              <th className="pb-2">Durum</th>
              <th className="pb-2 pr-1">Anomali</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sky-400/[0.07]">
            {rows.map((s) => (
              <tr key={s.id} className="hover:bg-sky-400/[0.04]">
                <td className="py-2 pl-1 font-mono text-[10px] text-sky-400/50">{s.id.slice(0, 8)}</td>
                <td className="py-2 text-slate-400">{new Date(s.created_at).toLocaleString("tr-TR")}</td>
                <td className="py-2 text-sky-100/70">{s.items.length}</td>
                <td className={`py-2 font-medium ${s.is_flagged_anomaly ? "text-rose-400" : "text-sky-100/80"}`}>
                  {formatCurrency(s.total_amount)}
                </td>
                <td className="py-2">
                  <span className="badge badge-neutral">{statusLabel[s.status] ?? s.status}</span>
                </td>
                <td className="py-2 pr-1">
                  {s.is_flagged_anomaly ? (
                    <StatusBadge
                      tone="critical"
                      label={s.anomaly_score ? `%${(s.anomaly_score * 100).toFixed(0)}` : "anomali"}
                    />
                  ) : (
                    <span className="text-slate-600">-</span>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="py-6 text-center text-slate-500">
                  Kayıt bulunamadı.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="text-[11px] text-slate-500">
        Not: yeni satışlar oluşturulduğunda anomali skoru artık senkron değil - Redis event ile
        ML servisine devredilir, sonuç birkaç saniye içinde bu tabloya yansır.
      </p>
    </div>
  );
}
