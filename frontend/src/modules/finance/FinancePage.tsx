import { useQuery } from "@tanstack/react-query";
import { TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchFinanceSummary, fetchFinanceTransactions } from "@/lib/api/endpoints";
import KpiCard from "@/components/ui/KpiCard";
import ChartCard from "@/components/ui/ChartCard";
import ChartTooltip from "@/components/charts/ChartTooltip";
import { CHART_GRID, CHART_TICK, SERIES } from "@/lib/chartColors";
import { formatCompact, formatCurrency, groupFinanceByMonth } from "@/lib/format";

export default function FinancePage() {
  const summary = useQuery({ queryKey: ["finance-summary"], queryFn: fetchFinanceSummary });
  const transactions = useQuery({ queryKey: ["finance-transactions"], queryFn: fetchFinanceTransactions });

  if (summary.isLoading) return <p className="text-sm text-slate-500">Yükleniyor...</p>;

  const monthly = groupFinanceByMonth(transactions.data ?? [], 12);
  const rows = [...(transactions.data ?? [])].sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <KpiCard
          label="Toplam Gelir"
          value={summary.data ? formatCurrency(summary.data.total_income) : "-"}
          icon={TrendingUp}
          accent="emerald"
          progress={80}
        />
        <KpiCard
          label="Toplam Gider"
          value={summary.data ? formatCurrency(summary.data.total_expense) : "-"}
          icon={TrendingDown}
          accent="amber"
          progress={55}
        />
        <KpiCard
          label="Net Kâr"
          value={summary.data ? formatCurrency(summary.data.net_profit) : "-"}
          icon={Wallet}
          progress={65}
        />
      </div>

      <ChartCard title="Gelir & Gider Trendi" subtitle="Son 12 ay" height={240}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={monthly} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={CHART_GRID} vertical={false} />
            <XAxis dataKey="label" stroke={CHART_TICK} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
            <YAxis
              stroke={CHART_TICK}
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              width={40}
              tickFormatter={formatCompact}
            />
            <Tooltip content={<ChartTooltip />} />
            <Area type="monotone" dataKey="income" name="Gelir" stroke={SERIES.blue} fill={SERIES.blue} fillOpacity={0.12} strokeWidth={2} />
            <Area type="monotone" dataKey="expense" name="Gider" stroke={SERIES.orange} fill={SERIES.orange} fillOpacity={0.1} strokeWidth={1.5} />
            <Area type="monotone" dataKey="net" name="Net" stroke={SERIES.aqua} fill={SERIES.aqua} fillOpacity={0.08} strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="card-dark">
        <div className="mb-3 text-[13px] font-semibold text-sky-100/90">İşlemler</div>
        <table className="w-full table-fixed text-left text-[12px]">
          <thead>
            <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
              <th className="pb-2 pl-1">Tarih</th>
              <th className="pb-2">Tür</th>
              <th className="pb-2">Kategori</th>
              <th className="pb-2 pr-1">Tutar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sky-400/[0.07]">
            {rows.map((t) => (
              <tr key={t.id} className="hover:bg-sky-400/[0.04]">
                <td className="py-2 pl-1 text-slate-400">{new Date(t.created_at).toLocaleDateString("tr-TR")}</td>
                <td className="py-2">
                  <span className={`badge ${t.type === "income" ? "badge-good" : "badge-serious"}`}>
                    {t.type === "income" ? "Gelir" : "Gider"}
                  </span>
                </td>
                <td className="py-2 text-sky-100/70">{t.category ?? "-"}</td>
                <td
                  className={`py-2 pr-1 font-medium ${t.type === "income" ? "text-emerald-400" : "text-rose-400"}`}
                >
                  {t.type === "income" ? "+" : "-"}
                  {formatCurrency(t.amount)}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4} className="py-6 text-center text-slate-500">
                  Kayıt bulunamadı.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
