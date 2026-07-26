import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { fetchChurnRisk, fetchCustomerSegments, fetchCustomers } from "@/lib/api/endpoints";
import ChartCard from "@/components/ui/ChartCard";
import ChartTooltip from "@/components/charts/ChartTooltip";
import StatusBadge from "@/components/ui/StatusBadge";
import { SERIES_ORDER } from "@/lib/chartColors";
import { formatCurrency } from "@/lib/format";

export default function CustomersPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: customers, isLoading } = useQuery({ queryKey: ["customers"], queryFn: fetchCustomers });
  const segments = useQuery({ queryKey: ["customer-segments"], queryFn: fetchCustomerSegments });
  const churn = useQuery({
    queryKey: ["churn-risk", selectedId],
    queryFn: () => fetchChurnRisk(selectedId!),
    enabled: !!selectedId,
  });

  if (isLoading) return <p className="text-sm text-slate-500">Yükleniyor...</p>;

  const selectedCustomer = customers?.find((c) => c.id === selectedId);

  const segmentCounts = Object.entries(
    (segments.data?.customers ?? []).reduce<Record<string, number>>((acc, c) => {
      acc[c.segment] = (acc[c.segment] ?? 0) + 1;
      return acc;
    }, {})
  ).map(([name, count]) => ({ name, count }));

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
      <div className="space-y-4">
        <div className="card-dark">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
                <th className="pb-2 pl-1">Ad</th>
                <th className="pb-2">E-posta</th>
                <th className="pb-2">Segment</th>
                <th className="pb-2">Yaşam Boyu Değer</th>
                <th className="pb-2 pr-1">Churn</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-sky-400/[0.07]">
              {customers?.map((c) => (
                <tr key={c.id} className="hover:bg-sky-400/[0.04]">
                  <td className="py-2 pl-1 text-sky-100/80">{c.name}</td>
                  <td className="py-2 text-slate-500">{c.email ?? "-"}</td>
                  <td className="py-2">
                    {c.segment ? <span className="badge badge-neutral">{c.segment}</span> : "-"}
                  </td>
                  <td className="py-2 text-slate-400">
                    {c.lifetime_value ? formatCurrency(c.lifetime_value) : "-"}
                  </td>
                  <td className="py-2 pr-1">
                    <button
                      onClick={() => setSelectedId(c.id)}
                      className="flex items-center gap-1 rounded-md border border-sky-400/20 bg-sky-400/5 px-2 py-1 text-[10px] text-sky-300 transition-colors hover:border-sky-400/50"
                    >
                      <Search size={10} />
                      Risk sorgula
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selectedId && (
          <div className="card-dark">
            <div className="mb-3 text-[13px] font-semibold text-sky-100/90">
              Churn Riski — {selectedCustomer?.name}
            </div>
            {churn.isLoading && <p className="text-xs text-slate-500">ML servisinden alınıyor...</p>}
            {churn.error && <p className="text-xs text-rose-400">Risk hesaplanamadı. ML servisi çalışıyor mu?</p>}
            {churn.data && (
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <div className="text-lg font-bold text-sky-300">
                    %{(churn.data.churn_probability * 100).toFixed(0)}
                  </div>
                  <StatusBadge
                    tone={
                      churn.data.risk_level === "high"
                        ? "critical"
                        : churn.data.risk_level === "medium"
                          ? "warning"
                          : "good"
                    }
                    label={churn.data.risk_level}
                  />
                </div>
                {churn.data.top_factors?.length > 0 && (
                  <ul className="list-inside list-disc text-[11px] text-slate-400">
                    {churn.data.top_factors.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <ChartCard title="Müşteri Segmentleri" subtitle="K-Means segmentasyon sonucu" height={260}>
        {segments.isLoading && <p className="text-xs text-slate-500">Yükleniyor...</p>}
        {segments.error && <p className="text-xs text-rose-400">Segment verisi alınamadı. ML servisi çalışıyor mu?</p>}
        {segments.data && (
          <div className="flex h-full items-center gap-4">
            <ResponsiveContainer width="55%" height="100%">
              <PieChart>
                <Pie
                  data={segmentCounts}
                  dataKey="count"
                  nameKey="name"
                  innerRadius="55%"
                  outerRadius="85%"
                  paddingAngle={2}
                >
                  {segmentCounts.map((_, i) => (
                    <Cell key={i} fill={SERIES_ORDER[i % SERIES_ORDER.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-1.5">
              {segmentCounts.map((s, i) => (
                <div key={s.name} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="h-2 w-2 flex-shrink-0 rounded-full"
                    style={{
                      background: SERIES_ORDER[i % SERIES_ORDER.length],
                      boxShadow: `0 0 6px ${SERIES_ORDER[i % SERIES_ORDER.length]}`,
                    }}
                  />
                  <span className="flex-1 text-sky-300/70">{s.name}</span>
                  <span className="font-medium text-sky-100/90">{s.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </ChartCard>
    </div>
  );
}
