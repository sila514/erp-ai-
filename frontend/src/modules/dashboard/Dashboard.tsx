import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Boxes, Users, ShoppingCart, AlertTriangle, Wallet, TrendingUp, Sparkles } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  fetchDashboardOverview,
  fetchFinanceSummary,
  fetchFinanceTransactions,
  fetchProducts,
  fetchSales,
} from "@/lib/api/endpoints";
import KpiCard from "@/components/ui/KpiCard";
import ChartCard from "@/components/ui/ChartCard";
import ChartTooltip from "@/components/charts/ChartTooltip";
import { CHART_GRID, CHART_TICK, SERIES } from "@/lib/chartColors";
import { formatCompact, formatCurrency, groupByDay, groupFinanceByMonth } from "@/lib/format";

export default function Dashboard() {
  const overview = useQuery({ queryKey: ["dashboard-overview"], queryFn: fetchDashboardOverview });
  const products = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const sales = useQuery({ queryKey: ["sales"], queryFn: fetchSales });
  const financeSummary = useQuery({ queryKey: ["finance-summary"], queryFn: fetchFinanceSummary });
  const financeTx = useQuery({ queryKey: ["finance-transactions"], queryFn: fetchFinanceTransactions });

  if (overview.isLoading) return <p className="text-sm text-slate-500">Yükleniyor...</p>;
  if (overview.error)
    return <p className="text-sm text-rose-400">Veri alınamadı. Backend çalışıyor mu?</p>;

  const salesTrend = groupByDay(sales.data ?? [], 14);
  const financeMonthly = groupFinanceByMonth(financeTx.data ?? [], 6);

  const stockByCategory = Object.values(
    (products.data ?? []).reduce<Record<string, { category: string; stock: number; reorder: number }>>(
      (acc, p) => {
        const key = p.category ?? "Diğer";
        acc[key] ??= { category: key, stock: 0, reorder: 0 };
        acc[key].stock += p.stock_quantity;
        acc[key].reorder += p.reorder_level;
        return acc;
      },
      {}
    )
  );

  const recentFlagged = (sales.data ?? [])
    .filter((s) => s.is_flagged_anomaly)
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, 5);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <KpiCard label="Toplam Ürün" value={overview.data!.total_products} icon={Boxes} progress={70} />
        <KpiCard
          label="Düşük Stoklu Ürün"
          value={overview.data!.low_stock_products}
          icon={AlertTriangle}
          accent="magenta"
          progress={45}
        />
        <KpiCard label="Toplam Müşteri" value={overview.data!.total_customers} icon={Users} progress={80} />
        <KpiCard
          label="Anomalili Satış"
          value={overview.data!.flagged_anomalous_sales}
          icon={AlertTriangle}
          accent="magenta"
          progress={30}
        />
        <KpiCard label="Toplam Satış" value={sales.data?.length ?? 0} icon={ShoppingCart} progress={65} />
        <KpiCard
          label="Toplam Gelir"
          value={financeSummary.data ? formatCompact(financeSummary.data.total_income) : "-"}
          icon={Wallet}
          progress={75}
        />
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <ChartCard
          title="Satış Trendi"
          subtitle="Son 14 gün — günlük toplam satış tutarı"
          badge={<span className="badge badge-neutral">Günlük</span>}
        >
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={salesTrend} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={CHART_GRID} vertical={false} />
              <XAxis dataKey="label" stroke={CHART_TICK} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis stroke={CHART_TICK} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={36} />
              <Tooltip content={<ChartTooltip />} />
              <Line
                type="monotone"
                dataKey="total"
                name="Satış Tutarı"
                stroke={SERIES.blue}
                strokeWidth={2}
                dot={{ r: 3, fill: SERIES.blue }}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Kategoriye Göre Stok Durumu"
          subtitle="Mevcut stok vs. yeniden sipariş eşiği"
          badge={<span className="badge badge-neutral">Stok</span>}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stockByCategory} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke={CHART_GRID} vertical={false} />
              <XAxis dataKey="category" stroke={CHART_TICK} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis stroke={CHART_TICK} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={30} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="stock" name="Mevcut Stok" fill={SERIES.blue} radius={[4, 4, 0, 0]} />
              <Bar dataKey="reorder" name="Sipariş Eşiği" fill={SERIES.orange} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1.2fr_1fr]">
        <ChartCard
          title="Gelir & Gider Trendi"
          subtitle="Son 6 ay — kümülatif alan grafiği"
          badge={<span className="badge badge-neutral">Aylık</span>}
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={financeMonthly} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
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
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="text-[13px] font-semibold text-sky-100/90">Son Anomalili Satışlar</div>
              <div className="mt-0.5 text-[11px] text-sky-400/40">ML anomali skoru dahil</div>
            </div>
            <span className="badge badge-critical">{recentFlagged.length} anomali</span>
          </div>
          {recentFlagged.length === 0 ? (
            <p className="text-xs text-slate-500">Şu an işaretli anomali yok.</p>
          ) : (
            <table className="w-full table-fixed text-left text-[11px]">
              <thead>
                <tr className="text-[10px] uppercase tracking-wide text-sky-400/35">
                  <th className="w-24 pb-2">ID</th>
                  <th className="pb-2">Tutar</th>
                  <th className="w-20 pb-2">Skor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-sky-400/[0.07]">
                {recentFlagged.map((s) => (
                  <tr key={s.id}>
                    <td className="py-1.5 font-mono text-[10px] text-sky-400/50">{s.id.slice(0, 8)}</td>
                    <td className="py-1.5 font-medium text-rose-400">{formatCurrency(s.total_amount)}</td>
                    <td className="py-1.5">{s.anomaly_score ? (s.anomaly_score * 100).toFixed(0) + "%" : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <Link
            to="/copilot"
            className="mt-3 flex items-center gap-2 rounded-lg border border-sky-400/25 bg-gradient-to-br from-sky-500/[0.12] to-fuchsia-500/[0.08] px-3 py-2 text-[11px] transition-colors hover:border-sky-400/50"
          >
            <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-sky-500 to-fuchsia-600 shadow-glow-sm">
              <Sparkles size={12} className="text-white" />
            </div>
            <span className="flex-1 text-sky-300/60">Bu anomalileri Copilot'a sor</span>
            <TrendingUp size={12} className="text-sky-400" />
          </Link>
        </div>
      </div>
    </div>
  );
}
